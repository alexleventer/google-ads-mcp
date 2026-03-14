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

"""Test cases for mutation helper functions in the utils module."""

import unittest
from unittest.mock import MagicMock, patch

from ads_mcp import utils


class TestResolveEnum(unittest.TestCase):
    """Tests for the resolve_enum helper."""

    def test_resolve_valid_enum(self):
        """Tests resolving a valid enum string value."""
        result = utils.resolve_enum("CampaignStatusEnum", "PAUSED")
        self.assertEqual(result, 3)

    def test_resolve_valid_enum_enabled(self):
        """Tests resolving ENABLED status."""
        result = utils.resolve_enum("CampaignStatusEnum", "ENABLED")
        self.assertEqual(result, 2)

    def test_resolve_invalid_enum_raises(self):
        """Tests that an invalid enum value raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            utils.resolve_enum("CampaignStatusEnum", "INVALID_VALUE")
        self.assertIn("Invalid CampaignStatusEnum", str(ctx.exception))
        self.assertIn("INVALID_VALUE", str(ctx.exception))
        self.assertIn("Valid values:", str(ctx.exception))

    def test_resolve_different_enum_types(self):
        """Tests resolving different enum types."""
        result = utils.resolve_enum(
            "AdvertisingChannelTypeEnum", "SEARCH"
        )
        self.assertEqual(result, 2)

        result = utils.resolve_enum(
            "AdGroupStatusEnum", "PAUSED"
        )
        self.assertEqual(result, 3)


class TestBuildFieldMask(unittest.TestCase):
    """Tests for the build_field_mask helper."""

    def test_field_mask_includes_set_fields(self):
        """Tests that field mask includes fields that were set."""
        client = utils.get_googleads_client()
        campaign = client.get_type("Campaign")
        campaign.resource_name = "customers/123/campaigns/456"
        campaign.name = "Test"

        mask = utils.build_field_mask(campaign)
        self.assertIn("resource_name", mask.paths)
        self.assertIn("name", mask.paths)

    def test_field_mask_excludes_unset_fields(self):
        """Tests that field mask excludes fields not explicitly set."""
        client = utils.get_googleads_client()
        campaign = client.get_type("Campaign")
        campaign.name = "Test"

        mask = utils.build_field_mask(campaign)
        self.assertNotIn("status", mask.paths)
        self.assertNotIn("start_date_time", mask.paths)


class TestExecuteMutate(unittest.TestCase):
    """Tests for the execute_mutate helper."""

    @patch("ads_mcp.utils.get_googleads_service")
    def test_execute_mutate_calls_correct_service(
        self, mock_get_service
    ):
        """Tests that execute_mutate calls the right service method."""
        mock_result = MagicMock()
        mock_result.resource_name = "customers/123/campaigns/456"
        mock_response = MagicMock()
        mock_response.results = [mock_result]

        mock_service = MagicMock()
        mock_service.mutate_campaigns.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = utils.execute_mutate(
            service_name="CampaignService",
            mutate_method_name="mutate_campaigns",
            customer_id="1234567890",
            operations=["fake_op"],
        )

        mock_get_service.assert_called_once_with("CampaignService")
        mock_service.mutate_campaigns.assert_called_once_with(
            customer_id="1234567890", operations=["fake_op"]
        )
        self.assertEqual(
            result, ["customers/123/campaigns/456"]
        )

    @patch("ads_mcp.utils.get_googleads_service")
    def test_execute_mutate_returns_multiple_results(
        self, mock_get_service
    ):
        """Tests that execute_mutate handles multiple results."""
        mock_r1 = MagicMock()
        mock_r1.resource_name = "customers/123/campaigns/1"
        mock_r2 = MagicMock()
        mock_r2.resource_name = "customers/123/campaigns/2"
        mock_response = MagicMock()
        mock_response.results = [mock_r1, mock_r2]

        mock_service = MagicMock()
        mock_service.mutate_campaigns.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = utils.execute_mutate(
            service_name="CampaignService",
            mutate_method_name="mutate_campaigns",
            customer_id="123",
            operations=["op1", "op2"],
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result[0], "customers/123/campaigns/1"
        )
        self.assertEqual(
            result[1], "customers/123/campaigns/2"
        )
