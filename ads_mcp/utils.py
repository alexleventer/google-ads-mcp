#!/usr/bin/env python

# Copyright 2025 Google LLC.
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
import logging
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.v23.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)

from google.ads.googleads.util import get_nested_attr
from google.api_core import protobuf_helpers
import google.auth
from ads_mcp.mcp_header_interceptor import MCPHeaderInterceptor
import os
import importlib.resources

# filename for generated field information used by search
_GAQL_FILENAME = "gaql_resources.json"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Full access scope for the Google Ads API.
_ADS_SCOPE = "https://www.googleapis.com/auth/adwords"


def _create_credentials() -> google.auth.credentials.Credentials:
    """Returns Application Default Credentials with Google Ads scope."""
    credentials, _ = google.auth.default(scopes=[_ADS_SCOPE])
    return credentials


def _get_developer_token() -> str:
    """Returns the developer token from the environment variable GOOGLE_ADS_DEVELOPER_TOKEN."""
    dev_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")
    if dev_token is None:
        raise ValueError(
            "GOOGLE_ADS_DEVELOPER_TOKEN environment variable not set."
        )
    return dev_token


def _get_login_customer_id() -> str | None:
    """Returns login customer id, if set, from the environment variable GOOGLE_ADS_LOGIN_CUSTOMER_ID."""
    return os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")


def _get_googleads_client() -> GoogleAdsClient:
    # Use this line if you have a google-ads.yaml file
    # client = GoogleAdsClient.load_from_storage()
    args = {
        "credentials": _create_credentials(),
        "developer_token": _get_developer_token(),
    }

    # If the login-customer-id is not set, avoid setting None.
    login_customer_id = _get_login_customer_id()

    if login_customer_id:
        args["login_customer_id"] = login_customer_id

    client = GoogleAdsClient(**args)

    return client


_googleads_client = _get_googleads_client()


def get_googleads_service(serviceName: str) -> GoogleAdsServiceClient:
    return _googleads_client.get_service(
        serviceName, interceptors=[MCPHeaderInterceptor()]
    )


def get_googleads_type(typeName: str):
    return _googleads_client.get_type(typeName)


def get_googleads_client():
    return _googleads_client


def format_output_value(value: Any) -> Any:
    if isinstance(value, proto.Enum):
        return value.name
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


def build_field_mask(modified_resource):
    """Builds a FieldMask for a protobuf resource based on set fields."""
    return protobuf_helpers.field_mask(None, modified_resource)


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
