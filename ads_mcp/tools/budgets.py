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

"""Tools for managing Google Ads campaign budgets via the MCP server."""

from ads_mcp.coordinator import mcp
import ads_mcp.utils as utils


@mcp.tool()
def create_campaign_budget(
    customer_id: str,
    name: str,
    amount_micros: int,
    delivery_method: str = "STANDARD",
    explicitly_shared: bool = False,
) -> dict:
    """Creates a new campaign budget.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        name: The name of the budget.
        amount_micros: The daily budget amount in micros (1,000,000 micros = 1 currency unit).
        delivery_method: Budget delivery method: STANDARD or ACCELERATED. Defaults to STANDARD.
        explicitly_shared: If True, the budget can be shared across campaigns.

    Returns:
        A dict with the created budget's resource_name.
    """
    client = utils.get_googleads_client()
    operation = client.get_type("CampaignBudgetOperation")
    budget = operation.create

    budget.name = name
    budget.amount_micros = amount_micros
    budget.delivery_method = utils.resolve_enum(
        "BudgetDeliveryMethodEnum", delivery_method
    )
    budget.explicitly_shared = explicitly_shared

    resource_names = utils.execute_mutate(
        service_name="CampaignBudgetService",
        mutate_method_name="mutate_campaign_budgets",
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}


@mcp.tool()
def update_campaign_budget(
    customer_id: str,
    budget_id: str,
    name: str = None,
    amount_micros: int = None,
) -> dict:
    """Updates an existing campaign budget.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        budget_id: The ID of the budget to update.
        name: New name for the budget (optional).
        amount_micros: New daily budget amount in micros (optional).

    Returns:
        A dict with the updated budget's resource_name.
    """
    if name is None and amount_micros is None:
        raise ValueError("At least one field must be specified for update.")

    client = utils.get_googleads_client()
    operation = client.get_type("CampaignBudgetOperation")
    budget = operation.update

    budget_service = utils.get_googleads_service("CampaignBudgetService")
    budget.resource_name = budget_service.campaign_budget_path(
        customer_id, budget_id
    )

    if name is not None:
        budget.name = name
    if amount_micros is not None:
        budget.amount_micros = amount_micros

    client.copy_from(
        operation.update_mask,
        utils.build_field_mask(budget),
    )

    resource_names = utils.execute_mutate(
        service_name="CampaignBudgetService",
        mutate_method_name="mutate_campaign_budgets",
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}


@mcp.tool()
def remove_campaign_budget(
    customer_id: str,
    budget_id: str,
) -> dict:
    """Removes a campaign budget.

    Args:
        customer_id: The customer ID (digits only, no hyphens).
        budget_id: The ID of the budget to remove.

    Returns:
        A dict with the removed budget's resource_name.
    """
    client = utils.get_googleads_client()
    operation = client.get_type("CampaignBudgetOperation")
    budget_service = utils.get_googleads_service("CampaignBudgetService")
    operation.remove = budget_service.campaign_budget_path(
        customer_id, budget_id
    )

    resource_names = utils.execute_mutate(
        service_name="CampaignBudgetService",
        mutate_method_name="mutate_campaign_budgets",
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}
