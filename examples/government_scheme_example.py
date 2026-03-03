"""
RISE Government Scheme Tools - Example Usage
Demonstrates how to use government scheme tools for searching, ingesting, and managing schemes
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

from government_scheme_tools import (
    GovernmentSchemeTools,
    search_schemes_tool,
    get_scheme_details_tool,
    ingest_scheme_tool
)
import json
from datetime import datetime, timedelta


def example_search_schemes():
    """Example: Search for government schemes"""
    print("=" * 60)
    print("Example 1: Search for Government Schemes")
    print("=" * 60)
    
    tools = GovernmentSchemeTools(region='us-east-1')
    
    # Search for central subsidies
    print("\n1. Searching for central subsidy schemes...")
    result = tools.search_schemes(
        state='central',
        category='subsidies',
        scheme_type='central',
        active_only=True
    )
    
    if result['success']:
        print(f"Found {result['count']} schemes:")
        for scheme in result['schemes']:
            print(f"\n  • {scheme['scheme_name']}")
            print(f"    Benefit: ₹{scheme.get('benefit_amount', 0):,.0f}")
            print(f"    Category: {scheme['category']}")
    else:
        print(f"Error: {result['error']}")
    
    # Search for crop insurance schemes
    print("\n2. Searching for crop insurance schemes...")
    result = tools.search_schemes(category='crop_insurance')
    
    if result['success']:
        print(f"Found {result['count']} insurance schemes:")
        for scheme in result['schemes']:
            print(f"\n  • {scheme['scheme_name']}")
            print(f"    Coverage: ₹{scheme.get('benefit_amount', 0):,.0f}")


def example_ingest_scheme():
    """Example: Ingest new scheme data"""
    print("\n" + "=" * 60)
    print("Example 2: Ingest New Scheme Data")
    print("=" * 60)
    
    tools = GovernmentSchemeTools(region='us-east-1')
    
    # Create new scheme data
    new_scheme = {
        'scheme_name': 'Uttar Pradesh Organic Farming Scheme 2024',
        'scheme_type': 'state',
        'state': 'uttar pradesh',
        'category': 'organic_farming',
        'description': 'Financial assistance for farmers transitioning to organic farming practices',
        'benefit_amount': 25000,
        'eligibility_criteria': {
            'land_ownership': 'required',
            'land_size': 'minimum 1 acre',
            'farmer_type': 'all',
            'organic_certification': 'not_required_initially'
        },
        'application_process': 'Apply through district agriculture office or online portal',
        'required_documents': [
            'Aadhaar Card',
            'Land Ownership Documents',
            'Bank Account Details',
            'Farmer Registration Certificate'
        ],
        'application_deadline': (datetime.now() + timedelta(days=120)).isoformat(),
        'official_website': 'https://upagriculture.gov.in/organic-scheme',
        'active_status': 'active'
    }
    
    print("\nIngesting new scheme...")
    result = tools.ingest_scheme_data(new_scheme)
    
    if result['success']:
        print(f"✓ Successfully ingested scheme!")
        print(f"  Scheme ID: {result['scheme_id']}")
        print(f"  Scheme Name: {result['scheme_name']}")
    else:
        print(f"✗ Error: {result['error']}")


def example_get_scheme_details():
    """Example: Get detailed scheme information"""
    print("\n" + "=" * 60)
    print("Example 3: Get Scheme Details")
    print("=" * 60)
    
    tools = GovernmentSchemeTools(region='us-east-1')
    
    # First, scrape some schemes to have data
    print("\nScraping government schemes...")
    scrape_result = tools.scrape_government_schemes('all')
    
    if scrape_result['success']:
        print(f"✓ Ingested {scrape_result['ingested_count']} schemes")
        
        # Search for a scheme
        search_result = tools.search_schemes(category='subsidies', active_only=True)
        
        if search_result['success'] and search_result['count'] > 0:
            scheme_id = search_result['schemes'][0]['scheme_id']
            
            print(f"\nGetting details for scheme: {scheme_id}")
            details_result = tools.get_scheme_details(scheme_id)
            
            if details_result['success']:
                scheme = details_result['scheme']
                print(f"\n{'='*50}")
                print(f"Scheme: {scheme['scheme_name']}")
                print(f"{'='*50}")
                print(f"Type: {scheme['scheme_type'].title()}")
                print(f"Category: {scheme['category'].replace('_', ' ').title()}")
                print(f"Benefit Amount: ₹{scheme.get('benefit_amount', 0):,.0f}")
                print(f"\nDescription:")
                print(f"  {scheme.get('description', 'N/A')}")
                print(f"\nEligibility Criteria:")
                for key, value in scheme.get('eligibility_criteria', {}).items():
                    print(f"  • {key.replace('_', ' ').title()}: {value}")
                print(f"\nRequired Documents:")
                for doc in scheme.get('required_documents', []):
                    print(f"  • {doc}")
                print(f"\nApplication Process:")
                print(f"  {scheme.get('application_process', 'N/A')}")
                if scheme.get('official_website'):
                    print(f"\nOfficial Website: {scheme['official_website']}")


def example_update_scheme_status():
    """Example: Update scheme status"""
    print("\n" + "=" * 60)
    print("Example 4: Update Scheme Status")
    print("=" * 60)
    
    tools = GovernmentSchemeTools(region='us-east-1')
    
    # Search for a scheme
    search_result = tools.search_schemes(active_only=True)
    
    if search_result['success'] and search_result['count'] > 0:
        scheme_id = search_result['schemes'][0]['scheme_id']
        scheme_name = search_result['schemes'][0]['scheme_name']
        
        print(f"\nUpdating status for: {scheme_name}")
        print(f"Scheme ID: {scheme_id}")
        
        # Update to inactive
        result = tools.update_scheme_status(scheme_id, 'inactive')
        
        if result['success']:
            print(f"✓ Status updated to: {result['new_status']}")
            
            # Update back to active
            result2 = tools.update_scheme_status(scheme_id, 'active')
            if result2['success']:
                print(f"✓ Status restored to: {result2['new_status']}")
        else:
            print(f"✗ Error: {result['error']}")


def example_monitor_schemes():
    """Example: Monitor scheme updates"""
    print("\n" + "=" * 60)
    print("Example 5: Monitor Scheme Updates")
    print("=" * 60)
    
    tools = GovernmentSchemeTools(region='us-east-1')
    
    print("\nMonitoring schemes for updates and expiration...")
    result = tools.monitor_scheme_updates()
    
    if result['success']:
        print(f"✓ Monitoring completed!")
        print(f"  Total schemes monitored: {result['total_schemes_monitored']}")
        print(f"  Expired schemes found: {result['expired_schemes']}")
        print(f"  Updates found: {result['updates_found']}")
        print(f"\n  {result['message']}")
    else:
        print(f"✗ Error: {result['error']}")


def example_categorize_scheme():
    """Example: AI-based scheme categorization"""
    print("\n" + "=" * 60)
    print("Example 6: AI-Based Scheme Categorization")
    print("=" * 60)
    
    tools = GovernmentSchemeTools(region='us-east-1')
    
    scheme_description = """
    The National Mission for Sustainable Agriculture (NMSA) aims to enhance agricultural 
    productivity especially in rainfed areas focusing on integrated farming, water use 
    efficiency, soil health management and synergizing resource conservation. The mission 
    promotes location specific integrated/composite farming systems.
    """
    
    print("\nCategorizing scheme using AI...")
    print(f"Description: {scheme_description[:100]}...")
    
    result = tools.categorize_scheme(scheme_description)
    
    if result['success']:
        cat = result['categorization']
        print(f"\n✓ Categorization completed!")
        print(f"  Primary Category: {cat.get('primary_category', 'N/A')}")
        print(f"  Secondary Categories: {', '.join(cat.get('secondary_categories', []))}")
        print(f"  Target Beneficiaries: {', '.join(cat.get('target_beneficiaries', []))}")
        print(f"  Key Benefits: {cat.get('key_benefits', 'N/A')[:100]}...")
        print(f"  Tags: {', '.join(cat.get('tags', []))}")
    else:
        print(f"✗ Error: {result['error']}")


def example_tool_functions():
    """Example: Using tool functions for agent integration"""
    print("\n" + "=" * 60)
    print("Example 7: Tool Functions for Agent Integration")
    print("=" * 60)
    
    # Search schemes tool
    print("\n1. Using search_schemes_tool:")
    result = search_schemes_tool(category='subsidies')
    print(result)
    
    # Get scheme details tool
    print("\n2. Using get_scheme_details_tool:")
    tools = GovernmentSchemeTools(region='us-east-1')
    search_result = tools.search_schemes(active_only=True)
    
    if search_result['success'] and search_result['count'] > 0:
        scheme_id = search_result['schemes'][0]['scheme_id']
        result = get_scheme_details_tool(scheme_id)
        print(result[:500] + "...")  # Print first 500 chars


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("RISE Government Scheme Tools - Example Usage")
    print("=" * 60)
    
    try:
        # Run examples
        example_search_schemes()
        example_ingest_scheme()
        example_get_scheme_details()
        example_update_scheme_status()
        example_monitor_schemes()
        example_categorize_scheme()
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
