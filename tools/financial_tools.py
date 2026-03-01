"""
Financial calculator tools for MissionAI Farmer Agent.

This module provides tools for financial planning, cost estimation,
profit calculation, and crop comparison.
"""

from typing import Dict, List, Optional
from datetime import datetime
import uuid
from data_models import FinancialCalculation, Costs, Revenue


# Mock crop cost data (per acre)
CROP_COST_DATABASE = {
    "tomato": {"seeds": 3000, "fertilizers": 5000, "pesticides": 3500, "labor": 8000, "water": 2000, "equipment": 1500},
    "onion": {"seeds": 2500, "fertilizers": 4000, "pesticides": 2500, "labor": 6000, "water": 1500, "equipment": 1000},
    "potato": {"seeds": 8000, "fertilizers": 6000, "pesticides": 3000, "labor": 7000, "water": 2500, "equipment": 2000},
    "rice": {"seeds": 2000, "fertilizers": 5000, "pesticides": 2000, "labor": 10000, "water": 3000, "equipment": 3000},
    "wheat": {"seeds": 1500, "fertilizers": 4500, "pesticides": 1500, "labor": 8000, "water": 2000, "equipment": 2500},
    "sugarcane": {"seeds": 15000, "fertilizers": 8000, "pesticides": 4000, "labor": 12000, "water": 5000, "equipment": 5000},
    "cotton": {"seeds": 3500, "fertilizers": 6000, "pesticides": 5000, "labor": 9000, "water": 2500, "equipment": 2000},
    "chilli": {"seeds": 4000, "fertilizers": 5500, "pesticides": 4500, "labor": 8500, "water": 2000, "equipment": 1500},
    "groundnut": {"seeds": 5000, "fertilizers": 4000, "pesticides": 2500, "labor": 7000, "water": 1500, "equipment": 1500},
    "coffee": {"seeds": 10000, "fertilizers": 7000, "pesticides": 3000, "labor": 15000, "water": 4000, "equipment": 3000},
}

# Mock yield data (kg per acre)
CROP_YIELD_DATABASE = {
    "tomato": {"kharif": 8000, "rabi": 9000, "summer": 7000},
    "onion": {"kharif": 6000, "rabi": 7000, "summer": 5500},
    "potato": {"kharif": 7000, "rabi": 8000, "summer": 6500},
    "rice": {"kharif": 2500, "rabi": 2000, "summer": 1800},
    "wheat": {"kharif": 1500, "rabi": 2000, "summer": 1200},
    "sugarcane": {"kharif": 35000, "rabi": 32000, "summer": 30000},
    "cotton": {"kharif": 800, "rabi": 700, "summer": 600},
    "chilli": {"kharif": 1500, "rabi": 1800, "summer": 1400},
    "groundnut": {"kharif": 1200, "rabi": 1400, "summer": 1100},
    "coffee": {"kharif": 600, "rabi": 650, "summer": 550},
}


