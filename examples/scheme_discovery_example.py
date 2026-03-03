"""
RISE Scheme Discovery Tools - Example Usage
Demonstrates how to use scheme discovery tools for profile analysis, eligibility checking, and recommendations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

from scheme_discovery_tools import (
    SchemeDiscoveryTools,
    recommend_schemes_tool,
    check_eligibility_tool
)
import json


def example_analyze_farmer_profile():
    """Example: Analyze farmer profile using AI"""
    print("=" * 60)
    print("Example 1: Analyze Farmer Profile")
    print("=" * 60)
    
    tools = SchemeDiscoveryTools(region='us-east-1')
    
    # Create sample farmer profile
    farmer_profile = {
        'name': 'Ravi Kumar',
        'location': {
            'state': 'uttar pradesh',
            'district': 'lucknow'
        },
        'farm_details': {
            'land_size': 2.0,
            'soil_type': 'loamy',
            'crops': ['wheat', 'rice'],
            'farming_experience': '10 years',
            'land_ownership': True
        },
        'annual_income': 150000
    }
    
    print("\nAnalyzing farmer profile...")
    print(f"Farmer: {farmer_profile['name']}")
    print(f"Location: {farmer_profile['location']['district'].title()}, {farmer_profile['location']['state'].title()}")
    print(f"Land Size: {farmer_profile['farm_details']['land_size']} acres")
    print(f"Crops: {', '.join(farmer_profile['farm_details']['crops'])}")
    
    result = tools.analyze_farmer_profile(farmer_profile)
    
    if result['success']:
        print("\n✓ Profile analysis completed!")
        
        analysis = result['analysis']
        profile_summary = result['profile_summary']
        
        print(f"\nFarmer Category: {profile_summary['farmer_category'].title()}")
        print(f"Profile Completeness: {analysis.get('profile_completeness', 0)*100:.0f}%")
        
        print("\nRelevant Scheme Categories:")
        for category in analysis.get('relevant_categories', []):
            print(f"  • {category.replace('_', ' ').title()}")
        
        print("\nIdentified Needs:")
        for need in analysis.get('farmer_needs', []):
            print(f"  • {need}")
        
        print("\nPriority Areas:")
        for area in analysis.get('priority_areas', []):
            print(f"  • {area}")
        
        print(f"\nEstimated Benefits: {analysis.get('estimated_benefits', 'Moderate')}")
    else:
        print(f"✗ Error: {result['error']}")


def example_check_eligibility():
    """Example: Check eligibility for a specific scheme"""
    print("\n" + "=" * 60)
    print("Example 2: Check Scheme Eligibility")
    print("=" * 60)
    
    tools = SchemeDiscoveryTools(region='us-east-1')
    
    # Create sample farmer profile
    farmer_profile = {
        'name': 'Lakshmi Devi',
        'location': {
            'state': 'karnataka',
            'district': 'bangalore'
        },
        'farm_details': {
            'land_size': 1.5,
            'soil_type': 'red',
            'crops': ['ragi', 'vegetables'],
            'farming_experience': '15 years',
            'land_ownership': True
        },
        'annual_income': 120000
    }
    
    # First, get some schemes to check
    from government_scheme_tools import GovernmentSchemeTools
    scheme_tools = GovernmentSchemeTools(region='us-east-1')
    
    # Scrape schemes if needed
    print("\nEnsuring schemes are available...")
    scrape_result = scheme_tools.scrape_government_schemes('all')
    
    if scrape_result['success']:
        print(f"✓ {scrape_result['ingested_count']} schemes available")
        
        # Search for a scheme
        search_result = scheme_tools.search_schemes(category='subsidies', active_only=True)
        
        if search_result['success'] and search_result['count'] > 0:
            scheme = search_result['schemes'][0]
            scheme_id = scheme['scheme_id']
            
            print(f"\nChecking eligibility for: {scheme['scheme_name']}")
            print(f"Scheme ID: {scheme_id}")
            
            result = tools.check_eligibility(farmer_profile, scheme_id)
            
            if result['success']:
                print(f"\n{'='*50}")
                print(f"Eligibility Result: {'✅ ELIGIBLE' if result['eligible'] else '❌ NOT ELIGIBLE'}")
                print(f"{'='*50}")
                print(f"Confidence Score: {result['confidence_score']*100:.0f}%")
                
                print("\nReasons:")
                for reason in result['reasons']:
                    print(f"  • {reason}")
                
                if result['eligible']:
                    print("\nRequired Documents:")
                    for doc in result['required_documents']:
                        print(f"  • {doc}")
                    
                    if result.get('missing_requirements'):
                        print("\n⚠️ Missing Requirements:")
                        for req in result['missing_requirements']:
                            print(f"  • {req}")
                    
                    print("\nNext Steps:")
                    for i, step in enumerate(result['next_steps'], 1):
                        print(f"  {i}. {step}")
            else:
                print(f"✗ Error: {result['error']}")


def example_recommend_schemes():
    """Example: Get personalized scheme recommendations"""
    print("\n" + "=" * 60)
    print("Example 3: Get Scheme Recommendations")
    print("=" * 60)
    
    tools = SchemeDiscoveryTools(region='us-east-1')
    
    # Create sample farmer profile
    farmer_profile = {
        'name': 'Arjun Singh',
        'location': {
            'state': 'punjab',
            'district': 'ludhiana'
        },
        'farm_details': {
            'land_size': 3.5,
            'soil_type': 'alluvial',
            'crops': ['wheat', 'rice', 'cotton'],
            'farming_experience': '8 years',
            'land_ownership': True
        },
        'annual_income': 250000
    }
    
    print("\nGetting scheme recommendations...")
    print(f"Farmer: {farmer_profile['name']}")
    print(f"Location: {farmer_profile['location']['district'].title()}, {farmer_profile['location']['state'].title()}")
    print(f"Land Size: {farmer_profile['farm_details']['land_size']} acres")
    
    result = tools.recommend_schemes(farmer_profile)
    
    if result['success']:
        print(f"\n✓ Found {result['count']} applicable schemes!")
        
        summary = result['recommendation_summary']
        print(f"\nRecommendation Summary:")
        print(f"  High Priority: {summary['high_priority']}")
        print(f"  Medium Priority: {summary['medium_priority']}")
        print(f"  Low Priority: {summary['low_priority']}")
        print(f"  Total Potential Benefit: ₹{result['total_potential_benefit']:,.0f}")
        
        print("\n" + "="*60)
        print("Top Recommended Schemes:")
        print("="*60)
        
        for i, scheme in enumerate(result['schemes'][:5], 1):
            print(f"\n{i}. {scheme['scheme_name']}")
            print(f"   Priority: {scheme['priority_level'].upper()} ({scheme['priority_score']:.1f}/100)")
            print(f"   Category: {scheme['category'].replace('_', ' ').title()}")
            print(f"   Estimated Benefit: ₹{scheme.get('estimated_benefit', 0):,.0f}")
            
            if scheme.get('days_to_deadline'):
                days = scheme['days_to_deadline']
                if days <= 30:
                    print(f"   ⏰ URGENT: {days} days remaining!")
                else:
                    print(f"   ⏰ Deadline: {days} days remaining")
            else:
                print(f"   📅 No deadline - Ongoing scheme")
            
            print(f"   Documents: {', '.join(scheme['required_documents'][:3])}")
    else:
        print(f"✗ Error: {result['error']}")


def example_calculate_benefits():
    """Example: Calculate benefit amounts for schemes"""
    print("\n" + "=" * 60)
    print("Example 4: Calculate Benefit Amounts")
    print("=" * 60)
    
    tools = SchemeDiscoveryTools(region='us-east-1')
    
    # Create sample farmer profile
    farmer_profile = {
        'name': 'Meena Patel',
        'location': {
            'state': 'gujarat',
            'district': 'ahmedabad'
        },
        'farm_details': {
            'land_size': 5.0,
            'soil_type': 'black',
            'crops': ['cotton', 'groundnut'],
            'farming_experience': '12 years',
            'land_ownership': True
        },
        'annual_income': 300000
    }
    
    # Get schemes first
    from government_scheme_tools import GovernmentSchemeTools
    scheme_tools = GovernmentSchemeTools(region='us-east-1')
    
    search_result = scheme_tools.search_schemes(active_only=True)
    
    if search_result['success'] and search_result['count'] > 0:
        print("\nCalculating benefits for available schemes...")
        
        for scheme in search_result['schemes'][:3]:
            scheme_id = scheme['scheme_id']
            
            result = tools.calculate_benefit_amount(farmer_profile, scheme_id)
            
            if result['success']:
                print(f"\n{'='*50}")
                print(f"Scheme: {result['scheme_name']}")
                print(f"{'='*50}")
                print(f"Base Benefit: ₹{result['base_benefit']:,.0f}")
                print(f"Estimated Benefit: ₹{result['estimated_benefit']:,.0f}")
                print(f"Recurring: {'Yes (Annual)' if result['is_recurring'] else 'No (One-time)'}")
                print(f"5-Year Total: ₹{result['total_5year_benefit']:,.0f}")
                
                factors = result['calculation_factors']
                print(f"\nCalculation Factors:")
                print(f"  Land Size: {factors['land_size']} acres")
                print(f"  Farmer Category: {factors['farmer_category'].title()}")
                print(f"  Scheme Category: {factors['scheme_category'].replace('_', ' ').title()}")


def example_prioritize_schemes():
    """Example: Prioritize schemes by deadline and benefit"""
    print("\n" + "=" * 60)
    print("Example 5: Prioritize Schemes")
    print("=" * 60)
    
    tools = SchemeDiscoveryTools(region='us-east-1')
    
    # Get schemes first
    from government_scheme_tools import GovernmentSchemeTools
    scheme_tools = GovernmentSchemeTools(region='us-east-1')
    
    search_result = scheme_tools.search_schemes(active_only=True)
    
    if search_result['success'] and search_result['count'] > 0:
        schemes = search_result['schemes']
        
        print(f"\nPrioritizing {len(schemes)} schemes...")
        
        result = tools.prioritize_schemes(schemes)
        
        if result['success']:
            print(f"\n✓ Prioritization completed!")
            
            summary = result['prioritization_summary']
            print(f"\nPrioritization Summary:")
            print(f"  Total Schemes: {summary['total_schemes']}")
            print(f"  High Priority: {summary['high_priority']}")
            print(f"  Urgent Deadlines: {summary['urgent_deadlines']}")
            print(f"  Total Potential Benefit: ₹{result['total_benefit']:,.0f}")
            
            print("\n" + "="*60)
            print("Prioritized Schemes (Top 5):")
            print("="*60)
            
            for i, scheme in enumerate(result['schemes'][:5], 1):
                print(f"\n{i}. {scheme['scheme_name']}")
                print(f"   Priority Score: {scheme['priority_score']:.1f}/100")
                print(f"   Priority Level: {scheme['priority_level'].upper()}")
                print(f"   Benefit: ₹{scheme.get('benefit_amount', 0):,.0f}")
                
                if scheme.get('days_to_deadline'):
                    print(f"   Days to Deadline: {scheme['days_to_deadline']}")
                else:
                    print(f"   Deadline: Ongoing")


def example_tool_functions():
    """Example: Using tool functions for agent integration"""
    print("\n" + "=" * 60)
    print("Example 6: Tool Functions for Agent Integration")
    print("=" * 60)
    
    # Create sample farmer profile
    farmer_profile = {
        'name': 'Suresh Reddy',
        'location': {
            'state': 'andhra pradesh',
            'district': 'guntur'
        },
        'farm_details': {
            'land_size': 4.0,
            'soil_type': 'clay',
            'crops': ['rice', 'chili'],
            'farming_experience': '20 years',
            'land_ownership': True
        },
        'annual_income': 200000
    }
    
    # Recommend schemes tool
    print("\n1. Using recommend_schemes_tool:")
    result = recommend_schemes_tool(farmer_profile)
    print(result[:800] + "...")  # Print first 800 chars
    
    # Check eligibility tool
    print("\n2. Using check_eligibility_tool:")
    from government_scheme_tools import GovernmentSchemeTools
    scheme_tools = GovernmentSchemeTools(region='us-east-1')
    
    search_result = scheme_tools.search_schemes(active_only=True)
    if search_result['success'] and search_result['count'] > 0:
        scheme_id = search_result['schemes'][0]['scheme_id']
        result = check_eligibility_tool(farmer_profile, scheme_id)
        print(result[:500] + "...")  # Print first 500 chars


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("RISE Scheme Discovery Tools - Example Usage")
    print("=" * 60)
    
    try:
        # Run examples
        example_analyze_farmer_profile()
        example_check_eligibility()
        example_recommend_schemes()
        example_calculate_benefits()
        example_prioritize_schemes()
        example_tool_functions()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
