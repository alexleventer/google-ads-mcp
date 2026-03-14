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

"""Test cases for the generic mutate tool and helpers."""

import unittest
from unittest.mock import patch

from ads_mcp.tools.mutate import (
    _to_camel_case,
    _convert_keys_to_camel,
    _to_snake_case,
    _ENTITY_MAP,
    google_ads_mutate,
)


class TestToCamelCase(unittest.TestCase):
    """Tests for the _to_camel_case helper."""

    def test_simple_snake_case(self):
        self.assertEqual(
            _to_camel_case("campaign_budget"), "campaignBudget"
        )

    def test_single_word(self):
        self.assertEqual(_to_camel_case("name"), "name")

    def test_multiple_underscores(self):
        self.assertEqual(
            _to_camel_case("ad_group_criterion_label"),
            "adGroupCriterionLabel",
        )

    def test_match_type(self):
        self.assertEqual(
            _to_camel_case("match_type"), "matchType"
        )


class TestConvertKeysToCamel(unittest.TestCase):
    """Tests for the _convert_keys_to_camel helper."""

    def test_flat_dict(self):
        result = _convert_keys_to_camel(
            {"campaign_budget": "foo", "status": "ENABLED"}
        )
        self.assertEqual(
            result,
            {"campaignBudget": "foo", "status": "ENABLED"},
        )

    def test_nested_dict(self):
        result = _convert_keys_to_camel(
            {
                "keyword": {
                    "match_type": "BROAD",
                    "text": "shoes",
                }
            }
        )
        self.assertEqual(
            result,
            {"keyword": {"matchType": "BROAD", "text": "shoes"}},
        )

    def test_list_values(self):
        result = _convert_keys_to_camel(
            {
                "final_urls": ["https://example.com"],
                "items": [
                    {"field_name": "a"},
                    {"field_name": "b"},
                ],
            }
        )
        self.assertEqual(
            result["finalUrls"], ["https://example.com"]
        )
        self.assertEqual(
            result["items"],
            [{"fieldName": "a"}, {"fieldName": "b"}],
        )

    def test_non_dict_passthrough(self):
        self.assertEqual(_convert_keys_to_camel("hello"), "hello")
        self.assertEqual(_convert_keys_to_camel(42), 42)
        self.assertIsNone(_convert_keys_to_camel(None))


class TestToSnakeCase(unittest.TestCase):
    """Tests for the _to_snake_case helper."""

    def test_simple_camel(self):
        self.assertEqual(
            _to_snake_case("Campaign"), "campaign"
        )

    def test_multi_word(self):
        self.assertEqual(
            _to_snake_case("AdGroupCriterion"),
            "ad_group_criterion",
        )

    def test_with_acronym(self):
        self.assertEqual(
            _to_snake_case("CampaignBudget"), "campaign_budget"
        )


class TestEntityMap(unittest.TestCase):
    """Tests for the _ENTITY_MAP completeness."""

    def test_entity_map_has_campaign(self):
        self.assertIn("Campaign", _ENTITY_MAP)
        svc, method = _ENTITY_MAP["Campaign"]
        self.assertEqual(svc, "CampaignService")
        self.assertEqual(method, "mutate_campaigns")

    def test_entity_map_has_ad_group(self):
        self.assertIn("AdGroup", _ENTITY_MAP)

    def test_entity_map_has_at_least_78_entries(self):
        self.assertGreaterEqual(len(_ENTITY_MAP), 78)

    def test_all_entries_have_service_and_method(self):
        for entity, (svc, method) in _ENTITY_MAP.items():
            self.assertTrue(
                svc.endswith("Service"),
                f"{entity}: service '{svc}' doesn't end with 'Service'",
            )
            self.assertTrue(
                method.startswith("mutate"),
                f"{entity}: method '{method}' doesn't start with 'mutate'",
            )


