"""
Property-based tests for market price tools.

Tests Properties 6, 7, 8, and 9 from the design document.
"""

import pytest
from hypothesis import given, strategies as st, assume
from datetime import datetime, timedelta
from tools.market_tools import (
    get_market_prices,
    create_listing,
    search_products,
    track_expiry,
    LISTINGS_STORAGE
)


# Helper strategies
@st.composite
def location_strategy(draw):
    """Generate valid location dictionaries."""
    districts = ["Bangalore", "Mysore", "Mandya", "Hassan", "Tumkur"]
    states = ["Karnataka", "Tamil Nadu", "Andhra Pradesh"]
    return {
        "district": draw(st.sampled_from(districts)),
        "state": draw(st.sampled_from(states))
    }


# Feature: missionai-farmer-agent, Property 6: Multi-Market Price Display
@given(
    crop=st.sampled_from(["tomato", "onion", "potato", "rice", "wheat"]),
    location=location_strategy(),
    radius_km=st.integers(min_value=10, max_value=500)
)
@pytest.mark.property_test
def test_multi_market_price_display(crop, location, radius_km):
    """
    **Validates: Requirements 5.2**
    
    Property 6: Multi-Market Price Display
    For any market price query for a specific crop and location,
    the Market_Price_Agent SHALL return prices from at least two
    nearby markets when available.
    """
    results = get_market_prices(crop, location, radius_km)
    
    # If results exist, verify we have multiple markets (when available)
    if len(results) > 0:
        # Each result should have required fields
        for market in results:
            assert "market_name" in market
            assert "location" in market
            assert "price_per_kg" in market
            assert market["price_per_kg"] > 0
        
        # If crop has multiple markets in data, we should get at least 2
        # (This property holds for crops in our test data)
        if crop in ["tomato", "onion", "potato", "rice", "wheat"]:
            assert len(results) >= 2, \
                f"Expected at least 2 markets for {crop}, got {len(results)}"


# Feature: missionai-farmer-agent, Property 7: Listing Completeness
@given(
    product=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    quantity=st.floats(min_value=0.1, max_value=10000.0),
    quality=st.sampled_from(["grade_a", "grade_b", "organic"]),
    price=st.floats(min_value=1.0, max_value=1000.0),
    days_until_expiry=st.integers(min_value=1, max_value=365)
)
@pytest.mark.property_test
def test_listing_completeness(product, quantity, quality, price, days_until_expiry):
    """
    **Validates: Requirements 5.3, 5.4**
    
    Property 7: Listing Completeness
    For any produce listing creation request, the Market_Price_Agent
    SHALL require and store quantity, quality, and expiry information.
    """
    # Clear storage before test
    LISTINGS_STORAGE.clear()
    
    # Generate expiry date
    expiry_date = (datetime.now() + timedelta(days=days_until_expiry)).isoformat()
    
    # Create listing
    result = create_listing(
        product=product,
        quantity=quantity,
        quality=quality,
        expiry_date=expiry_date,
        price=price
    )
    
    # Verify all required fields are present and stored
    assert "quantity" in result
    assert result["quantity"] == quantity
    
    assert "quality" in result
    assert result["quality"] == quality
    
    assert "expiry_date" in result
    assert result["expiry_date"] == expiry_date
    
    assert "price_per_unit" in result
    assert result["price_per_unit"] == price
    
    # Verify listing was stored
    assert len(LISTINGS_STORAGE) == 1
    assert LISTINGS_STORAGE[0]["listing_id"] == result["listing_id"]


# Feature: missionai-farmer-agent, Property 8: Expiry Alert Generation
@given(
    days_until_expiry=st.integers(min_value=0, max_value=3)
)
@pytest.mark.property_test
def test_expiry_alert_generation(days_until_expiry):
    """
    **Validates: Requirements 5.5**
    
    Property 8: Expiry Alert Generation
    For any active listing with an expiry date, when the current date
    is within 3 days of expiry, the Market_Price_Agent SHALL generate an alert.
    """
    # Clear storage
    LISTINGS_STORAGE.clear()
    
    # Create listing with specific expiry
    expiry_date = (datetime.now() + timedelta(days=days_until_expiry)).isoformat()
    
    listing = create_listing(
        product="tomato",
        quantity=100.0,
        quality="grade_a",
        expiry_date=expiry_date,
        price=25.0
    )
    
    # Track expiry
    result = track_expiry(listing["listing_id"])
    
    # Verify alert is generated for items expiring within 3 days
    assert result["alert_generated"] is True, \
        f"Alert should be generated for listing expiring in {days_until_expiry} days"
    assert result["alert_message"] is not None
    assert result["days_until_expiry"] == days_until_expiry


