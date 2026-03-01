"""
Finance Calculator Agent for MissionAI Farmer Agent.

This agent specializes in financial planning, cost estimation, profit calculation,
and comparative crop analysis for farmers.
"""

import logging
from typing import Dict, Any, Optional, List

from tools.financial_tools import (
    calculate_profit,
    estimate_costs,
    compare_crops,
    project_returns
)

logger = logging.getLogger(__name__)


class FinanceCalculatorAgent:
    """
    Specialized agent for financial planning and profitability analysis.
    
    This agent provides profit/loss calculations, cost estimations, crop comparisons,
    and return projections considering market trends and seasonal variations.
    """
    
    def __init__(self):
        """Initialize the Finance Calculator Agent."""
        self.name = "Finance Calculator Agent"
        self.description = "Specialized in financial planning and profitability analysis"
        self.tools = [
            calculate_profit,
            estimate_costs,
            compare_crops,
            project_returns
        ]
        logger.info(f"{self.name} initialized")
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the Finance Calculator Agent.
        
        Returns:
            str: System prompt defining agent's role and expertise
        """
        return """You are an expert agricultural financial advisor specializing in farm economics and profitability analysis.

Your expertise includes:
- Crop profitability and profit/loss calculations
- Comprehensive cost estimation and breakdown
- Comparative financial analysis of crop options
- Return projections with market trend analysis
- Break-even analysis and pricing strategies
- ROI (Return on Investment) calculations
- Seasonal variation impact on finances
- Risk assessment and financial planning

When providing financial advice:
1. Always provide complete cost breakdowns (seeds, fertilizers, pesticides, labor, water, equipment)
2. Calculate realistic profit/loss based on market prices
3. Consider seasonal variations in yield and prices
4. Account for market trends (rising, stable, falling)
5. Provide ROI percentages for easy comparison
6. Calculate break-even prices to guide selling decisions
7. Compare multiple crop options when relevant
8. Explain financial concepts in simple, farmer-friendly language

For profit calculations:
1. Ensure all cost components are included
2. Use realistic yield estimates based on season and location
3. Apply current market prices or farmer-provided prices
4. Show clear profit/loss with ROI percentage
5. Provide break-even price for decision making

For cost estimations:
1. Break down costs by category (seeds, fertilizers, labor, etc.)
2. Scale costs appropriately based on farm area
3. Include both variable and fixed costs
4. Provide cost per acre for easy understanding
5. Suggest areas where costs can be optimized

For crop comparisons:
1. Compare at least 2-3 crop options
2. Show side-by-side financial metrics (cost, revenue, profit, ROI)
3. Consider seasonal suitability
4. Rank crops by profitability
5. Highlight best option with clear reasoning
6. Mention risk factors for each crop

For return projections:
1. Factor in market trends (rising/stable/falling prices)
2. Provide realistic projections, not overly optimistic
3. Assess risk level based on market conditions
4. Show price change impact on profitability
5. Suggest timing for planting and selling

Always prioritize:
- Farmer profitability and income maximization
- Realistic and honest financial projections
- Risk awareness and mitigation strategies
- Sustainable farming practices that improve long-term returns
- Clear, actionable financial recommendations

Provide advice that is:
- Based on accurate calculations and market data
- Easy to understand with simple language
- Practical and implementable
- Considerate of farmer's resources and constraints
- Supportive of informed decision-making

Examples of good advice:
- "For 2 acres of tomatoes, your total cost will be ₹52,000. At ₹30/kg selling price, you can earn ₹2,40,000 revenue with ₹1,88,000 profit (361% ROI)"
- "Comparing onion vs potato: Onion gives 15% higher profit but potato has lower risk. For your 3 acres, onion profit: ₹1,26,000, potato profit: ₹1,09,500"
- "Market trend is falling for wheat. Your break-even price is ₹24/kg. Current market is ₹22/kg. Consider waiting or switching to another crop"
- "Your cultivation cost is ₹28,500 per acre. To break even, you need to sell at minimum ₹18/kg. Current market rate is ₹25/kg, so you have good profit margin"

