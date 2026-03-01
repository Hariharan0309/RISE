"""
Market price tools for MissionAI Farmer Agent.

This module provides tools for market price queries, listing creation,
product search, and expiry tracking.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import uuid
import math
from data_models import MarketListing


# Load market prices from JSON
def load_market_prices() -> List[Dict]:
    """Load market prices from data file."""
    try:
        with open("data/market_prices.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


# In-memory storage for listings (would be database in production)
LISTINGS_STORAGE = []


def get_market_prices(
    crop: str,
    location: Dict[str, str],
    radius_km: int = 100
) -> List[Dict]:
    """
    Get market prices for a crop from nearby markets.
    
    Args:
        crop: Name of the crop
        location: Location dict with district and state
        radius_km: Search radius in kilometers
    
    Returns:
        List of market price dictionaries
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not crop or not isinstance(crop, str):
        raise ValueError("Crop name must be a non-empty string")
    if not location or not isinstance(location, dict):
        raise ValueError("Location must be a dictionary")
    if "district" not in location or "state" not in location:
        raise ValueError("Location must contain 'district' and 'state' fields")
    if radius_km <= 0:
        raise ValueError("Radius must be greater than zero")
    
    crop_lower = crop.lower()
    market_data = load_market_prices()
    
    # Find crop in market data
    crop_markets = None
    for item in market_data:
        if item["crop"].lower() == crop_lower:
            crop_markets = item["markets"]
            break
    
    if not crop_markets:
        return []
    
    # Filter markets by location (simplified - in production would use actual distance)
    # For now, prioritize same state, then nearby states
    user_state = location["state"].lower()
    user_district = location["district"].lower()
    
    results = []
    for market in crop_markets:
        market_state = market["location"]["state"].lower()
        market_district = market["location"]["district"].lower()
        
        # Calculate simple distance score (0 = same district, 1 = same state, 2 = other state)
        if market_district == user_district and market_state == user_state:
            distance_score = 0
        elif market_state == user_state:
            distance_score = 1
        else:
            distance_score = 2
        
        # Include markets within conceptual radius
        if distance_score <= 1:  # Same state
            results.append({
                "market_name": market["name"],
                "location": market["location"],
                "price_per_kg": market.get("price_per_kg", market.get("price_per_unit", 0)),
                "date": market["date"],
                "quality": market["quality"],
                "distance_score": distance_score
            })
    
    # Sort by distance, then by price
    results.sort(key=lambda x: (x["distance_score"], x["price_per_kg"]))
    
    return results