class TestGoogleAdsMutateValidation(unittest.TestCase):
    """Tests for input validation in google_ads_mutate."""

    def test_invalid_entity_type_raises(self):
        with self.assertRaises(ValueError) as ctx:
            google_ads_mutate(
                customer_id="123",
                entity_type="NonExistentType",
                action="create",
                attributes={"name": "test"},
            )
        self.assertIn("Unknown entity_type", str(ctx.exception))

    def test_invalid_action_raises(self):
        with self.assertRaises(ValueError) as ctx:
            google_ads_mutate(
                customer_id="123",
                entity_type="Campaign",
                action="delete",
                attributes={"name": "test"},
            )
        self.assertIn("Invalid action", str(ctx.exception))

    def test_update_without_resource_name_raises(self):
        with self.assertRaises(ValueError) as ctx:
            google_ads_mutate(
                customer_id="123",
                entity_type="Campaign",
                action="update",
                attributes={"name": "new name"},
            )
        self.assertIn(
            "resource_name is required", str(ctx.exception)
        )

    def test_remove_without_resource_name_raises(self):
        with self.assertRaises(ValueError) as ctx:
            google_ads_mutate(
                customer_id="123",
                entity_type="Campaign",
                action="remove",
            )
        self.assertIn(
            "resource_name is required", str(ctx.exception)
        )

    def test_create_without_attributes_raises(self):
        with self.assertRaises(ValueError) as ctx:
            google_ads_mutate(
                customer_id="123",
                entity_type="Campaign",
                action="create",
            )
        self.assertIn(
            "attributes dict is required", str(ctx.exception)
        )

    @patch("ads_mcp.utils.execute_mutate")
    def test_create_calls_execute_mutate(self, mock_mutate):
        mock_mutate.return_value = [
            "customers/123/campaigns/456"
        ]

        result = google_ads_mutate(
            customer_id="1234567890",
            entity_type="Campaign",
            action="create",
            attributes={
                "name": "Test",
                "status": "PAUSED",
                "advertising_channel_type": "SEARCH",
                "campaign_budget": "customers/1234567890/campaignBudgets/1",
            },
        )

        self.assertEqual(
            result["resource_name"],
            "customers/123/campaigns/456",
        )
        mock_mutate.assert_called_once()
        call_kwargs = mock_mutate.call_args[1]
        self.assertEqual(
            call_kwargs["service_name"], "CampaignService"
        )
        self.assertEqual(
            call_kwargs["mutate_method_name"], "mutate_campaigns"
        )

    @patch("ads_mcp.utils.execute_mutate")
    def test_remove_calls_execute_mutate(self, mock_mutate):
        mock_mutate.return_value = [
            "customers/123/campaigns/456"
        ]

        result = google_ads_mutate(
            customer_id="1234567890",
            entity_type="Campaign",
            action="remove",
            resource_name="customers/123/campaigns/456",
        )

        self.assertEqual(
            result["resource_name"],
            "customers/123/campaigns/456",
        )

    @patch("ads_mcp.utils.execute_mutate")
    def test_update_calls_execute_mutate(self, mock_mutate):
        mock_mutate.return_value = [
            "customers/123/campaigns/456"
        ]

        result = google_ads_mutate(
            customer_id="1234567890",
            entity_type="Campaign",
            action="update",
            resource_name="customers/123/campaigns/456",
            attributes={"name": "Updated Name"},
        )

        self.assertEqual(
            result["resource_name"],
            "customers/123/campaigns/456",
        )

    @patch("ads_mcp.utils.execute_mutate")
    def test_create_label(self, mock_mutate):
        """Tests generic mutate with a non-common entity type."""
        mock_mutate.return_value = [
            "customers/123/labels/789"
        ]

        result = google_ads_mutate(
            customer_id="1234567890",
            entity_type="Label",
            action="create",
            attributes={"name": "My Label"},
        )

        self.assertEqual(
            result["resource_name"],
            "customers/123/labels/789",
        )
        call_kwargs = mock_mutate.call_args[1]
        self.assertEqual(
            call_kwargs["service_name"], "LabelService"
        )
        self.assertEqual(
            call_kwargs["mutate_method_name"], "mutate_labels"
        )

    @patch("ads_mcp.utils.execute_mutate")
    def test_create_with_nested_attributes(self, mock_mutate):
        """Tests generic mutate with nested attributes (keyword)."""
        mock_mutate.return_value = [
            "customers/123/adGroupCriteria/456~789"
        ]

        result = google_ads_mutate(
            customer_id="1234567890",
            entity_type="AdGroupCriterion",
            action="create",
            attributes={
                "ad_group": "customers/1234567890/adGroups/456",
                "status": "ENABLED",
                "keyword": {
                    "text": "running shoes",
                    "match_type": "BROAD",
                },
            },
        )

        self.assertIn("resource_name", result)
