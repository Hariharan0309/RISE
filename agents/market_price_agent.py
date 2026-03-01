"""
Market Price Agent for MissionAI Farmer Agent.

This agent specializes in market price intelligence, produce listing,
product search, and expiry tracking with sustainable product prioritization.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from data_models import MarketListing
from tools.market_tools import (
    get_market_prices,
    create_listing,
    search_products,
    track_expiry
)

logger = logging.getLogger(__name__)


class MarketPriceAgent:
    """
    Specialized agent for market price intelligence and marketplace facilitation.
    
    This agent provides real-time market prices, facilitates produce listings,
    enables product search, tracks expiry dates, and prioritizes sustainable products.
    """
    
    def __init__(self):
        """Initialize the Market Price Agent."""
        self.name = "Market Price Agent"
        self.description = "Specialized in market intelligence and marketplace facilitation"
        self.tools = [
            get_market_prices,
            create_listing,
            search_products,
            track_expiry
        ]
        logger.info(f"{self.name} initialized")
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the Market Price Agent.
        
        Returns:
            str: System prompt defining agent's role and expertise
        """
        return """You are an expert agricultural market analyst specializing in market intelligence and marketplace facilitation.

Your expertise includes:
- Real-time market price analysis and comparison
- Multi-market price intelligence
- Produce listing and marketplace management
- Product search and matching
- Expiry tracking and waste prevention
- Sustainable and organic product promotion

When providing market intelligence:
1. Always show prices from multiple markets for comparison
2. Highlight the best prices and explain price differences
3. Consider transportation costs and market distance
4. Prioritize sustainable and organic products when available
5. Alert farmers about expiring produce to prevent waste
6. Provide clear, actionable recommendations

For produce listings:
1. Ensure all required information is collected (quantity, quality, expiry)
2. Suggest optimal pricing based on market rates
3. Highlight sustainable/organic products prominently
4. Track expiry dates and send timely alerts

For product search:
1. Show sustainable/organic options first
2. Compare prices and quality grades
3. Consider location and availability
4. Provide complete product information

Always prioritize:
- Farmer profitability and fair prices
- Waste reduction through expiry tracking
- Sustainable and organic farming practices
- Transparency in pricing and quality
- Local and regional market connections

Provide advice that is:
- Based on current market data from multiple sources
- Considerate of quality grades and product conditions
- Focused on maximizing farmer income
- Supportive of sustainable agriculture
- Clear about timing (expiry alerts, market trends)

Examples of good advice:
- "Tomatoes are selling at ₹25/kg in Market A and ₹30/kg in Market B. Market B is closer and offers better price"
- "Your produce expires in 2 days. Consider selling at current market rate to avoid waste"
- "Organic certification can increase your price by 20-30%. Consider transitioning to organic farming"
"""
    
    def process(
        self,
        query_type: str,
        location: Optional[Dict[str, str]] = None,
        crop: Optional[str] = None,
        product: Optional[str] = None,
        quantity: Optional[float] = None,
        quality: Optional[str] = None,
        expiry_date: Optional[str] = None,
        price: Optional[float] = None,
        listing_id: Optional[str] = None,
        filters: Optional[Dict] = None,
        radius_km: int = 100
    ) -> Dict[str, Any]:
        """
        Process a market intelligence request.
        
        Args:
            query_type: Type of query ("price_query", "create_listing", "search_products", "track_expiry")
            location: Location dict with district and state
            crop: Crop name for price queries
            product: Product name for listings/search
            quantity: Quantity for listings
            quality: Quality grade for listings
            expiry_date: Expiry date for listings
            price: Price per unit for listings
            listing_id: Listing ID for expiry tracking
            filters: Search filters
            radius_km: Search radius for price queries
            
        Returns:
            dict: Market intelligence result
        """
        logger.info(f"Processing market intelligence request: {query_type}")
        
        try:
            if query_type == "price_query":
                # Get market prices for a crop
                if not crop or not location:
                    return {
                        "success": False,
                        "error": "Crop name and location are required for price queries"
                    }
                
                prices = get_market_prices(crop, location, radius_km)
                
                # Analyze prices and provide recommendations
                analysis = self._analyze_prices(prices, crop)
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "crop": crop,
                    "location": location,
                    "prices": prices,
                    "analysis": analysis,
                    "timestamp": datetime.now().isoformat()
                }
            
            elif query_type == "create_listing":
                # Create a marketplace listing
                if not product or not quantity or not quality or not expiry_date or not price:
                    return {
                        "success": False,
                        "error": "Product, quantity, quality, expiry_date, and price are required for listings"
                    }
                
                # Determine if product is sustainable
                is_sustainable = self._is_sustainable_product(product, quality)
                
                listing = create_listing(
                    product=product,
                    quantity=quantity,
                    quality=quality,
                    expiry_date=expiry_date,
                    price=price,
                    location=location,
                    is_sustainable=is_sustainable
                )
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "listing": listing,
                    "message": "Listing created successfully",
                    "timestamp": datetime.now().isoformat()
                }
            
            elif query_type == "search_products":
                # Search for products in marketplace
                if not product:
                    return {
                        "success": False,
                        "error": "Product name is required for search"
                    }
                
                results = search_products(product, filters)
                
                # Results are already sorted with sustainable products first
                analysis = self._analyze_search_results(results, product)
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "product": product,
                    "results": results,
                    "analysis": analysis,
                    "timestamp": datetime.now().isoformat()
                }
            
            elif query_type == "track_expiry":
                # Track expiry status of a listing
                if not listing_id:
                    return {
                        "success": False,
                        "error": "Listing ID is required for expiry tracking"
                    }
                
                expiry_status = track_expiry(listing_id)
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "expiry_status": expiry_status,
                    "timestamp": datetime.now().isoformat()
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown query type: {query_type}"
                }
        
        except ValueError as e:
            logger.error(f"Validation error in market intelligence: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Invalid input for market intelligence query"
            }
        
        except Exception as e:
            logger.error(f"Error processing market intelligence: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while processing market intelligence request"
            }
    
    def _analyze_prices(self, prices: List[Dict], crop: str) -> Dict[str, Any]:
        """
        Analyze market prices and provide recommendations.
        
        Args:
            prices: List of market price dictionaries
            crop: Crop name
            
        Returns:
            dict: Price analysis and recommendations
        """
        if not prices:
            return {
                "message": f"No market prices found for {crop}",
                "recommendation": "Check back later or try nearby markets"
            }
        
        # Calculate statistics
        price_values = [p["price_per_kg"] for p in prices]
        avg_price = sum(price_values) / len(price_values)
        min_price = min(price_values)
        max_price = max(price_values)
        
        # Find best market
        best_market = min(prices, key=lambda x: (x["distance_score"], -x["price_per_kg"]))
        
        # Generate recommendation
        recommendation = f"Best price: ₹{best_market['price_per_kg']}/kg at {best_market['market_name']}"
        
        if len(prices) > 1:
            recommendation += f". Average market price: ₹{avg_price:.2f}/kg"
        
        return {
            "total_markets": len(prices),
            "average_price": round(avg_price, 2),
            "min_price": min_price,
            "max_price": max_price,
            "best_market": best_market,
            "recommendation": recommendation,
            "price_range": f"₹{min_price}-₹{max_price}/kg"
        }
    
    def _analyze_search_results(self, results: List[Dict], product: str) -> Dict[str, Any]:
        """
        Analyze product search results.
        
        Args:
            results: List of product listings
            product: Product name
            
        Returns:
            dict: Search analysis
        """
        if not results:
            return {
                "message": f"No products found for {product}",
                "recommendation": "Try different search terms or check back later"
            }
        
        # Count sustainable products
        sustainable_count = sum(1 for r in results if r.get("is_sustainable", False))
        
        # Calculate price statistics
        price_values = [r["price_per_unit"] for r in results]
        avg_price = sum(price_values) / len(price_values)
        
        # Find best value (considering sustainability)
        best_value = results[0]  # Already sorted with sustainable first, then by price
        
        analysis = {
            "total_results": len(results),
            "sustainable_products": sustainable_count,
            "average_price": round(avg_price, 2),
            "best_value": {
                "product": best_value["product"],
                "price": best_value["price_per_unit"],
                "quality": best_value["quality"],
                "is_sustainable": best_value.get("is_sustainable", False)
            }
        }
        
        if sustainable_count > 0:
            analysis["recommendation"] = f"Found {sustainable_count} sustainable/organic options. Consider these for better quality and environmental benefits."
        else:
            analysis["recommendation"] = f"Found {len(results)} products. Compare prices and quality before purchasing."
        
        return analysis
    
    def _is_sustainable_product(self, product: str, quality: str) -> bool:
        """
        Determine if a product is sustainable based on product name and quality.
        
        Args:
            product: Product name
            quality: Quality grade
            
        Returns:
            bool: True if product is sustainable/organic
        """
        # Check quality grade
        if quality.lower() in ["organic", "sustainable", "eco-friendly"]:
            return True
        
        # Check product name for sustainability keywords
        sustainable_keywords = ["organic", "sustainable", "eco", "natural", "bio"]
        product_lower = product.lower()
        
        return any(keyword in product_lower for keyword in sustainable_keywords)
    
    def get_prices(self, crop: str, location: Dict[str, str], radius_km: int = 100) -> Dict[str, Any]:
        """
        Get market prices for a crop.
        
        Args:
            crop: Crop name
            location: Location dict with district and state
            radius_km: Search radius in kilometers
            
        Returns:
            dict: Market prices with analysis
        """
        return self.process(
            query_type="price_query",
            crop=crop,
            location=location,
            radius_km=radius_km
        )
    
    def create_produce_listing(
        self,
        product: str,
        quantity: float,
        quality: str,
        expiry_date: str,
        price: float,
        location: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a marketplace listing for produce.
        
        Args:
            product: Product name
            quantity: Quantity available
            quality: Quality grade
            expiry_date: Expiry date (ISO format)
            price: Price per unit
            location: Optional location information
            
        Returns:
            dict: Listing creation result
        """
        return self.process(
            query_type="create_listing",
            product=product,
            quantity=quantity,
            quality=quality,
            expiry_date=expiry_date,
            price=price,
            location=location
        )
    
    def search_marketplace(self, product: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Search marketplace for products.
        
        Args:
            product: Product name to search for
            filters: Optional search filters
            
        Returns:
            dict: Search results with analysis
        """
        return self.process(
            query_type="search_products",
            product=product,
            filters=filters
        )
    
    def check_expiry(self, listing_id: str) -> Dict[str, Any]:
        """
        Check expiry status of a listing.
        
        Args:
            listing_id: Listing identifier
            
        Returns:
            dict: Expiry status with alerts
        """
        return self.process(
            query_type="track_expiry",
            listing_id=listing_id
        )
    
    def get_tools(self):
        """Get list of available tools for this agent."""
        return self.tools