def create_listing(
    product: str,
    quantity: float,
    quality: str,
    expiry_date: str,
    price: float,
    seller_id: str = "default_seller",
    location: Optional[Dict] = None,
    category: str = "produce",
    is_sustainable: bool = False
) -> Dict:
    """
    Create a marketplace listing for produce or inputs.
    
    Args:
        product: Product name
        quantity: Quantity available
        quality: Quality grade (grade_a, grade_b, organic)
        expiry_date: Expiry date (ISO format)
        price: Price per unit
        seller_id: Seller identifier
        location: Location dictionary
        category: Product category
        is_sustainable: Whether product is sustainable/organic
    
    Returns:
        Dictionary with listing details
    
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Input validation
    if not product or not isinstance(product, str):
        raise ValueError("Product name must be a non-empty string")
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")
    if not quality or not isinstance(quality, str):
        raise ValueError("Quality must be a non-empty string")
    if not expiry_date or not isinstance(expiry_date, str):
        raise ValueError("Expiry date must be a non-empty string")
    if price <= 0:
        raise ValueError("Price must be greater than zero")
    
    # Validate expiry date format
    try:
        expiry_dt = datetime.fromisoformat(expiry_date.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("Expiry date must be in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
    
    # Create listing
    listing = MarketListing(
        listing_id=str(uuid.uuid4()),
        type="sell",
        product=product,
        category=category,
        quantity=quantity,
        unit="kg",
        quality=quality,
        price_per_unit=price,
        location=location or {"district": "Unknown", "state": "Unknown"},
        expiry_date=expiry_date,
        is_sustainable=is_sustainable,
        seller_id=seller_id,
        created_at=datetime.now().isoformat(),
        status="active"
    )
    
    # Store listing
    LISTINGS_STORAGE.append(listing.to_dict())
    
    return listing.to_dict()


def search_products(
    product_type: str,
    filters: Optional[Dict] = None
) -> List[Dict]:
    """
    Search marketplace for products.
    
    Args:
        product_type: Type of product to search for
        filters: Optional filters (quality, max_price, location, sustainable_only)
    
    Returns:
        List of matching product listings
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not product_type or not isinstance(product_type, str):
        raise ValueError("Product type must be a non-empty string")
    
    filters = filters or {}
    product_lower = product_type.lower()
    
    # Filter listings
    results = []
    for listing in LISTINGS_STORAGE:
        # Check if product matches
        if product_lower not in listing["product"].lower():
            continue
        
        # Check if listing is active
        if listing["status"] != "active":
            continue
        
        # Apply filters
        if "quality" in filters and listing["quality"] != filters["quality"]:
            continue
        
        if "max_price" in filters and listing["price_per_unit"] > filters["max_price"]:
            continue
        
        if "location" in filters:
            filter_loc = filters["location"]
            listing_loc = listing["location"]
            if "state" in filter_loc and listing_loc.get("state") != filter_loc["state"]:
                continue
        
        if filters.get("sustainable_only", False) and not listing["is_sustainable"]:
            continue
        
        results.append(listing)
    
    # Sort: sustainable first, then by price
    results.sort(key=lambda x: (not x["is_sustainable"], x["price_per_unit"]))
    
    return results


def track_expiry(listing_id: str) -> Dict:
    """
    Track expiry status of a listing and generate alerts.
    
    Args:
        listing_id: Listing identifier
    
    Returns:
        Dictionary with expiry status and alert information
    
    Raises:
        ValueError: If listing not found
    """
    # Input validation
    if not listing_id or not isinstance(listing_id, str):
        raise ValueError("Listing ID must be a non-empty string")
    
    # Find listing
    listing = None
    for item in LISTINGS_STORAGE:
        if item["listing_id"] == listing_id:
            listing = item
            break
    
    if not listing:
        raise ValueError(f"Listing with ID '{listing_id}' not found")
    
    # Parse expiry date
    try:
        expiry_dt = datetime.fromisoformat(listing["expiry_date"].replace("Z", "+00:00"))
    except ValueError:
        return {
            "listing_id": listing_id,
            "error": "Invalid expiry date format",
            "alert_generated": False
        }
    
    # Calculate days until expiry
    now = datetime.now()
    if expiry_dt.tzinfo:
        # Make now timezone-aware if expiry_dt is
        from datetime import timezone
        now = now.replace(tzinfo=timezone.utc)
    
    days_until_expiry = (expiry_dt - now).days
    
    # Generate alert if within 3 days
    alert_generated = days_until_expiry <= 3 and days_until_expiry >= 0
    
    # Determine status
    if days_until_expiry < 0:
        status = "expired"
        alert_message = f"Product has expired {abs(days_until_expiry)} days ago"
    elif days_until_expiry == 0:
        status = "expires_today"
        alert_message = "Product expires today! Urgent action required"
    elif days_until_expiry <= 3:
        status = "expiring_soon"
        alert_message = f"Product expires in {days_until_expiry} days"
    else:
        status = "fresh"
        alert_message = f"Product is fresh, expires in {days_until_expiry} days"
    
    return {
        "listing_id": listing_id,
        "product": listing["product"],
        "expiry_date": listing["expiry_date"],
        "days_until_expiry": days_until_expiry,
        "status": status,
        "alert_generated": alert_generated,
        "alert_message": alert_message if alert_generated or days_until_expiry < 0 else None
    }