def calculate_profit(
    crop: str,
    area: float,
    selling_price: float,
    costs: Optional[Dict[str, float]] = None
) -> Dict:
    """
    Calculate profit or loss for a crop.
    
    Args:
        crop: Name of the crop
        area: Farm area in acres
        selling_price: Selling price per kg
        costs: Optional cost breakdown dict. If not provided, uses database estimates.
    
    Returns:
        Dictionary with financial calculation details
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not crop or not isinstance(crop, str):
        raise ValueError("Crop name must be a non-empty string")
    if area <= 0:
        raise ValueError("Area must be greater than zero")
    if selling_price <= 0:
        raise ValueError("Selling price must be greater than zero")
    
    crop_lower = crop.lower()
    
    # Get or calculate costs
    if costs is None:
        if crop_lower not in CROP_COST_DATABASE:
            raise ValueError(f"Crop '{crop}' not found in database. Please provide cost breakdown.")
        cost_per_acre = CROP_COST_DATABASE[crop_lower]
        costs = {
            "seeds": cost_per_acre["seeds"] * area,
            "fertilizers": cost_per_acre["fertilizers"] * area,
            "pesticides": cost_per_acre["pesticides"] * area,
            "labor": cost_per_acre["labor"] * area,
            "water": cost_per_acre["water"] * area,
            "equipment": cost_per_acre["equipment"] * area,
            "other": 0.0
        }
    else:
        # Validate provided costs
        required_fields = ["seeds", "fertilizers", "pesticides", "labor", "water", "equipment"]
        for field in required_fields:
            if field not in costs:
                raise ValueError(f"Missing required cost field: {field}")
            if costs[field] < 0:
                raise ValueError(f"Cost for {field} cannot be negative")
        if "other" not in costs:
            costs["other"] = 0.0
    
    # Calculate total costs
    total_costs = sum(costs.values())
    costs["total"] = total_costs
    
    # Estimate yield (use average of seasons if crop in database)
    if crop_lower in CROP_YIELD_DATABASE:
        yields = CROP_YIELD_DATABASE[crop_lower]
        avg_yield_per_acre = sum(yields.values()) / len(yields)
        expected_yield = avg_yield_per_acre * area
    else:
        # Default estimate if crop not in database
        expected_yield = 5000 * area
    
    # Calculate revenue
    total_revenue = expected_yield * selling_price
    
    # Calculate profit/loss
    profit_loss = total_revenue - total_costs
    
    # Calculate ROI
    roi_percentage = (profit_loss / total_costs * 100) if total_costs > 0 else 0.0
    
    # Calculate break-even price
    break_even_price = total_costs / expected_yield if expected_yield > 0 else 0.0
    
    # Create result
    costs_obj = Costs(**costs)
    revenue_obj = Revenue(
        expected_yield_kg=expected_yield,
        price_per_kg=selling_price,
        total=total_revenue
    )
    
    result = FinancialCalculation(
        calculation_id=str(uuid.uuid4()),
        crop=crop,
        area_acres=area,
        costs=costs_obj,
        revenue=revenue_obj,
        profit_loss=profit_loss,
        roi_percentage=round(roi_percentage, 2),
        break_even_price=round(break_even_price, 2),
        timestamp=datetime.now().isoformat()
    )
    
    return result.to_dict()


def estimate_costs(
    crop: str,
    area: float,
    inputs: Optional[Dict[str, float]] = None
) -> Dict:
    """
    Estimate cultivation costs for a crop.
    
    Args:
        crop: Name of the crop
        area: Farm area in acres
        inputs: Optional input quantities/costs override
    
    Returns:
        Dictionary with cost breakdown
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not crop or not isinstance(crop, str):
        raise ValueError("Crop name must be a non-empty string")
    if area <= 0:
        raise ValueError("Area must be greater than zero")
    
    crop_lower = crop.lower()
    
    # Get base costs from database
    if crop_lower not in CROP_COST_DATABASE:
        raise ValueError(f"Crop '{crop}' not found in cost database")
    
    cost_per_acre = CROP_COST_DATABASE[crop_lower]
    
    # Calculate costs
    costs = {
        "seeds": cost_per_acre["seeds"] * area,
        "fertilizers": cost_per_acre["fertilizers"] * area,
        "pesticides": cost_per_acre["pesticides"] * area,
        "labor": cost_per_acre["labor"] * area,
        "water": cost_per_acre["water"] * area,
        "equipment": cost_per_acre["equipment"] * area,
        "other": 0.0
    }
    
    # Apply input overrides if provided
    if inputs:
        for key, value in inputs.items():
            if key in costs:
                if value < 0:
                    raise ValueError(f"Cost for {key} cannot be negative")
                costs[key] = value
    
    costs["total"] = sum(costs.values())
    
    return {
        "crop": crop,
        "area_acres": area,
        "costs": costs,
        "cost_per_acre": costs["total"] / area if area > 0 else 0.0
    }


