#!/usr/bin/env python

# Copyright 2026 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Common utilities used by the MCP server."""

from typing import Any
import proto
from google.protobuf.message import Message as PbMessage
from google.protobuf.json_format import MessageToDict
import logging
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.v25.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)

from google.ads.googleads.util import get_nested_attr
from google.api_core import protobuf_helpers
import google.auth
import proto
from ads_mcp.mcp_header_interceptor import MCPHeaderInterceptor
import os
import re
import importlib.resources
import contextlib
import subprocess
from unittest.mock import patch

# filename for generated field information used by search
_GAQL_FILENAME = "gaql_resources.txt"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# OAuth scope for the Google Ads API. Google Ads does not publish a separate
# read-only scope; access is restricted to read methods by the tools this
# server exposes (see ads_mcp/tools/).
_ADS_SCOPE = "https://www.googleapis.com/auth/adwords"


@contextlib.contextmanager
def prevent_stdio_inheritance():
    """Prevents child processes from inheriting the parent's stdio handles.

    Fixes a deadlock on Windows where `google.auth.default()` spawns `gcloud`
    via subprocess without redirecting stdin, causing it to inherit the
    ProactorEventLoop's overlapping I/O handles used by MCP's stdio transport.
    """
    original_popen = subprocess.Popen

    def safe_popen(*args, **kwargs):
        if kwargs.get("stdin") is None:
            kwargs["stdin"] = subprocess.DEVNULL
        return original_popen(*args, **kwargs)

    with patch("subprocess.Popen", new=safe_popen):
        yield


def _create_credentials() -> google.auth.credentials.Credentials:
    """Returns Application Default Credentials with the Google Ads scope, or the FastMCP token if found."""
    from fastmcp.server.dependencies import get_access_token
    from google.oauth2.credentials import Credentials

    token_obj = get_access_token()
    if token_obj and token_obj.token:
        # Create credentials using the access token provided by FastMCP
        return Credentials(token=token_obj.token)

    with prevent_stdio_inheritance():
        credentials, _ = google.auth.default(scopes=[_ADS_SCOPE])
    return credentials


def _get_developer_token() -> str | None:
    """Returns the developer token from the environment variable GOOGLE_ADS_DEVELOPER_TOKEN, if set."""
    return os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")


def clean_customer_id(customer_id: str | int) -> str:
    """Cleans a customer ID by stripping non-digit characters."""
    return re.sub(r"\D", "", str(customer_id))


def _get_login_customer_id() -> str | None:
    """Returns login customer id, if set, from the environment variable GOOGLE_ADS_LOGIN_CUSTOMER_ID."""
    login_customer_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    if login_customer_id:
        return clean_customer_id(login_customer_id)
    return None


def _get_googleads_client() -> GoogleAdsClient:
    args = {
        "credentials": _create_credentials(),
        "use_proto_plus": True,
    }

    # If the developer-token is not set, avoid setting None.
    dev_token = _get_developer_token()
    if dev_token:
        args["developer_token"] = dev_token

    # If the login-customer-id is not set, avoid setting None.
    login_customer_id = _get_login_customer_id()

    if login_customer_id:
        args["login_customer_id"] = login_customer_id

    client = GoogleAdsClient(**args)

    return client


def get_googleads_service(serviceName: str) -> GoogleAdsServiceClient:
    return _get_googleads_client().get_service(
        serviceName, interceptors=[MCPHeaderInterceptor()]
    )


def get_googleads_type(typeName: str):
    return _get_googleads_client().get_type(typeName)


def get_googleads_client():
    return _get_googleads_client()


def format_output_value(value: Any) -> Any:
    if isinstance(value, proto.Enum):
        return value.name
    elif isinstance(value, proto.Message):
        return proto.Message.to_dict(value)
    elif isinstance(value, PbMessage):
        return MessageToDict(value, preserving_proto_field_name=True)
    elif hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
        return [format_output_value(v) for v in value]
    else:
        return value


def format_output_row(row: proto.Message, attributes):
    return {
        attr: format_output_value(get_nested_attr(row, attr))
        for attr in attributes
    }


def get_gaql_resources_filepath():
    package_root = importlib.resources.files("ads_mcp")
    file_path = package_root.joinpath(_GAQL_FILENAME)
    return file_path


def resolve_enum(enum_class_name: str, value: str):
    """Resolves a string to a Google Ads enum value with validation.

    Args:
        enum_class_name: The enum class name (e.g., "CampaignStatusEnum").
        value: The string enum value (e.g., "PAUSED").

    Returns:
        The resolved enum value.

    Raises:
        ValueError: If the value is not a valid enum member.
    """
    client = get_googleads_client()
    enum_class = getattr(client.enums, enum_class_name)
    try:
        return getattr(enum_class, value)
    except AttributeError:
        valid = [
            name
            for name in dir(enum_class)
            if not name.startswith("_") and name.isupper()
        ]
        raise ValueError(
            f"Invalid {enum_class_name} value '{value}'. "
            f"Valid values: {', '.join(valid)}"
        )


def to_pb(message):
    """Returns the raw protobuf underlying a proto-plus message.

    The client is created with use_proto_plus=True, but protobuf utilities such
    as json_format and protobuf_helpers only accept raw protobuf messages. The
    returned message shares storage with the wrapper, so edits apply to both.
    """
    if isinstance(message, proto.Message):
        return type(message).pb(message)
    return message


def build_field_mask(modified_resource):
    """Builds a FieldMask for a protobuf resource based on set fields."""
    return protobuf_helpers.field_mask(None, to_pb(modified_resource))


def execute_mutate(
    service_name: str,
    mutate_method_name: str,
    customer_id: str,
    operations: list,
) -> list[str]:
    """Executes a Google Ads mutate call and returns resource names.

    Args:
        service_name: The Google Ads service name (e.g., "CampaignService").
        mutate_method_name: The method on the service (e.g., "mutate_campaigns").
        customer_id: The customer ID (digits only, no hyphens).
        operations: List of operation protobuf objects.

    Returns:
        A list of resource_name strings from the mutation results.
    """
    service = get_googleads_service(service_name)
    mutate_fn = getattr(service, mutate_method_name)
    response = mutate_fn(customer_id=customer_id, operations=operations)
    return [result.resource_name for result in response.results]