# Feature: missionai-farmer-agent, Property 9: Sustainable Product Prioritization
@given(
    num_sustainable=st.integers(min_value=1, max_value=5),
    num_regular=st.integers(min_value=1, max_value=5)
)
@pytest.mark.property_test
def test_sustainable_product_prioritization(num_sustainable, num_regular):
    """
    **Validates: Requirements 5.6**
    
    Property 9: Sustainable Product Prioritization
    For any product search results containing both sustainable and
    non-sustainable options, the Market_Price_Agent SHALL rank
    sustainable/organic products higher in the result list.
    """
    # Clear storage
    LISTINGS_STORAGE.clear()
    
    # Create sustainable listings
    for i in range(num_sustainable):
        create_listing(
            product="tomato",
            quantity=100.0,
            quality="organic",
            expiry_date=(datetime.now() + timedelta(days=30)).isoformat(),
            price=30.0 + i,  # Varying prices
            is_sustainable=True
        )
    
    # Create regular listings
    for i in range(num_regular):
        create_listing(
            product="tomato",
            quantity=100.0,
            quality="grade_a",
            expiry_date=(datetime.now() + timedelta(days=30)).isoformat(),
            price=25.0 + i,  # Varying prices
            is_sustainable=False
        )
    
    # Search for products
    results = search_products("tomato")
    
    # Verify sustainable products come first
    assert len(results) == num_sustainable + num_regular
    
    # All sustainable products should appear before non-sustainable ones
    sustainable_indices = [i for i, r in enumerate(results) if r["is_sustainable"]]
    non_sustainable_indices = [i for i, r in enumerate(results) if not r["is_sustainable"]]
    
    if sustainable_indices and non_sustainable_indices:
        max_sustainable_index = max(sustainable_indices)
        min_non_sustainable_index = min(non_sustainable_indices)
        assert max_sustainable_index < min_non_sustainable_index, \
            "Sustainable products should appear before non-sustainable products"


# Additional unit tests
def test_get_market_prices_invalid_crop():
    """Test market prices with empty crop name."""
    with pytest.raises(ValueError) as exc_info:
        get_market_prices("", {"district": "Bangalore", "state": "Karnataka"}, 100)
    assert "crop" in str(exc_info.value).lower()


def test_get_market_prices_invalid_location():
    """Test market prices with invalid location."""
    with pytest.raises(ValueError) as exc_info:
        get_market_prices("tomato", {"district": "Bangalore"}, 100)  # Missing state
    assert "location" in str(exc_info.value).lower()


def test_create_listing_invalid_quantity():
    """Test listing creation with invalid quantity."""
    with pytest.raises(ValueError) as exc_info:
        create_listing(
            product="tomato",
            quantity=-10.0,
            quality="grade_a",
            expiry_date="2024-12-31",
            price=25.0
        )
    assert "quantity" in str(exc_info.value).lower()


def test_create_listing_invalid_price():
    """Test listing creation with invalid price."""
    with pytest.raises(ValueError) as exc_info:
        create_listing(
            product="tomato",
            quantity=100.0,
            quality="grade_a",
            expiry_date="2024-12-31",
            price=0.0
        )
    assert "price" in str(exc_info.value).lower()


def test_search_products_with_filters():
    """Test product search with various filters."""
    LISTINGS_STORAGE.clear()
    
    # Create test listings
    create_listing("tomato", 100.0, "grade_a", "2024-12-31", 25.0, location={"state": "Karnataka"})
    create_listing("tomato", 100.0, "organic", "2024-12-31", 35.0, location={"state": "Karnataka"}, is_sustainable=True)
    create_listing("onion", 100.0, "grade_a", "2024-12-31", 20.0, location={"state": "Karnataka"})
    
    # Search with quality filter
    results = search_products("tomato", {"quality": "organic"})
    assert len(results) == 1
    assert results[0]["quality"] == "organic"
    
    # Search with max_price filter
    results = search_products("tomato", {"max_price": 30.0})
    assert len(results) == 1
    assert results[0]["price_per_unit"] <= 30.0
    
    # Search with sustainable_only filter
    results = search_products("tomato", {"sustainable_only": True})
    assert len(results) == 1
    assert results[0]["is_sustainable"] is True


def test_track_expiry_not_found():
    """Test expiry tracking for non-existent listing."""
    with pytest.raises(ValueError) as exc_info:
        track_expiry("non_existent_id")
    assert "not found" in str(exc_info.value).lower()


def test_track_expiry_expired_product():
    """Test expiry tracking for already expired product."""
    LISTINGS_STORAGE.clear()
    
    # Create listing that expired 5 days ago
    expiry_date = (datetime.now() - timedelta(days=5)).isoformat()
    listing = create_listing("tomato", 100.0, "grade_a", expiry_date, 25.0)
    
    result = track_expiry(listing["listing_id"])
    
    assert result["status"] == "expired"
    assert result["days_until_expiry"] < 0
    assert "expired" in result["alert_message"].lower()


def test_get_market_prices_unknown_crop():
    """Test market prices for crop not in database."""
    results = get_market_prices(
        "unknown_crop",
        {"district": "Bangalore", "state": "Karnataka"},
        100
    )
    assert results == []
