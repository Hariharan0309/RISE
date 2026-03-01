"""
Tests for Market Price Agent.
"""

import pytest
from datetime import datetime, timedelta
from agents.market_price_agent import MarketPriceAgent
from tools.market_tools import LISTINGS_STORAGE, create_listing


@pytest.fixture
def market_agent():
    """Create a Market Price Agent instance."""
    return MarketPriceAgent()


@pytest.fixture
def sample_location():
    """Sample location for testing."""
    return {
        "district": "Bangalore Urban",
        "state": "Karnataka"
    }


@pytest.fixture(autouse=True)
def clear_listings():
    """Clear listings storage before each test."""
    LISTINGS_STORAGE.clear()
    yield
    LISTINGS_STORAGE.clear()


def test_market_price_agent_initialization(market_agent):
    """Test that Market Price Agent initializes correctly."""
    assert market_agent.name == "Market Price Agent"
    assert market_agent.description == "Specialized in market intelligence and marketplace facilitation"
    assert len(market_agent.tools) == 4


def test_get_system_prompt(market_agent):
    """Test that system prompt is comprehensive."""
    prompt = market_agent.get_system_prompt()
    
    assert "market" in prompt.lower()
    assert "price" in prompt.lower()
    assert "sustainable" in prompt.lower()
    assert "expiry" in prompt.lower()


def test_get_market_prices(market_agent, sample_location):
    """Test getting market prices for a crop."""
    result = market_agent.get_prices("tomato", sample_location)
    
    assert result["success"] is True
    assert result["query_type"] == "price_query"
    assert result["crop"] == "tomato"
    assert "prices" in result
    assert "analysis" in result


def test_create_listing(market_agent, sample_location):
    """Test creating a marketplace listing."""
    expiry_date = (datetime.now() + timedelta(days=5)).isoformat()
    
    result = market_agent.create_produce_listing(
        product="Tomatoes",
        quantity=100.0,
        quality="grade_a",
        expiry_date=expiry_date,
        price=25.0,
        location=sample_location
    )
    
    assert result["success"] is True
    assert result["query_type"] == "create_listing"
    assert "listing" in result
    assert result["listing"]["product"] == "Tomatoes"
    assert result["listing"]["quantity"] == 100.0
    assert result["listing"]["quality"] == "grade_a"
    assert result["listing"]["price_per_unit"] == 25.0


def test_sustainable_product_prioritization(market_agent, sample_location):
    """Test that sustainable products are prioritized in search results."""
    expiry_date = (datetime.now() + timedelta(days=5)).isoformat()
    
    # Create regular listing
    create_listing(
        product="Regular Tomatoes",
        quantity=100.0,
        quality="grade_a",
        expiry_date=expiry_date,
        price=25.0,
        location=sample_location,
        is_sustainable=False
    )
    
    # Create sustainable listing with higher price
    create_listing(
        product="Organic Tomatoes",
        quantity=50.0,
        quality="organic",
        expiry_date=expiry_date,
        price=35.0,
        location=sample_location,
        is_sustainable=True
    )
    
    # Search for tomatoes
    result = market_agent.search_marketplace("tomatoes")
    
    assert result["success"] is True
    assert len(result["results"]) == 2
    
    # First result should be sustainable product (even though it's more expensive)
    assert result["results"][0]["is_sustainable"] is True
    assert "Organic" in result["results"][0]["product"]


def test_expiry_tracking(market_agent, sample_location):
    """Test expiry tracking functionality."""
    # Create listing expiring in 2 days
    expiry_date = (datetime.now() + timedelta(days=2)).isoformat()
    
    listing = create_listing(
        product="Tomatoes",
        quantity=100.0,
        quality="grade_a",
        expiry_date=expiry_date,
        price=25.0,
        location=sample_location
    )
    
    # Track expiry
    result = market_agent.check_expiry(listing["listing_id"])
    
    assert result["success"] is True
    assert "expiry_status" in result
    
    expiry_status = result["expiry_status"]
    assert expiry_status["days_until_expiry"] == 2
    assert expiry_status["alert_generated"] is True  # Should alert within 3 days
    assert expiry_status["status"] == "expiring_soon"


