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

"""Test cases for dedicated mutation tools."""

import unittest
from unittest.mock import MagicMock, patch


def _mock_execute_mutate(resource_name):
    """Returns a patcher for utils.execute_mutate returning the given name."""
    return patch(
        "ads_mcp.utils.execute_mutate",
        return_value=[resource_name],
    )


class TestBudgetTools(unittest.TestCase):
    """Tests for campaign budget tools."""

    @_mock_execute_mutate("customers/123/campaignBudgets/456")
    def test_create_campaign_budget(self, mock_mutate):
        from ads_mcp.tools.budgets import create_campaign_budget

        result = create_campaign_budget(
            customer_id="1234567890",
            name="Test Budget",
            amount_micros=50000000,
        )
        self.assertEqual(
            result["resource_name"],
            "customers/123/campaignBudgets/456",
        )
        mock_mutate.assert_called_once()
        call_kwargs = mock_mutate.call_args[1]
        self.assertEqual(
            call_kwargs["service_name"], "CampaignBudgetService"
        )
        self.assertEqual(
            call_kwargs["mutate_method_name"],
            "mutate_campaign_budgets",
        )
        self.assertEqual(
            call_kwargs["customer_id"], "1234567890"
        )

    @_mock_execute_mutate("customers/123/campaignBudgets/456")
    def test_update_campaign_budget(self, mock_mutate):
        from ads_mcp.tools.budgets import update_campaign_budget

        result = update_campaign_budget(
            customer_id="1234567890",
            budget_id="456",
            amount_micros=75000000,
        )
        self.assertEqual(
            result["resource_name"],
            "customers/123/campaignBudgets/456",
        )

    def test_update_campaign_budget_no_fields_raises(self):
        from ads_mcp.tools.budgets import update_campaign_budget

        with self.assertRaises(ValueError) as ctx:
            update_campaign_budget(
                customer_id="123", budget_id="456"
            )
        self.assertIn("At least one field", str(ctx.exception))

    @_mock_execute_mutate("customers/123/campaignBudgets/456")
    def test_remove_campaign_budget(self, mock_mutate):
        from ads_mcp.tools.budgets import remove_campaign_budget

        result = remove_campaign_budget(
            customer_id="1234567890", budget_id="456"
        )
        self.assertEqual(
            result["resource_name"],
            "customers/123/campaignBudgets/456",
        )


class TestCampaignTools(unittest.TestCase):
    """Tests for campaign tools."""

    @_mock_execute_mutate("customers/123/campaigns/789")
    def test_create_campaign(self, mock_mutate):
        from ads_mcp.tools.campaigns import create_campaign

        result = create_campaign(
            customer_id="1234567890",
            name="Test Campaign",
            budget_id="456",
        )
        self.assertEqual(
            result["resource_name"],
            "customers/123/campaigns/789",
        )
        call_kwargs = mock_mutate.call_args[1]
        self.assertEqual(
            call_kwargs["service_name"], "CampaignService"
        )

    @_mock_execute_mutate("customers/123/campaigns/789")
    def test_create_campaign_with_dates(self, mock_mutate):
        from ads_mcp.tools.campaigns import create_campaign

        result = create_campaign(
            customer_id="1234567890",
            name="Dated Campaign",
            budget_id="456",
            start_date_time="2025-06-01 00:00:00",
            end_date_time="2025-12-31 23:59:59",
        )
        self.assertIn("resource_name", result)

    @_mock_execute_mutate("customers/123/campaigns/789")
    def test_update_campaign_status(self, mock_mutate):
        from ads_mcp.tools.campaigns import update_campaign

        result = update_campaign(
            customer_id="1234567890",
            campaign_id="789",
            status="PAUSED",
        )
        self.assertEqual(
            result["resource_name"],
            "customers/123/campaigns/789",
        )

    def test_update_campaign_no_fields_raises(self):
        from ads_mcp.tools.campaigns import update_campaign

        with self.assertRaises(ValueError):
            update_campaign(
                customer_id="123", campaign_id="789"
            )

    @_mock_execute_mutate("customers/123/campaigns/789")
    def test_remove_campaign(self, mock_mutate):
        from ads_mcp.tools.campaigns import remove_campaign

        result = remove_campaign(
            customer_id="1234567890", campaign_id="789"
        )
        self.assertEqual(
            result["resource_name"],
            "customers/123/campaigns/789",
        )


