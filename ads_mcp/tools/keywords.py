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

"""Tools for managing Google Ads keywords via the MCP server."""

from ads_mcp.coordinator import mcp
import ads_mcp.utils as utils


@mcp.tool()
def create_keyword(
    customer_id: str,
    ad_group_id: str,
    keyword_text: str,
    match_type: str = "BROAD",
    cpc_bid_micros: int = None,
    status: str = "ENABLED",
) -> dict:
    """Creates a new keyword criterion in an ad group.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        ad_group_id: The ID of the parent ad group.
        keyword_text: The keyword text.
        match_type: Keyword match type: EXACT, PHRASE, or BROAD. Defaults to BROAD.
        cpc_bid_micros: The max CPC bid in micros for this keyword (optional).
        status: Initial status: ENABLED or PAUSED. Defaults to ENABLED.

    Returns:
        A dict with the created keyword criterion's resource_name.
    """
    client = utils.get_googleads_client()
    operation = client.get_type("AdGroupCriterionOperation")
    criterion = operation.create

    ad_group_service = utils.get_googleads_service("AdGroupService")
    criterion.ad_group = ad_group_service.ad_group_path(
        customer_id, ad_group_id
    )
    criterion.status = utils.resolve_enum(
        "AdGroupCriterionStatusEnum", status
    )
    criterion.keyword.text = keyword_text
    criterion.keyword.match_type = utils.resolve_enum(
        "KeywordMatchTypeEnum", match_type
    )

    if cpc_bid_micros is not None:
        criterion.cpc_bid_micros = cpc_bid_micros

    resource_names = utils.execute_mutate(
        service_name="AdGroupCriterionService",
        mutate_method_name="mutate_ad_group_criteria",
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}


@mcp.tool()
def update_keyword(
    customer_id: str,
    ad_group_id: str,
    criterion_id: str,
    status: str = None,
    cpc_bid_micros: int = None,
) -> dict:
    """Updates an existing keyword criterion.

    Note: Keyword text and match type cannot be updated. To change them,
    remove the keyword and create a new one.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        ad_group_id: The ID of the parent ad group.
        criterion_id: The ID of the keyword criterion to update.
        status: New status: ENABLED or PAUSED (optional).
        cpc_bid_micros: New max CPC bid in micros (optional).

    Returns:
        A dict with the updated keyword criterion's resource_name.
    """
    if all(v is None for v in [status, cpc_bid_micros]):
        raise ValueError("At least one field must be specified for update.")

    client = utils.get_googleads_client()
    operation = client.get_type("AdGroupCriterionOperation")
    criterion = operation.update

    ad_group_criterion_service = utils.get_googleads_service(
        "AdGroupCriterionService"
    )
    criterion.resource_name = ad_group_criterion_service.ad_group_criterion_path(
        customer_id, ad_group_id, criterion_id
    )

    if status is not None:
        criterion.status = utils.resolve_enum(
            "AdGroupCriterionStatusEnum", status
        )
    if cpc_bid_micros is not None:
        criterion.cpc_bid_micros = cpc_bid_micros

    client.copy_from(
        operation.update_mask,
        utils.build_field_mask(criterion),
    )

    resource_names = utils.execute_mutate(
        service_name="AdGroupCriterionService",
        mutate_method_name="mutate_ad_group_criteria",
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}


@mcp.tool()
def remove_keyword(
    customer_id: str,
    ad_group_id: str,
    criterion_id: str,
) -> dict:
    """Removes a keyword criterion from an ad group.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        ad_group_id: The ID of the parent ad group.
        criterion_id: The ID of the keyword criterion to remove.

    Returns:
        A dict with the removed keyword criterion's resource_name.
    """
    client = utils.get_googleads_client()
    operation = client.get_type("AdGroupCriterionOperation")
    ad_group_criterion_service = utils.get_googleads_service(
        "AdGroupCriterionService"
    )
    operation.remove = ad_group_criterion_service.ad_group_criterion_path(
        customer_id, ad_group_id, criterion_id
    )

    resource_names = utils.execute_mutate(
        service_name="AdGroupCriterionService",
        mutate_method_name="mutate_ad_group_criteria",
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}
