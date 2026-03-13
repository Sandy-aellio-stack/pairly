"""
Unit tests for the privacy-safe location service (tb_location_service).

Covers:
- Coordinate precision reduction
- Distance bucketing and display formatting
- Location freshness checks
- Jitter / random offset utility
"""

import math
import time
from datetime import datetime, timezone, timedelta

import pytest

from backend.services.tb_location_service import PrivacyLocation, DISTANCE_BUCKET_SIZE_KM


# ---------------------------------------------------------------------------
# PrivacyLocation.reduce_precision
# ---------------------------------------------------------------------------

class TestReducePrecision:
    def test_reduces_to_three_decimal_places_by_default(self):
        lat, lng = PrivacyLocation.reduce_precision(12.97165, 77.59460)
        assert lat == round(12.97165, 3)
        assert lng == round(77.59460, 3)

    def test_custom_decimal_places(self):
        lat, lng = PrivacyLocation.reduce_precision(12.97165, 77.59460, decimals=2)
        assert lat == round(12.97165, 2)
        assert lng == round(77.59460, 2)

    def test_exact_values_unchanged(self):
        lat, lng = PrivacyLocation.reduce_precision(12.000, 77.000)
        assert lat == 12.0
        assert lng == 77.0

    def test_negative_coordinates(self):
        lat, lng = PrivacyLocation.reduce_precision(-33.86851, 151.20930)
        assert lat == round(-33.86851, 3)
        assert lng == round(151.20930, 3)


# ---------------------------------------------------------------------------
# PrivacyLocation.bucket_distance
# ---------------------------------------------------------------------------

class TestBucketDistance:
    def test_sub_one_km_returns_bucket_size(self):
        result = PrivacyLocation.bucket_distance(0.5)
        assert result == DISTANCE_BUCKET_SIZE_KM

    def test_exactly_one_km(self):
        result = PrivacyLocation.bucket_distance(1.0)
        assert result == 1.0

    def test_rounds_up_to_next_bucket(self):
        result = PrivacyLocation.bucket_distance(1.1)
        assert result == 2.0

    def test_large_distance(self):
        result = PrivacyLocation.bucket_distance(47.3)
        assert result == 48.0

    def test_exactly_on_boundary(self):
        result = PrivacyLocation.bucket_distance(10.0)
        assert result == 10.0


# ---------------------------------------------------------------------------
# PrivacyLocation.format_distance_display
# ---------------------------------------------------------------------------

class TestFormatDistanceDisplay:
    def test_under_1km(self):
        assert PrivacyLocation.format_distance_display(0.3) == "< 1 km"

    def test_between_1_and_5(self):
        display = PrivacyLocation.format_distance_display(3.0)
        assert "3" in display

    def test_between_5_and_10(self):
        assert PrivacyLocation.format_distance_display(7.0) == "< 10 km"

    def test_between_10_and_25(self):
        assert PrivacyLocation.format_distance_display(15.0) == "< 25 km"

    def test_beyond_25(self):
        display = PrivacyLocation.format_distance_display(50.0)
        assert "km" in display


# ---------------------------------------------------------------------------
# PrivacyLocation.add_random_offset
# ---------------------------------------------------------------------------

class TestAddRandomOffset:
    def test_offset_is_small(self):
        """Offset should be within ~200m (~0.002 degrees)."""
        lat, lng = PrivacyLocation.add_random_offset(12.9716, 77.5946)
        assert abs(lat - 12.9716) < 0.005
        assert abs(lng - 77.5946) < 0.005

    def test_deterministic_for_same_input(self):
        lat1, lng1 = PrivacyLocation.add_random_offset(12.9716, 77.5946)
        lat2, lng2 = PrivacyLocation.add_random_offset(12.9716, 77.5946)
        assert lat1 == lat2
        assert lng1 == lng2

    def test_different_inputs_give_different_offsets(self):
        lat1, lng1 = PrivacyLocation.add_random_offset(12.9716, 77.5946)
        lat2, lng2 = PrivacyLocation.add_random_offset(13.0000, 77.0000)
        assert lat1 != lat2 or lng1 != lng2


# ---------------------------------------------------------------------------
# PrivacyLocation.is_location_fresh
# ---------------------------------------------------------------------------

class TestIsLocationFresh:
    def test_fresh_location_returns_true(self):
        recent = datetime.now(timezone.utc) - timedelta(minutes=5)
        assert PrivacyLocation.is_location_fresh(recent) is True

    def test_stale_location_returns_false(self):
        stale = datetime.now(timezone.utc) - timedelta(hours=1)
        assert PrivacyLocation.is_location_fresh(stale) is False

    def test_none_returns_false(self):
        assert PrivacyLocation.is_location_fresh(None) is False
