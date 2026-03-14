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

"""Generic mutate tool supporting ALL Google Ads API mutation operations."""

from typing import Any, Dict, List

from google.protobuf import json_format

from ads_mcp.coordinator import mcp
import ads_mcp.utils as utils


# Complete mapping of entity types to (service_name, mutate_method_name).
# Covers all 79 mutable services in the Google Ads API v23.
_ENTITY_MAP = {
    "AccountBudgetProposal": (
        "AccountBudgetProposalService",
        "mutate_account_budget_proposal",
    ),
    "AccountLink": ("AccountLinkService", "mutate_account_link"),
    "Ad": ("AdService", "mutate_ads"),
    "AdGroupAd": ("AdGroupAdService", "mutate_ad_group_ads"),
    "AdGroupAdLabel": (
        "AdGroupAdLabelService",
        "mutate_ad_group_ad_labels",
    ),
    "AdGroupAsset": ("AdGroupAssetService", "mutate_ad_group_assets"),
    "AdGroupAssetSet": (
        "AdGroupAssetSetService",
        "mutate_ad_group_asset_sets",
    ),
    "AdGroupBidModifier": (
        "AdGroupBidModifierService",
        "mutate_ad_group_bid_modifiers",
    ),
    "AdGroupCriterion": (
        "AdGroupCriterionService",
        "mutate_ad_group_criteria",
    ),
    "AdGroupCriterionCustomizer": (
        "AdGroupCriterionCustomizerService",
        "mutate_ad_group_criterion_customizers",
    ),
    "AdGroupCriterionLabel": (
        "AdGroupCriterionLabelService",
        "mutate_ad_group_criterion_labels",
    ),
    "AdGroupCustomizer": (
        "AdGroupCustomizerService",
        "mutate_ad_group_customizers",
    ),
    "AdGroupLabel": ("AdGroupLabelService", "mutate_ad_group_labels"),
    "AdGroup": ("AdGroupService", "mutate_ad_groups"),
    "AdParameter": ("AdParameterService", "mutate_ad_parameters"),
    "AssetGroupAsset": (
        "AssetGroupAssetService",
        "mutate_asset_group_assets",
    ),
    "AssetGroupListingGroupFilter": (
        "AssetGroupListingGroupFilterService",
        "mutate_asset_group_listing_group_filters",
    ),
    "AssetGroup": ("AssetGroupService", "mutate_asset_groups"),
    "AssetGroupSignal": (
        "AssetGroupSignalService",
        "mutate_asset_group_signals",
    ),
    "Asset": ("AssetService", "mutate_assets"),
    "AssetSetAsset": ("AssetSetAssetService", "mutate_asset_set_assets"),
    "AssetSet": ("AssetSetService", "mutate_asset_sets"),
    "Audience": ("AudienceService", "mutate_audiences"),
    "BatchJob": ("BatchJobService", "mutate_batch_job"),
    "BiddingDataExclusion": (
        "BiddingDataExclusionService",
        "mutate_bidding_data_exclusions",
    ),
    "BiddingSeasonalityAdjustment": (
        "BiddingSeasonalityAdjustmentService",
        "mutate_bidding_seasonality_adjustments",
    ),
    "BiddingStrategy": (
        "BiddingStrategyService",
        "mutate_bidding_strategies",
    ),
    "BillingSetup": ("BillingSetupService", "mutate_billing_setup"),
    "CampaignAsset": (
        "CampaignAssetService",
        "mutate_campaign_assets",
    ),
    "CampaignAssetSet": (
        "CampaignAssetSetService",
        "mutate_campaign_asset_sets",
    ),
    "CampaignBidModifier": (
        "CampaignBidModifierService",
        "mutate_campaign_bid_modifiers",
    ),
    "CampaignBudget": (
        "CampaignBudgetService",
        "mutate_campaign_budgets",
    ),
    "CampaignConversionGoal": (
        "CampaignConversionGoalService",
        "mutate_campaign_conversion_goals",
    ),
    "CampaignCriterion": (
        "CampaignCriterionService",
        "mutate_campaign_criteria",
    ),
    "CampaignCustomizer": (
        "CampaignCustomizerService",
        "mutate_campaign_customizers",
    ),
    "CampaignDraft": (
        "CampaignDraftService",
        "mutate_campaign_drafts",
    ),
    "CampaignGoalConfig": (
        "CampaignGoalConfigService",
        "mutate_campaign_goal_configs",
    ),
    "CampaignGroup": ("CampaignGroupService", "mutate_campaign_groups"),
    "CampaignLabel": (
        "CampaignLabelService",
        "mutate_campaign_labels",
    ),
    "Campaign": ("CampaignService", "mutate_campaigns"),
    "CampaignSharedSet": (
        "CampaignSharedSetService",
        "mutate_campaign_shared_sets",
    ),
    "ConversionAction": (
        "ConversionActionService",
        "mutate_conversion_actions",
    ),
    "ConversionCustomVariable": (
        "ConversionCustomVariableService",
        "mutate_conversion_custom_variables",
    ),
    "ConversionGoalCampaignConfig": (
        "ConversionGoalCampaignConfigService",
        "mutate_conversion_goal_campaign_configs",
    ),
    "ConversionValueRule": (
        "ConversionValueRuleService",
        "mutate_conversion_value_rules",
    ),
    "ConversionValueRuleSet": (
        "ConversionValueRuleSetService",
        "mutate_conversion_value_rule_sets",
    ),
    "CustomAudience": (
        "CustomAudienceService",
        "mutate_custom_audiences",
    ),
    "CustomConversionGoal": (
        "CustomConversionGoalService",
        "mutate_custom_conversion_goals",
    ),
    "CustomInterest": (
        "CustomInterestService",
        "mutate_custom_interests",
    ),
    "CustomerAsset": (
        "CustomerAssetService",
        "mutate_customer_assets",
    ),
    "CustomerAssetSet": (
        "CustomerAssetSetService",
        "mutate_customer_asset_sets",
    ),
    "CustomerClientLink": (
        "CustomerClientLinkService",
        "mutate_customer_client_link",
    ),
    "CustomerConversionGoal": (
        "CustomerConversionGoalService",
        "mutate_customer_conversion_goals",
    ),
    "CustomerCustomizer": (
        "CustomerCustomizerService",
        "mutate_customer_customizers",
    ),
    "CustomerLabel": (
        "CustomerLabelService",
        "mutate_customer_labels",
    ),
    "CustomerManagerLink": (
        "CustomerManagerLinkService",
        "mutate_customer_manager_link",
    ),
    "CustomerNegativeCriterion": (
        "CustomerNegativeCriterionService",
        "mutate_customer_negative_criteria",
    ),
    "Customer": ("CustomerService", "mutate_customer"),
    "CustomerSkAdNetworkConversionValueSchema": (
        "CustomerSkAdNetworkConversionValueSchemaService",
        "mutate_customer_sk_ad_network_conversion_value_schema",
    ),
    "CustomerUserAccessInvitation": (
        "CustomerUserAccessInvitationService",
        "mutate_customer_user_access_invitation",
    ),
    "CustomerUserAccess": (
        "CustomerUserAccessService",
        "mutate_customer_user_access",
    ),
    "CustomizerAttribute": (
        "CustomizerAttributeService",
        "mutate_customizer_attributes",
    ),
    "ExperimentArm": (
        "ExperimentArmService",
        "mutate_experiment_arms",
    ),
    "Experiment": ("ExperimentService", "mutate_experiments"),
    "Goal": ("GoalService", "mutate_goals"),
    "KeywordPlanAdGroupKeyword": (
        "KeywordPlanAdGroupKeywordService",
        "mutate_keyword_plan_ad_group_keywords",
    ),
    "KeywordPlanAdGroup": (
        "KeywordPlanAdGroupService",
        "mutate_keyword_plan_ad_groups",
    ),
    "KeywordPlanCampaignKeyword": (
        "KeywordPlanCampaignKeywordService",
        "mutate_keyword_plan_campaign_keywords",
    ),
    "KeywordPlanCampaign": (
        "KeywordPlanCampaignService",
        "mutate_keyword_plan_campaigns",
    ),
    "KeywordPlan": ("KeywordPlanService", "mutate_keyword_plans"),
    "Label": ("LabelService", "mutate_labels"),
    "RecommendationSubscription": (
        "RecommendationSubscriptionService",
        "mutate_recommendation_subscription",
    ),
    "RemarketingAction": (
        "RemarketingActionService",
        "mutate_remarketing_actions",
    ),
    "SharedCriterion": (
        "SharedCriterionService",
        "mutate_shared_criteria",
    ),
    "SharedSet": ("SharedSetService", "mutate_shared_sets"),
    "SmartCampaignSetting": (
        "SmartCampaignSettingService",
        "mutate_smart_campaign_settings",
    ),
    "UserListCustomerType": (
        "UserListCustomerTypeService",
        "mutate_user_list_customer_types",
    ),
    "UserList": ("UserListService", "mutate_user_lists"),
}


