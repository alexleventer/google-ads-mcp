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

"""Tools for managing Google Ads campaigns via the MCP server."""

from ads_mcp.coordinator import mcp
import ads_mcp.utils as utils


@mcp.tool()
def create_campaign(
    customer_id: str,
    name: str,
    budget_id: str,
    advertising_channel_type: str = "SEARCH",
    status: str = "PAUSED",
    start_date_time: str = None,
    end_date_time: str = None,
) -> dict:
    """Creates a new campaign.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        name: The campaign name.
        budget_id: The ID of the campaign budget to use.
        advertising_channel_type: Channel type: SEARCH, DISPLAY, SHOPPING, VIDEO, etc. Defaults to SEARCH.
        status: Initial status: ENABLED or PAUSED. Defaults to PAUSED for safety.
        start_date_time: Campaign start date/time as 'YYYY-MM-DD HH:MM:SS' (optional).
        end_date_time: Campaign end date/time as 'YYYY-MM-DD HH:MM:SS' (optional).

    Returns:
        A dict with the created campaign's resource_name.
    """
    client = utils.get_googleads_client()
    operation = client.get_type("CampaignOperation")
    campaign = operation.create

    campaign.name = name
    campaign.advertising_channel_type = utils.resolve_enum(
        "AdvertisingChannelTypeEnum", advertising_channel_type
    )
    campaign.status = utils.resolve_enum("CampaignStatusEnum", status)

    budget_service = utils.get_googleads_service("CampaignBudgetService")
    campaign.campaign_budget = budget_service.campaign_budget_path(
        customer_id, budget_id
    )

    if start_date_time is not None:
        campaign.start_date_time = start_date_time
    if end_date_time is not None:
        campaign.end_date_time = end_date_time

    resource_names = utils.execute_mutate(
        service_name="CampaignService",
        mutate_method_name="mutate_campaigns",
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}


@mcp.tool()
def update_campaign(
    customer_id: str,
    campaign_id: str,
    name: str = None,
    status: str = None,
    start_date_time: str = None,
    end_date_time: str = None,
) -> dict:
    """Updates an existing campaign.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        campaign_id: The ID of the campaign to update.
        name: New campaign name (optional).
        status: New status: ENABLED, PAUSED, or REMOVED (optional).
        start_date_time: New start date/time as 'YYYY-MM-DD HH:MM:SS' (optional).
        end_date_time: New end date/time as 'YYYY-MM-DD HH:MM:SS' (optional).

    Returns:
        A dict with the updated campaign's resource_name.
    """
    if all(
        v is None
        for v in [name, status, start_date_time, end_date_time]
    ):
        raise ValueError("At least one field must be specified for update.")

    client = utils.get_googleads_client()
    operation = client.get_type("CampaignOperation")
    campaign = operation.update

    campaign_service = utils.get_googleads_service("CampaignService")
    campaign.resource_name = campaign_service.campaign_path(
        customer_id, campaign_id
    )

    if name is not None:
        campaign.name = name
    if status is not None:
        campaign.status = utils.resolve_enum("CampaignStatusEnum", status)
    if start_date_time is not None:
        campaign.start_date_time = start_date_time
    if end_date_time is not None:
        campaign.end_date_time = end_date_time

    client.copy_from(
        operation.update_mask,
        utils.build_field_mask(campaign),
    )

    resource_names = utils.execute_mutate(
        service_name="CampaignService",
        mutate_method_name="mutate_campaigns",
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}


@mcp.tool()
def remove_campaign(
    customer_id: str,
    campaign_id: str,
) -> dict:
    """Removes a campaign. This sets the campaign status to REMOVED.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        campaign_id: The ID of the campaign to remove.

    Returns:
        A dict with the removed campaign's resource_name.
    """
    client = utils.get_googleads_client()
    operation = client.get_type("CampaignOperation")
    campaign_service = utils.get_googleads_service("CampaignService")
    operation.remove = campaign_service.campaign_path(
        customer_id, campaign_id
    )

    resource_names = utils.execute_mutate(
        service_name="CampaignService",
        mutate_method_name="mutate_campaigns",
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}