class TestAdGroupTools(unittest.TestCase):
    """Tests for ad group tools."""

    @_mock_execute_mutate("customers/123/adGroups/111")
    def test_create_ad_group(self, mock_mutate):
        from ads_mcp.tools.ad_groups import create_ad_group

        result = create_ad_group(
            customer_id="1234567890",
            campaign_id="789",
            name="Test Ad Group",
        )
        self.assertEqual(
            result["resource_name"],
            "customers/123/adGroups/111",
        )
        call_kwargs = mock_mutate.call_args[1]
        self.assertEqual(
            call_kwargs["service_name"], "AdGroupService"
        )

    @_mock_execute_mutate("customers/123/adGroups/111")
    def test_create_ad_group_with_bid(self, mock_mutate):
        from ads_mcp.tools.ad_groups import create_ad_group

        result = create_ad_group(
            customer_id="1234567890",
            campaign_id="789",
            name="Bid Group",
            cpc_bid_micros=1500000,
        )
        self.assertIn("resource_name", result)

    @_mock_execute_mutate("customers/123/adGroups/111")
    def test_update_ad_group(self, mock_mutate):
        from ads_mcp.tools.ad_groups import update_ad_group

        result = update_ad_group(
            customer_id="1234567890",
            ad_group_id="111",
            status="ENABLED",
        )
        self.assertIn("resource_name", result)

    def test_update_ad_group_no_fields_raises(self):
        from ads_mcp.tools.ad_groups import update_ad_group

        with self.assertRaises(ValueError):
            update_ad_group(
                customer_id="123", ad_group_id="111"
            )

    @_mock_execute_mutate("customers/123/adGroups/111")
    def test_remove_ad_group(self, mock_mutate):
        from ads_mcp.tools.ad_groups import remove_ad_group

        result = remove_ad_group(
            customer_id="1234567890", ad_group_id="111"
        )
        self.assertIn("resource_name", result)


class TestAdTools(unittest.TestCase):
    """Tests for responsive search ad tools."""

    @_mock_execute_mutate("customers/123/adGroupAds/111~222")
    def test_create_responsive_search_ad(self, mock_mutate):
        from ads_mcp.tools.ads import create_responsive_search_ad

        result = create_responsive_search_ad(
            customer_id="1234567890",
            ad_group_id="111",
            headlines=["H1", "H2", "H3"],
            descriptions=["D1", "D2"],
            final_urls=["https://example.com"],
        )
        self.assertEqual(
            result["resource_name"],
            "customers/123/adGroupAds/111~222",
        )
        call_kwargs = mock_mutate.call_args[1]
        self.assertEqual(
            call_kwargs["service_name"], "AdGroupAdService"
        )

    @_mock_execute_mutate("customers/123/adGroupAds/111~222")
    def test_update_ad_group_ad_status(self, mock_mutate):
        from ads_mcp.tools.ads import update_ad_group_ad_status

        result = update_ad_group_ad_status(
            customer_id="1234567890",
            ad_group_id="111",
            ad_id="222",
            status="PAUSED",
        )
        self.assertIn("resource_name", result)

    @_mock_execute_mutate("customers/123/adGroupAds/111~222")
    def test_remove_ad(self, mock_mutate):
        from ads_mcp.tools.ads import remove_ad

        result = remove_ad(
            customer_id="1234567890",
            ad_group_id="111",
            ad_id="222",
        )
        self.assertIn("resource_name", result)


class TestKeywordTools(unittest.TestCase):
    """Tests for keyword tools."""

    @_mock_execute_mutate(
        "customers/123/adGroupCriteria/111~333"
    )
    def test_create_keyword(self, mock_mutate):
        from ads_mcp.tools.keywords import create_keyword

        result = create_keyword(
            customer_id="1234567890",
            ad_group_id="111",
            keyword_text="running shoes",
        )
        self.assertEqual(
            result["resource_name"],
            "customers/123/adGroupCriteria/111~333",
        )
        call_kwargs = mock_mutate.call_args[1]
        self.assertEqual(
            call_kwargs["service_name"],
            "AdGroupCriterionService",
        )

    @_mock_execute_mutate(
        "customers/123/adGroupCriteria/111~333"
    )
    def test_create_keyword_exact_match(self, mock_mutate):
        from ads_mcp.tools.keywords import create_keyword

        result = create_keyword(
            customer_id="1234567890",
            ad_group_id="111",
            keyword_text="running shoes",
            match_type="EXACT",
            cpc_bid_micros=2000000,
        )
        self.assertIn("resource_name", result)

    @_mock_execute_mutate(
        "customers/123/adGroupCriteria/111~333"
    )
    def test_update_keyword(self, mock_mutate):
        from ads_mcp.tools.keywords import update_keyword

        result = update_keyword(
            customer_id="1234567890",
            ad_group_id="111",
            criterion_id="333",
            status="PAUSED",
        )
        self.assertIn("resource_name", result)

    def test_update_keyword_no_fields_raises(self):
        from ads_mcp.tools.keywords import update_keyword

        with self.assertRaises(ValueError):
            update_keyword(
                customer_id="123",
                ad_group_id="111",
                criterion_id="333",
            )

    @_mock_execute_mutate(
        "customers/123/adGroupCriteria/111~333"
    )
    def test_remove_keyword(self, mock_mutate):
        from ads_mcp.tools.keywords import remove_keyword

        result = remove_keyword(
            customer_id="1234567890",
            ad_group_id="111",
            criterion_id="333",
        )
        self.assertIn("resource_name", result)