def _to_camel_case(snake_str: str) -> str:
    """Converts snake_case to camelCase for protobuf field names."""
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def _convert_keys_to_camel(obj: Any) -> Any:
    """Recursively converts dict keys from snake_case to camelCase."""
    if isinstance(obj, dict):
        return {
            _to_camel_case(k): _convert_keys_to_camel(v)
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [_convert_keys_to_camel(item) for item in obj]
    return obj


def _google_ads_mutate_description() -> str:
    entity_list = ", ".join(sorted(_ENTITY_MAP.keys()))
    return f"""Executes a create, update, or remove mutation on ANY Google Ads API entity.

This is a generic tool that supports all 79 mutable resource types in the Google Ads API.
For common operations (Campaign, AdGroup, Ad, Keyword, Budget), prefer the dedicated tools.
Use this tool for entity types not covered by dedicated tools.

Args:
    customer_id: The customer ID (digits only, no hyphens).
    entity_type: The entity type to mutate. Must be one of: {entity_list}
    action: The mutation action: "create", "update", or "remove".
    attributes: Dict of field names (snake_case) to values for create/update.
        Nested fields use nested dicts (e.g. {{"keyword": {{"text": "shoes", "match_type": "BROAD"}}}}).
        Enum values use their string names (e.g. "ENABLED", "SEARCH", "BROAD").
        Resource references use full resource name strings
        (e.g. "customers/123/campaigns/456").
    resource_name: The resource name string for update/remove
        (e.g. "customers/123/campaigns/456"). Required for update and remove.

Returns:
    A dict with the resource_name of the mutated entity.

### Available entity types
{entity_list}
"""


def google_ads_mutate(
    customer_id: str,
    entity_type: str,
    action: str,
    attributes: Dict[str, Any] = None,
    resource_name: str = None,
) -> dict:
    """Executes a mutation on any Google Ads API entity type."""
    if entity_type not in _ENTITY_MAP:
        raise ValueError(
            f"Unknown entity_type '{entity_type}'. "
            f"Valid types: {', '.join(sorted(_ENTITY_MAP.keys()))}"
        )

    if action not in ("create", "update", "remove"):
        raise ValueError(
            f"Invalid action '{action}'. Must be 'create', 'update', or 'remove'."
        )

    if action in ("update", "remove") and not resource_name:
        raise ValueError(
            f"resource_name is required for '{action}' operations."
        )

    if action in ("create", "update") and not attributes:
        if action == "create":
            raise ValueError(
                "attributes dict is required for 'create' operations."
            )

    service_name, mutate_method = _ENTITY_MAP[entity_type]
    client = utils.get_googleads_client()
    operation = client.get_type(f"{entity_type}Operation")

    if action == "create":
        resource = operation.create
        camel_attrs = _convert_keys_to_camel(attributes)
        json_format.ParseDict(camel_attrs, resource)

    elif action == "update":
        resource = operation.update
        resource.resource_name = resource_name
        if attributes:
            camel_attrs = _convert_keys_to_camel(attributes)
            json_format.ParseDict(camel_attrs, resource)
        client.copy_from(
            operation.update_mask,
            utils.build_field_mask(resource),
        )

    elif action == "remove":
        operation.remove = resource_name

    resource_names = utils.execute_mutate(
        service_name=service_name,
        mutate_method_name=mutate_method,
        customer_id=customer_id,
        operations=[operation],
    )

    return {"resource_name": resource_names[0]}


mcp.add_tool(
    google_ads_mutate,
    title="Mutate any Google Ads entity (create/update/remove)",
    description=_google_ads_mutate_description(),
)


def _google_ads_bulk_mutate_description() -> str:
    entity_list = ", ".join(sorted(_ENTITY_MAP.keys()))
    return f"""Executes multiple mutations atomically using GoogleAdsService.Mutate.

All operations succeed or all fail together. Supports temporary resource names
(negative IDs) to reference newly created resources within the same request.

Args:
    customer_id: The customer ID (digits only, no hyphens).
    operations: List of operation dicts, each with:
        - entity_type: The entity type (e.g. "Campaign", "AdGroup").
        - action: "create", "update", or "remove".
        - attributes: Dict of field names to values (for create/update).
        - resource_name: Resource name string (for update/remove).

Returns:
    A list of dicts with resource_name for each mutated entity.

### Temporary resource names
When creating multiple related resources in one call, use negative IDs as
temporary resource names. For example:
    - Create a budget with resource_name "customers/123/campaignBudgets/-1"
    - Reference it in a campaign: {{"campaign_budget": "customers/123/campaignBudgets/-1"}}
The API will substitute real IDs after creation.

### Available entity types
{entity_list}
"""


def google_ads_bulk_mutate(
    customer_id: str,
    operations: List[Dict[str, Any]],
) -> List[dict]:
    """Executes multiple mutations atomically via GoogleAdsService.Mutate."""
    client = utils.get_googleads_client()
    ga_service = utils.get_googleads_service("GoogleAdsService")

    mutate_operations = []

    for op_spec in operations:
        entity_type = op_spec.get("entity_type")
        action = op_spec.get("action")
        attributes = op_spec.get("attributes", {})
        resource_name = op_spec.get("resource_name")

        if entity_type not in _ENTITY_MAP:
            raise ValueError(
                f"Unknown entity_type '{entity_type}'. "
                f"Valid types: {', '.join(sorted(_ENTITY_MAP.keys()))}"
            )

        if action not in ("create", "update", "remove"):
            raise ValueError(
                f"Invalid action '{action}'. "
                "Must be 'create', 'update', or 'remove'."
            )

        # Build the entity-specific operation
        entity_operation = client.get_type(f"{entity_type}Operation")

        if action == "create":
            resource = entity_operation.create
            if attributes:
                camel_attrs = _convert_keys_to_camel(attributes)
                json_format.ParseDict(camel_attrs, resource)

        elif action == "update":
            resource = entity_operation.update
            resource.resource_name = resource_name
            if attributes:
                camel_attrs = _convert_keys_to_camel(attributes)
                json_format.ParseDict(camel_attrs, resource)
            client.copy_from(
                entity_operation.update_mask,
                utils.build_field_mask(resource),
            )

        elif action == "remove":
            entity_operation.remove = resource_name

        # Wrap in a MutateOperation
        mutate_op = client.get_type("MutateOperation")
        # The MutateOperation field name is the snake_case of the entity
        # operation type, e.g. "campaign_operation" for CampaignOperation
        op_field = _to_snake_case(entity_type) + "_operation"
        client.copy_from(
            getattr(mutate_op, op_field), entity_operation
        )
        mutate_operations.append(mutate_op)

    response = ga_service.mutate(
        customer_id=customer_id,
        mutate_operations=mutate_operations,
    )

    results = []
    for result in response.mutate_operation_responses:
        # Each response has exactly one of the *_result fields set
        for field in result.ListFields():
            field_name = field[0].name
            if field_name.endswith("_result"):
                results.append(
                    {"resource_name": field[1].resource_name}
                )
                break
    return results


def _to_snake_case(name: str) -> str:
    """Converts CamelCase to snake_case."""
    import re

    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


mcp.add_tool(
    google_ads_bulk_mutate,
    title="Bulk mutate multiple Google Ads entities atomically",
    description=_google_ads_bulk_mutate_description(),
)
