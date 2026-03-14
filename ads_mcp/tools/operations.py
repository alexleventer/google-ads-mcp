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

"""Tools for non-standard Google Ads API operations.

Covers services that don't follow the standard mutate pattern:
- RecommendationService (apply/dismiss)
- ConversionUploadService (upload click/call conversions)
- ConversionAdjustmentUploadService (upload conversion adjustments)
- OfflineUserDataJobService (create/add/run offline user data jobs)
- BatchJobService (add operations to / run batch jobs)
- UserDataService (upload user data)
"""

from typing import Any, Dict, List

from google.protobuf import json_format

from ads_mcp.coordinator import mcp
import ads_mcp.utils as utils
from ads_mcp.tools.mutate import _convert_keys_to_camel


@mcp.tool()
def apply_recommendation(
    customer_id: str,
    recommendation_resource_name: str,
) -> dict:
    """Applies a Google Ads recommendation.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        recommendation_resource_name: The resource name of the recommendation
            (e.g. "customers/123/recommendations/456").

    Returns:
        A dict with the resource_name of the applied recommendation.
    """
    client = utils.get_googleads_client()
    service = utils.get_googleads_service("RecommendationService")

    operation = client.get_type("ApplyRecommendationOperation")
    operation.resource_name = recommendation_resource_name

    response = service.apply_recommendation(
        customer_id=customer_id, operations=[operation]
    )
    return {
        "resource_name": response.results[0].resource_name,
    }


@mcp.tool()
def dismiss_recommendation(
    customer_id: str,
    recommendation_resource_name: str,
) -> dict:
    """Dismisses a Google Ads recommendation.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        recommendation_resource_name: The resource name of the recommendation
            (e.g. "customers/123/recommendations/456").

    Returns:
        A dict with the resource_name of the dismissed recommendation.
    """
    client = utils.get_googleads_client()
    service = utils.get_googleads_service("RecommendationService")

    operation = client.get_type("DismissRecommendationOperation")
    operation.resource_name = recommendation_resource_name

    response = service.dismiss_recommendation(
        customer_id=customer_id, operations=[operation]
    )
    return {
        "resource_name": response.results[0].resource_name,
    }


@mcp.tool()
def upload_click_conversions(
    customer_id: str,
    conversions: List[Dict[str, Any]],
    partial_failure: bool = True,
) -> dict:
    """Uploads click conversions to Google Ads.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        conversions: List of conversion dicts. Each must include:
            - gclid: The Google click ID.
            - conversion_action: Resource name of the conversion action
                (e.g. "customers/123/conversionActions/456").
            - conversion_date_time: Conversion time as 'YYYY-MM-DD HH:MM:SS+HH:MM'.
            - conversion_value: The conversion value (float).
            - currency_code: 3-letter currency code (e.g. "USD"). Optional.
        partial_failure: If True, valid conversions are uploaded even if
            some fail. Defaults to True.

    Returns:
        A dict with the number of results and any partial failure errors.
    """
    client = utils.get_googleads_client()
    service = utils.get_googleads_service("ConversionUploadService")

    click_conversions = []
    for conv in conversions:
        cc = client.get_type("ClickConversion")
        camel_conv = _convert_keys_to_camel(conv)
        json_format.ParseDict(camel_conv, cc)
        click_conversions.append(cc)

    response = service.upload_click_conversions(
        customer_id=customer_id,
        conversions=click_conversions,
        partial_failure=partial_failure,
    )

    result = {"results_count": len(response.results)}
    if response.partial_failure_error:
        result["partial_failure_error"] = (
            response.partial_failure_error.message
        )
    return result


@mcp.tool()
def upload_call_conversions(
    customer_id: str,
    conversions: List[Dict[str, Any]],
    partial_failure: bool = True,
) -> dict:
    """Uploads call conversions to Google Ads.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        conversions: List of conversion dicts. Each must include:
            - caller_id: The caller's phone number in E.164 format.
            - conversion_action: Resource name of the conversion action.
            - conversion_date_time: Conversion time as 'YYYY-MM-DD HH:MM:SS+HH:MM'.
            - conversion_value: The conversion value (float). Optional.
            - currency_code: 3-letter currency code. Optional.
        partial_failure: If True, valid conversions are uploaded even if
            some fail. Defaults to True.

    Returns:
        A dict with the number of results and any partial failure errors.
    """
    client = utils.get_googleads_client()
    service = utils.get_googleads_service("ConversionUploadService")

    call_conversions = []
    for conv in conversions:
        cc = client.get_type("CallConversion")
        camel_conv = _convert_keys_to_camel(conv)
        json_format.ParseDict(camel_conv, cc)
        call_conversions.append(cc)

    response = service.upload_call_conversions(
        customer_id=customer_id,
        conversions=call_conversions,
        partial_failure=partial_failure,
    )

    result = {"results_count": len(response.results)}
    if response.partial_failure_error:
        result["partial_failure_error"] = (
            response.partial_failure_error.message
        )
    return result


