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

"""Tools for managing Google Ads ad groups via the MCP server."""

from ads_mcp.coordinator import mcp
import ads_mcp.utils as utils


@mcp.tool()
def create_ad_group(
    customer_id: str,
    campaign_id: str,
    name: str,
    status: str = "PAUSED",
    ad_group_type: str = "SEARCH_STANDARD",
    cpc_bid_micros: int = None,
) -> dict:
    """Creates a new ad group within a campaign.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        campaign_id: The ID of the parent campaign.
        name: The ad group name.
        status: Initial status: ENABLED or PAUSED. Defaults to PAUSED.
        ad_group_type: The type: SEARCH_STANDARD, DISPLAY_STANDARD, etc. Defaults to SEARCH_STANDARD.
        cpc_bid_micros: The max CPC bid in micros (1,000,000 micros = 1 currency unit). Optional.

    Returns:
        A dict with the created ad group's resource_name.
    """
    client = utils.get_googleads_client()
    operation = client.get_type("AdGroupOperation")
    ad_group = operation.create

    campaign_service = utils.get_googleads_service("CampaignService")
    ad_group.campaign = campaign_service.campaign_path(
        customer_id, campaign_id
    )
    ad_group.name = name
    ad_group.status = utils.resolve_enum("AdGroupStatusEnum", status)
    ad_group.type_ = utils.resolve_enum("AdGroupTypeEnum", ad_group_type)

    if cpc_bid_micros is not None:
        ad_group.cpc_bid_micros = cpc_bid_micros

    resource_names = utils.execute_mutate(
        service_name="AdGroupService",
        mutate_method_name="mutate_ad_groups",
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}


@mcp.tool()
def update_ad_group(
    customer_id: str,
    ad_group_id: str,
    name: str = None,
    status: str = None,
    cpc_bid_micros: int = None,
) -> dict:
    """Updates an existing ad group.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        ad_group_id: The ID of the ad group to update.
        name: New ad group name (optional).
        status: New status: ENABLED, PAUSED, or REMOVED (optional).
        cpc_bid_micros: New max CPC bid in micros (optional).

    Returns:
        A dict with the updated ad group's resource_name.
    """
    if all(v is None for v in [name, status, cpc_bid_micros]):
        raise ValueError("At least one field must be specified for update.")

    client = utils.get_googleads_client()
    operation = client.get_type("AdGroupOperation")
    ad_group = operation.update

    ad_group_service = utils.get_googleads_service("AdGroupService")
    ad_group.resource_name = ad_group_service.ad_group_path(
        customer_id, ad_group_id
    )

    if name is not None:
        ad_group.name = name
    if status is not None:
        ad_group.status = utils.resolve_enum("AdGroupStatusEnum", status)
    if cpc_bid_micros is not None:
        ad_group.cpc_bid_micros = cpc_bid_micros

    client.copy_from(
        operation.update_mask,
        utils.build_field_mask(ad_group),
    )

    resource_names = utils.execute_mutate(
        service_name="AdGroupService",
        mutate_method_name="mutate_ad_groups",
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}


@mcp.tool()
def remove_ad_group(
    customer_id: str,
    ad_group_id: str,
) -> dict:
    """Removes an ad group. This sets the ad group status to REMOVED.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        ad_group_id: The ID of the ad group to remove.

    Returns:
        A dict with the removed ad group's resource_name.
    """
    client = utils.get_googleads_client()
    operation = client.get_type("AdGroupOperation")
    ad_group_service = utils.get_googleads_service("AdGroupService")
    operation.remove = ad_group_service.ad_group_path(
        customer_id, ad_group_id
    )

    resource_names = utils.execute_mutate(
        service_name="AdGroupService",
        mutate_method_name="mutate_ad_groups",
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}
