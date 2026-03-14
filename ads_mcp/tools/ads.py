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

"""Tools for managing Google Ads responsive search ads via the MCP server."""

from typing import List

from ads_mcp.coordinator import mcp
import ads_mcp.utils as utils


@mcp.tool()
def create_responsive_search_ad(
    customer_id: str,
    ad_group_id: str,
    headlines: List[str],
    descriptions: List[str],
    final_urls: List[str],
    status: str = "PAUSED",
) -> dict:
    """Creates a new Responsive Search Ad in an ad group.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        ad_group_id: The ID of the parent ad group.
        headlines: List of headline texts (minimum 3, maximum 15, each max 30 chars).
        descriptions: List of description texts (minimum 2, maximum 4, each max 90 chars).
        final_urls: List of final landing page URLs (at least 1).
        status: Initial status: ENABLED or PAUSED. Defaults to PAUSED.

    Returns:
        A dict with the created ad's resource_name.
    """
    client = utils.get_googleads_client()
    operation = client.get_type("AdGroupAdOperation")
    ad_group_ad = operation.create

    ad_group_service = utils.get_googleads_service("AdGroupService")
    ad_group_ad.ad_group = ad_group_service.ad_group_path(
        customer_id, ad_group_id
    )
    ad_group_ad.status = utils.resolve_enum("AdGroupAdStatusEnum", status)

    ad = ad_group_ad.ad
    ad.final_urls.extend(final_urls)

    for headline_text in headlines:
        headline = client.get_type("AdTextAsset")
        headline.text = headline_text
        ad.responsive_search_ad.headlines.append(headline)

    for description_text in descriptions:
        description = client.get_type("AdTextAsset")
        description.text = description_text
        ad.responsive_search_ad.descriptions.append(description)

    resource_names = utils.execute_mutate(
        service_name="AdGroupAdService",
        mutate_method_name="mutate_ad_group_ads",
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}


@mcp.tool()
def update_ad_group_ad_status(
    customer_id: str,
    ad_group_id: str,
    ad_id: str,
    status: str,
) -> dict:
    """Updates the status of an ad in an ad group.

    Note: Ad content (headlines, descriptions, URLs) cannot be updated in-place.
    To change ad content, remove the ad and create a new one.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        ad_group_id: The ID of the parent ad group.
        ad_id: The ID of the ad to update.
        status: New status: ENABLED, PAUSED, or REMOVED.

    Returns:
        A dict with the updated ad's resource_name.
    """
    client = utils.get_googleads_client()
    operation = client.get_type("AdGroupAdOperation")
    ad_group_ad = operation.update

    ad_group_ad_service = utils.get_googleads_service("AdGroupAdService")
    ad_group_ad.resource_name = ad_group_ad_service.ad_group_ad_path(
        customer_id, ad_group_id, ad_id
    )
    ad_group_ad.status = utils.resolve_enum("AdGroupAdStatusEnum", status)

    client.copy_from(
        operation.update_mask,
        utils.build_field_mask(ad_group_ad),
    )

    resource_names = utils.execute_mutate(
        service_name="AdGroupAdService",
        mutate_method_name="mutate_ad_group_ads",
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}


@mcp.tool()
def remove_ad(
    customer_id: str,
    ad_group_id: str,
    ad_id: str,
) -> dict:
    """Removes an ad from an ad group.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        ad_group_id: The ID of the parent ad group.
        ad_id: The ID of the ad to remove.

    Returns:
        A dict with the removed ad's resource_name.
    """
    client = utils.get_googleads_client()
    operation = client.get_type("AdGroupAdOperation")
    ad_group_ad_service = utils.get_googleads_service("AdGroupAdService")
    operation.remove = ad_group_ad_service.ad_group_ad_path(
        customer_id, ad_group_id, ad_id
    )

    resource_names = utils.execute_mutate(
        service_name="AdGroupAdService",
        mutate_method_name="mutate_ad_group_ads",
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}