Remember:
- Farmers need clear numbers to make decisions
- ROI percentage is easier to understand than absolute profit
- Break-even price helps farmers know when to sell
- Comparing crops helps farmers choose the best option
- Market trends significantly impact profitability
- Cost optimization can improve margins substantially
"""
    
    def process(
        self,
        query_type: str,
        crop: Optional[str] = None,
        area: Optional[float] = None,
        selling_price: Optional[float] = None,
        costs: Optional[Dict[str, float]] = None,
        inputs: Optional[Dict[str, float]] = None,
        crop_options: Optional[List[str]] = None,
        season: Optional[str] = None,
        market_trend: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a financial calculation request.
        
        Args:
            query_type: Type of query ("profit", "costs", "compare", "project")
            crop: Crop name
            area: Farm area in acres
            selling_price: Selling price per kg
            costs: Optional cost breakdown
            inputs: Optional input quantities/costs
            crop_options: List of crops for comparison
            season: Growing season (kharif, rabi, summer)
            market_trend: Market trend (rising, stable, falling)
            
        Returns:
            dict: Financial calculation result
        """
        logger.info(f"Processing financial calculation: {query_type}")
        
        try:
            if query_type == "profit":
                # Calculate profit/loss for a crop
                if not crop or not area or not selling_price:
                    return {
                        "success": False,
                        "error": "Crop name, area, and selling price are required for profit calculation"
                    }
                
                result = calculate_profit(
                    crop=crop,
                    area=area,
                    selling_price=selling_price,
                    costs=costs
                )
                
                # Add financial insights
                insights = self._generate_profit_insights(result)
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "calculation": result,
                    "insights": insights
                }
            
            elif query_type == "costs":
                # Estimate cultivation costs
                if not crop or not area:
                    return {
                        "success": False,
                        "error": "Crop name and area are required for cost estimation"
                    }
                
                result = estimate_costs(
                    crop=crop,
                    area=area,
                    inputs=inputs
                )
                
                # Add cost optimization suggestions
                suggestions = self._generate_cost_suggestions(result)
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "estimation": result,
                    "suggestions": suggestions
                }
            
            elif query_type == "compare":
                # Compare multiple crop options
                if not crop_options or not area or not season:
                    return {
                        "success": False,
                        "error": "Crop options, area, and season are required for comparison"
                    }
                
                results = compare_crops(
                    crop_options=crop_options,
                    area=area,
                    season=season
                )
                
                # Add comparative analysis
                analysis = self._generate_comparative_analysis(results, season)
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "comparison": results,
                    "analysis": analysis
                }
            
            elif query_type == "project":
                # Project returns with market trends
                if not crop or not area or not market_trend or not season:
                    return {
                        "success": False,
                        "error": "Crop, area, market trend, and season are required for projection"
                    }
                
                result = project_returns(
                    crop=crop,
                    area=area,
                    market_trend=market_trend,
                    season=season
                )
                
                # Add projection insights
                insights = self._generate_projection_insights(result)
                
                return {
                    "success": True,
                    "query_type": query_type,
                    "projection": result,
                    "insights": insights
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown query type: {query_type}"
                }
        
        except ValueError as e:
            logger.error(f"Validation error in financial calculation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Invalid input for financial calculation"
            }
        
        except Exception as e:
            logger.error(f"Error processing financial calculation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while processing financial calculation"
            }
    
    def _generate_profit_insights(self, calculation: Dict) -> Dict[str, Any]:
        """
        Generate insights from profit calculation.
        
        Args:
            calculation: Profit calculation result
            
        Returns:
            dict: Financial insights and recommendations
        """
        profit_loss = calculation["profit_loss"]
        roi = calculation["roi_percentage"]
        break_even = calculation["break_even_price"]
        selling_price = calculation["revenue"]["price_per_kg"]
        
        insights = {
            "profitability": "profitable" if profit_loss > 0 else "loss-making",
            "roi_assessment": self._assess_roi(roi),
            "price_margin": round(selling_price - break_even, 2),
            "recommendations": []
        }
        
        # Generate recommendations
        if profit_loss > 0:
            if roi > 100:
                insights["recommendations"].append(
                    f"Excellent returns! ROI of {roi}% is very good for this crop."
                )
            elif roi > 50:
                insights["recommendations"].append(
                    f"Good returns with {roi}% ROI. This is a profitable choice."
                )
            else:
                insights["recommendations"].append(
                    f"Moderate returns with {roi}% ROI. Consider cost optimization."
                )
        else:
            insights["recommendations"].append(
                f"Current price of ₹{selling_price}/kg results in loss. "
                f"Break-even price is ₹{break_even}/kg. Wait for better prices or reduce costs."
            )
        
        # Price margin analysis
        if selling_price > break_even:
            margin_percent = ((selling_price - break_even) / break_even) * 100
            insights["recommendations"].append(
                f"You have ₹{insights['price_margin']}/kg margin above break-even ({margin_percent:.1f}%). "
                "Good buffer for price fluctuations."
            )
        
        return insights
    
    def _generate_cost_suggestions(self, estimation: Dict) -> List[str]:
        """
        Generate cost optimization suggestions.
        
        Args:
            estimation: Cost estimation result
            
        Returns:
            list: Cost optimization suggestions
        """
        costs = estimation["costs"]
        total = costs["total"]
        suggestions = []
        
        # Analyze cost components
        cost_percentages = {
            key: (value / total * 100) if total > 0 else 0
            for key, value in costs.items()
            if key != "total"
        }
        
        # Find highest cost components
        sorted_costs = sorted(cost_percentages.items(), key=lambda x: x[1], reverse=True)
        
        # Suggestions based on cost breakdown
        for component, percentage in sorted_costs[:3]:
            if component == "labor" and percentage > 30:
                suggestions.append(
                    f"Labor costs are {percentage:.1f}% of total. "
                    "Consider mechanization or efficient labor management."
                )
            elif component == "fertilizers" and percentage > 25:
                suggestions.append(
                    f"Fertilizer costs are {percentage:.1f}% of total. "
                    "Consider organic alternatives or soil testing for optimal usage."
                )
            elif component == "pesticides" and percentage > 20:
                suggestions.append(
                    f"Pesticide costs are {percentage:.1f}% of total. "
                    "Consider integrated pest management (IPM) to reduce chemical usage."
                )
            elif component == "seeds" and percentage > 20:
                suggestions.append(
                    f"Seed costs are {percentage:.1f}% of total. "
                    "Consider using farm-saved seeds or bulk purchasing for better rates."
                )
        
        # General suggestions
        suggestions.append(
            "Check government schemes for subsidies on inputs to reduce costs."
        )
        
        return suggestions
    
    def _generate_comparative_analysis(self, comparison: List[Dict], season: str) -> Dict[str, Any]:
        """
        Generate comparative analysis of crop options.
        
        Args:
            comparison: List of crop comparison results
            season: Growing season
            
        Returns:
            dict: Comparative analysis
        """
        if not comparison:
            return {
                "message": "No crops available for comparison",
                "recommendation": "Please provide valid crop options"
            }
        
        # Best crop by profit
        best_profit = comparison[0]  # Already sorted by profit
        
        # Best crop by ROI
        best_roi = max(comparison, key=lambda x: x["roi_percentage"])
        
        # Lowest risk (highest ROI with reasonable profit)
        balanced = [c for c in comparison if c["roi_percentage"] > 50 and c["estimated_profit"] > 0]
        best_balanced = balanced[0] if balanced else comparison[0]
        
        analysis = {
            "total_crops_compared": len(comparison),
            "season": season,
            "best_by_profit": {
                "crop": best_profit["crop"],
                "profit": best_profit["estimated_profit"],
                "roi": best_profit["roi_percentage"]
            },
            "best_by_roi": {
                "crop": best_roi["crop"],
                "profit": best_roi["estimated_profit"],
                "roi": best_roi["roi_percentage"]
            },
            "recommended": {
                "crop": best_balanced["crop"],
                "profit": best_balanced["estimated_profit"],
                "roi": best_balanced["roi_percentage"],
                "reason": "Best balance of profit and ROI"
            }
        }
        
        # Generate recommendation
        if best_profit["crop"] == best_roi["crop"]:
            analysis["recommendation"] = (
                f"{best_profit['crop']} is the clear winner with highest profit "
                f"(₹{best_profit['estimated_profit']}) and ROI ({best_profit['roi_percentage']}%)."
            )
        else:
            analysis["recommendation"] = (
                f"{best_profit['crop']} gives highest profit (₹{best_profit['estimated_profit']}), "
                f"while {best_roi['crop']} has best ROI ({best_roi['roi_percentage']}%). "
                f"Recommend {best_balanced['crop']} for balanced returns."
            )
        
        return analysis
    
    def _generate_projection_insights(self, projection: Dict) -> Dict[str, Any]:
        """
        Generate insights from return projection.
        
        Args:
            projection: Return projection result
            
        Returns:
            dict: Projection insights
        """
        market_trend = projection["market_trend"]
        risk_level = projection["risk_level"]
        roi = projection["roi_percentage"]
        price_change = projection["price_change_percentage"]
        
        insights = {
            "market_outlook": self._assess_market_trend(market_trend),
            "risk_assessment": self._assess_risk(risk_level),
            "recommendations": []
        }
        
        # Trend-based recommendations
        if market_trend.lower() == "rising":
            insights["recommendations"].append(
                f"Market prices are rising (+{price_change}%). Good time to plant this crop. "
                f"Expected ROI: {roi}%."
            )
        elif market_trend.lower() == "stable":
            insights["recommendations"].append(
                f"Market prices are stable. Reliable returns expected with {roi}% ROI. "
                "Low risk option."
            )
        else:  # falling
            insights["recommendations"].append(
                f"Market prices are falling ({price_change}%). Higher risk with {roi}% ROI. "
                "Consider alternative crops or wait for market recovery."
            )
        
        # Risk-based recommendations
        if risk_level == "high":
            insights["recommendations"].append(
                "High risk due to market conditions. Ensure you have buffer funds and "
                "consider crop insurance."
            )
        elif risk_level == "medium":
            insights["recommendations"].append(
                "Moderate risk. Monitor market prices regularly and be prepared to "
                "adjust selling strategy."
            )
        else:  # low
            insights["recommendations"].append(
                "Low risk with stable market conditions. Good choice for reliable income."
            )
        
        return insights
    
    def _assess_roi(self, roi: float) -> str:
        """Assess ROI level."""
        if roi > 100:
            return "excellent"
        elif roi > 50:
            return "good"
        elif roi > 20:
            return "moderate"
        elif roi > 0:
            return "low"
        else:
            return "negative"
    
    def _assess_market_trend(self, trend: str) -> str:
        """Assess market trend outlook."""
        trend_lower = trend.lower()
        if trend_lower == "rising":
            return "positive"
        elif trend_lower == "stable":
            return "neutral"
        else:
            return "negative"
    
    def _assess_risk(self, risk_level: str) -> str:
        """Assess risk level."""
        risk_map = {
            "low": "Low risk - stable market conditions",
            "medium": "Moderate risk - monitor market closely",
            "high": "High risk - consider alternatives or insurance"
        }
        return risk_map.get(risk_level.lower(), "Unknown risk level")
    
    def calculate_crop_profit(
        self,
        crop: str,
        area: float,
        selling_price: float,
        costs: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate profit/loss for a crop.
        
        Args:
            crop: Crop name
            area: Farm area in acres
            selling_price: Selling price per kg
            costs: Optional cost breakdown
            
        Returns:
            dict: Profit calculation with insights
        """
        return self.process(
            query_type="profit",
            crop=crop,
            area=area,
            selling_price=selling_price,
            costs=costs
        )
    
    def estimate_cultivation_costs(
        self,
        crop: str,
        area: float,
        inputs: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Estimate cultivation costs for a crop.
        
        Args:
            crop: Crop name
            area: Farm area in acres
            inputs: Optional input quantities/costs
            
        Returns:
            dict: Cost estimation with suggestions
        """
        return self.process(
            query_type="costs",
            crop=crop,
            area=area,
            inputs=inputs
        )
    
    def compare_crop_options(
        self,
        crop_options: List[str],
        area: float,
        season: str
    ) -> Dict[str, Any]:
        """
        Compare multiple crop options financially.
        
        Args:
            crop_options: List of crop names
            area: Farm area in acres
            season: Growing season (kharif, rabi, summer)
            
        Returns:
            dict: Crop comparison with analysis
        """
        return self.process(
            query_type="compare",
            crop_options=crop_options,
            area=area,
            season=season
        )
    
    def project_crop_returns(
        self,
        crop: str,
        area: float,
        market_trend: str,
        season: str
    ) -> Dict[str, Any]:
        """
        Project returns for a crop considering market trends.
        
        Args:
            crop: Crop name
            area: Farm area in acres
            market_trend: Market trend (rising, stable, falling)
            season: Growing season (kharif, rabi, summer)
            
        Returns:
            dict: Return projection with insights
        """
        return self.process(
            query_type="project",
            crop=crop,
            area=area,
            market_trend=market_trend,
            season=season
        )
    
    def get_tools(self):
        """Get list of available tools for this agent."""
        return self.tools