@mcp.tool()
def upload_conversion_adjustments(
    customer_id: str,
    conversion_adjustments: List[Dict[str, Any]],
    partial_failure: bool = True,
) -> dict:
    """Uploads conversion adjustments (retractions or restatements).

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        conversion_adjustments: List of adjustment dicts. Each must include:
            - adjustment_type: "RETRACTION" or "RESTATEMENT".
            - conversion_action: Resource name of the conversion action.
            - adjustment_date_time: Adjustment time as 'YYYY-MM-DD HH:MM:SS+HH:MM'.
            - order_id or gclid_date_time_pair: Identifier for the conversion.
            - restatement_value: New value (for RESTATEMENT only).
        partial_failure: If True, valid adjustments are uploaded even if
            some fail. Defaults to True.

    Returns:
        A dict with the number of results and any partial failure errors.
    """
    client = utils.get_googleads_client()
    service = utils.get_googleads_service(
        "ConversionAdjustmentUploadService"
    )

    adjustments = []
    for adj in conversion_adjustments:
        ca = client.get_type("ConversionAdjustment")
        camel_adj = _convert_keys_to_camel(adj)
        json_format.ParseDict(camel_adj, ca)
        adjustments.append(ca)

    response = service.upload_conversion_adjustments(
        customer_id=customer_id,
        conversion_adjustments=adjustments,
        partial_failure=partial_failure,
    )

    result = {"results_count": len(response.results)}
    if response.partial_failure_error:
        result["partial_failure_error"] = (
            response.partial_failure_error.message
        )
    return result


@mcp.tool()
def create_offline_user_data_job(
    customer_id: str,
    job_type: str,
    external_id: int = None,
    customer_match_user_list_metadata: Dict[str, Any] = None,
    store_sales_metadata: Dict[str, Any] = None,
) -> dict:
    """Creates an offline user data job for Customer Match or Store Sales.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        job_type: Job type: "CUSTOMER_MATCH_USER_LIST",
            "CUSTOMER_MATCH_WITH_ATTRIBUTES", or "STORE_SALES_UPLOAD_FIRST_PARTY".
        external_id: Optional external ID for the job.
        customer_match_user_list_metadata: Metadata for Customer Match jobs.
            Must include "user_list" resource name.
        store_sales_metadata: Metadata for Store Sales jobs.

    Returns:
        A dict with the created job's resource_name.
    """
    client = utils.get_googleads_client()
    service = utils.get_googleads_service(
        "OfflineUserDataJobService"
    )

    job = client.get_type("OfflineUserDataJob")
    job.type_ = utils.resolve_enum(
        "OfflineUserDataJobTypeEnum", job_type
    )

    if external_id is not None:
        job.external_id = external_id

    if customer_match_user_list_metadata:
        camel = _convert_keys_to_camel(
            customer_match_user_list_metadata
        )
        json_format.ParseDict(
            camel, job.customer_match_user_list_metadata
        )

    if store_sales_metadata:
        camel = _convert_keys_to_camel(store_sales_metadata)
        json_format.ParseDict(camel, job.store_sales_metadata)

    response = service.create_offline_user_data_job(
        customer_id=customer_id, job=job
    )

    return {"resource_name": response.resource_name}


@mcp.tool()
def add_offline_user_data_job_operations(
    customer_id: str,
    resource_name: str,
    operations: List[Dict[str, Any]],
) -> dict:
    """Adds user data operations to an offline user data job.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        resource_name: The resource name of the offline user data job.
        operations: List of operation dicts. Each should have either
            "create" or "remove" with a UserData dict containing
            user_identifiers (hashed_email, hashed_phone_number, etc.).

    Returns:
        A dict confirming the operations were added.
    """
    client = utils.get_googleads_client()
    service = utils.get_googleads_service(
        "OfflineUserDataJobService"
    )

    job_operations = []
    for op_spec in operations:
        op = client.get_type("OfflineUserDataJobOperation")
        if "create" in op_spec:
            camel = _convert_keys_to_camel(op_spec["create"])
            json_format.ParseDict(camel, op.create)
        elif "remove" in op_spec:
            camel = _convert_keys_to_camel(op_spec["remove"])
            json_format.ParseDict(camel, op.remove)
        job_operations.append(op)

    response = service.add_offline_user_data_job_operations(
        resource_name=resource_name,
        operations=job_operations,
    )

    return {"received_operations_count": len(job_operations)}