def compare_crops(
    crop_options: List[str],
    area: float,
    season: str
) -> List[Dict]:
    """
    Compare multiple crop options financially.
    
    Args:
        crop_options: List of crop names to compare
        area: Farm area in acres
        season: Growing season (kharif, rabi, summer)
    
    Returns:
        List of dictionaries with comparison data for each crop
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not crop_options or not isinstance(crop_options, list):
        raise ValueError("Crop options must be a non-empty list")
    if len(crop_options) < 2:
        raise ValueError("At least two crops required for comparison")
    if area <= 0:
        raise ValueError("Area must be greater than zero")
    if season.lower() not in ["kharif", "rabi", "summer"]:
        raise ValueError("Season must be one of: kharif, rabi, summer")
    
    season_lower = season.lower()
    results = []
    
    for crop in crop_options:
        crop_lower = crop.lower()
        
        # Skip crops not in database
        if crop_lower not in CROP_COST_DATABASE or crop_lower not in CROP_YIELD_DATABASE:
            continue
        
        # Get costs
        cost_per_acre = CROP_COST_DATABASE[crop_lower]
        total_cost = sum(cost_per_acre.values()) * area
        
        # Get yield for season
        yield_data = CROP_YIELD_DATABASE[crop_lower]
        yield_per_acre = yield_data.get(season_lower, sum(yield_data.values()) / len(yield_data))
        expected_yield = yield_per_acre * area
        
        # Estimate market price (mock data - would come from market API)
        mock_prices = {
            "tomato": 30, "onion": 22, "potato": 19, "rice": 28,
            "wheat": 24, "sugarcane": 3.2, "cotton": 62, "chilli": 185,
            "groundnut": 58, "coffee": 285
        }
        estimated_price = mock_prices.get(crop_lower, 25)
        
        # Calculate revenue and profit
        revenue = expected_yield * estimated_price
        profit = revenue - total_cost
        roi = (profit / total_cost * 100) if total_cost > 0 else 0.0
        
        results.append({
            "crop": crop,
            "season": season,
            "area_acres": area,
            "total_cost": round(total_cost, 2),
            "expected_yield_kg": round(expected_yield, 2),
            "estimated_price_per_kg": estimated_price,
            "estimated_revenue": round(revenue, 2),
            "estimated_profit": round(profit, 2),
            "roi_percentage": round(roi, 2),
            "cost_per_acre": round(total_cost / area, 2)
        })
    
    # Sort by profit (descending)
    results.sort(key=lambda x: x["estimated_profit"], reverse=True)
    
    return results


def project_returns(
    crop: str,
    area: float,
    market_trend: str,
    season: str
) -> Dict:
    """
    Project returns for a crop considering market trends.
    
    Args:
        crop: Name of the crop
        area: Farm area in acres
        market_trend: Market trend (rising, stable, falling)
        season: Growing season (kharif, rabi, summer)
    
    Returns:
        Dictionary with projected returns
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not crop or not isinstance(crop, str):
        raise ValueError("Crop name must be a non-empty string")
    if area <= 0:
        raise ValueError("Area must be greater than zero")
    if market_trend.lower() not in ["rising", "stable", "falling"]:
        raise ValueError("Market trend must be one of: rising, stable, falling")
    if season.lower() not in ["kharif", "rabi", "summer"]:
        raise ValueError("Season must be one of: kharif, rabi, summer")
    
    crop_lower = crop.lower()
    season_lower = season.lower()
    trend_lower = market_trend.lower()
    
    # Get base data
    if crop_lower not in CROP_COST_DATABASE or crop_lower not in CROP_YIELD_DATABASE:
        raise ValueError(f"Crop '{crop}' not found in database")
    
    # Calculate costs
    cost_per_acre = CROP_COST_DATABASE[crop_lower]
    total_cost = sum(cost_per_acre.values()) * area
    
    # Get yield
    yield_data = CROP_YIELD_DATABASE[crop_lower]
    yield_per_acre = yield_data.get(season_lower, sum(yield_data.values()) / len(yield_data))
    expected_yield = yield_per_acre * area
    
    # Base price (mock)
    mock_prices = {
        "tomato": 30, "onion": 22, "potato": 19, "rice": 28,
        "wheat": 24, "sugarcane": 3.2, "cotton": 62, "chilli": 185,
        "groundnut": 58, "coffee": 285
    }
    base_price = mock_prices.get(crop_lower, 25)
    
    # Adjust price based on trend
    price_adjustments = {
        "rising": 1.15,    # 15% increase
        "stable": 1.0,     # No change
        "falling": 0.85    # 15% decrease
    }
    projected_price = base_price * price_adjustments[trend_lower]
    
    # Calculate projections
    projected_revenue = expected_yield * projected_price
    projected_profit = projected_revenue - total_cost
    roi = (projected_profit / total_cost * 100) if total_cost > 0 else 0.0
    
    # Risk assessment
    risk_level = "low" if trend_lower == "rising" else "medium" if trend_lower == "stable" else "high"
    
    return {
        "crop": crop,
        "area_acres": area,
        "season": season,
        "market_trend": market_trend,
        "total_cost": round(total_cost, 2),
        "expected_yield_kg": round(expected_yield, 2),
        "base_price_per_kg": base_price,
        "projected_price_per_kg": round(projected_price, 2),
        "projected_revenue": round(projected_revenue, 2),
        "projected_profit": round(projected_profit, 2),
        "roi_percentage": round(roi, 2),
        "risk_level": risk_level,
        "price_change_percentage": round((price_adjustments[trend_lower] - 1) * 100, 2)
    }