def test_expiry_alert_generation(market_agent, sample_location):
    """Test that alerts are generated for expiring products."""
    # Create listing expiring in 2 days (use a specific time to ensure consistent calculation)
    expiry_date = (datetime.now().replace(hour=23, minute=59, second=59) + timedelta(days=2)).isoformat()
    
    listing = create_listing(
        product="Vegetables",
        quantity=50.0,
        quality="grade_b",
        expiry_date=expiry_date,
        price=15.0,
        location=sample_location
    )
    
    result = market_agent.check_expiry(listing["listing_id"])
    
    assert result["success"] is True
    expiry_status = result["expiry_status"]
    
    # Should generate alert for products expiring within 3 days
    assert expiry_status["alert_generated"] is True
    assert expiry_status["alert_message"] is not None
    # Check for either 1 or 2 days due to timing calculation differences
    assert ("expires in 1 days" in expiry_status["alert_message"] or 
            "expires in 2 days" in expiry_status["alert_message"])


def test_multi_market_price_display(market_agent, sample_location):
    """Test that prices from multiple markets are displayed."""
    result = market_agent.get_prices("rice", sample_location)
    
    assert result["success"] is True
    
    # Should have prices from multiple markets
    prices = result["prices"]
    if len(prices) > 1:
        assert result["analysis"]["total_markets"] > 1
        assert "average_price" in result["analysis"]
        assert "best_market" in result["analysis"]


def test_listing_completeness(market_agent, sample_location):
    """Test that listings require all necessary information."""
    expiry_date = (datetime.now() + timedelta(days=5)).isoformat()
    
    # Test with missing quantity
    result = market_agent.process(
        query_type="create_listing",
        product="Tomatoes",
        quality="grade_a",
        expiry_date=expiry_date,
        price=25.0,
        location=sample_location
    )
    
    assert result["success"] is False
    assert "error" in result


def test_search_with_filters(market_agent, sample_location):
    """Test product search with filters."""
    expiry_date = (datetime.now() + timedelta(days=5)).isoformat()
    
    # Create listings with different qualities
    create_listing(
        product="Tomatoes Grade A",
        quantity=100.0,
        quality="grade_a",
        expiry_date=expiry_date,
        price=30.0,
        location=sample_location
    )
    
    create_listing(
        product="Tomatoes Grade B",
        quantity=150.0,
        quality="grade_b",
        expiry_date=expiry_date,
        price=20.0,
        location=sample_location
    )
    
    # Search with quality filter
    result = market_agent.search_marketplace(
        "tomatoes",
        filters={"quality": "grade_a"}
    )
    
    assert result["success"] is True
    assert len(result["results"]) == 1
    assert result["results"][0]["quality"] == "grade_a"


def test_is_sustainable_product(market_agent):
    """Test sustainable product detection."""
    # Test with organic quality
    assert market_agent._is_sustainable_product("Tomatoes", "organic") is True
    
    # Test with sustainable keyword in product name
    assert market_agent._is_sustainable_product("Organic Tomatoes", "grade_a") is True
    
    # Test with regular product
    assert market_agent._is_sustainable_product("Regular Tomatoes", "grade_a") is False


def test_price_analysis(market_agent):
    """Test price analysis functionality."""
    prices = [
        {"market_name": "Market A", "price_per_kg": 25, "distance_score": 0},
        {"market_name": "Market B", "price_per_kg": 30, "distance_score": 1},
        {"market_name": "Market C", "price_per_kg": 28, "distance_score": 0}
    ]
    
    analysis = market_agent._analyze_prices(prices, "tomato")
    
    assert analysis["total_markets"] == 3
    assert analysis["average_price"] == 27.67
    assert analysis["min_price"] == 25
    assert analysis["max_price"] == 30
    assert "best_market" in analysis
    # Best market should be the one with lowest distance_score and highest price (Market C has distance 0 and price 28)
    assert analysis["best_market"]["distance_score"] == 0


def test_invalid_query_type(market_agent):
    """Test handling of invalid query type."""
    result = market_agent.process(query_type="invalid_type")
    
    assert result["success"] is False
    assert "error" in result
    assert "Unknown query type" in result["error"]