@mcp.tool()
def run_offline_user_data_job(
    resource_name: str,
) -> dict:
    """Runs (executes) an offline user data job.

    This triggers async processing. Use the search tool to check the
    job status via the offline_user_data_job resource.

    Args:
        resource_name: The resource name of the offline user data job.

    Returns:
        A dict confirming the job was triggered.
    """
    service = utils.get_googleads_service(
        "OfflineUserDataJobService"
    )
    service.run_offline_user_data_job(resource_name=resource_name)
    return {"status": "job_started", "resource_name": resource_name}


@mcp.tool()
def add_batch_job_operations(
    customer_id: str,
    resource_name: str,
    operations: List[Dict[str, Any]],
) -> dict:
    """Adds mutate operations to a batch job for async processing.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        resource_name: The resource name of the batch job
            (created via google_ads_mutate with entity_type="BatchJob").
        operations: List of operation dicts, each with:
            - entity_type: The entity type (e.g. "Campaign").
            - action: "create", "update", or "remove".
            - attributes: Dict of field names to values.
            - resource_name: Resource name (for update/remove).

    Returns:
        A dict with the total operation count.
    """
    from ads_mcp.tools.mutate import (
        _ENTITY_MAP,
        _to_snake_case,
    )

    client = utils.get_googleads_client()
    service = utils.get_googleads_service("BatchJobService")

    mutate_operations = []
    for op_spec in operations:
        entity_type = op_spec["entity_type"]
        action = op_spec["action"]
        attributes = op_spec.get("attributes", {})
        res_name = op_spec.get("resource_name")

        if entity_type not in _ENTITY_MAP:
            raise ValueError(f"Unknown entity_type '{entity_type}'.")

        entity_operation = client.get_type(
            f"{entity_type}Operation"
        )

        if action == "create":
            resource = entity_operation.create
            if attributes:
                camel = _convert_keys_to_camel(attributes)
                json_format.ParseDict(camel, resource)
        elif action == "update":
            resource = entity_operation.update
            resource.resource_name = res_name
            if attributes:
                camel = _convert_keys_to_camel(attributes)
                json_format.ParseDict(camel, resource)
            client.copy_from(
                entity_operation.update_mask,
                utils.build_field_mask(resource),
            )
        elif action == "remove":
            entity_operation.remove = res_name

        mutate_op = client.get_type("MutateOperation")
        op_field = _to_snake_case(entity_type) + "_operation"
        client.copy_from(
            getattr(mutate_op, op_field), entity_operation
        )
        mutate_operations.append(mutate_op)

    response = service.add_batch_job_operations(
        resource_name=resource_name,
        mutate_operations=mutate_operations,
    )

    return {
        "total_operation_count": response.total_operation_count,
    }


@mcp.tool()
def run_batch_job(
    resource_name: str,
) -> dict:
    """Runs a batch job for async processing.

    The batch job must have operations added via add_batch_job_operations
    before running. Use the search tool to check job status and results.

    Args:
        resource_name: The resource name of the batch job.

    Returns:
        A dict confirming the batch job was started.
    """
    service = utils.get_googleads_service("BatchJobService")
    service.run_batch_job(resource_name=resource_name)
    return {"status": "job_started", "resource_name": resource_name}


@mcp.tool()
def upload_user_data(
    customer_id: str,
    operations: List[Dict[str, Any]],
    customer_match_user_list_metadata: Dict[str, Any] = None,
) -> dict:
    """Uploads user data for Customer Match.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        operations: List of operation dicts, each with either
            "create" or "remove" containing a UserData dict with
            user_identifiers.
        customer_match_user_list_metadata: Metadata including the
            user_list resource name.

    Returns:
        A dict with upload results.
    """
    client = utils.get_googleads_client()
    service = utils.get_googleads_service("UserDataService")

    user_data_operations = []
    for op_spec in operations:
        op = client.get_type("UserDataOperation")
        if "create" in op_spec:
            camel = _convert_keys_to_camel(op_spec["create"])
            json_format.ParseDict(camel, op.create)
        elif "remove" in op_spec:
            camel = _convert_keys_to_camel(op_spec["remove"])
            json_format.ParseDict(camel, op.remove)
        user_data_operations.append(op)

    kwargs = {
        "customer_id": customer_id,
        "operations": user_data_operations,
    }

    if customer_match_user_list_metadata:
        metadata = client.get_type(
            "CustomerMatchUserListMetadata"
        )
        camel = _convert_keys_to_camel(
            customer_match_user_list_metadata
        )
        json_format.ParseDict(camel, metadata)
        kwargs["customer_match_user_list_metadata"] = metadata

    response = service.upload_user_data(**kwargs)

    return {
        "received_operations_count": response.received_operations_count,
    }
