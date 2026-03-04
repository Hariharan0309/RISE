"""
RISE Cooperative Buying Groups Example
Demonstrates how to use the buying group tools for cooperative purchasing
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.buying_group_tools import create_buying_group_tools
from datetime import datetime, timedelta
import json


def main():
    """Run buying groups example"""
    
    print("="*60)
    print("RISE Cooperative Buying Groups Example")
    print("="*60)
    
    # Initialize tools
    buying_tools = create_buying_group_tools()
    
    # Example 1: Create a buying group
    print("\n1. Creating a Buying Group")
    print("-" * 60)
    
    organizer_id = "farmer_12345"
    group_data = {
        'group_name': 'Ludhiana Seed Buyers Cooperative',
        'target_products': ['wheat_seeds', 'fertilizer_urea', 'pesticide_spray'],
        'location': {
            'state': 'Punjab',
            'district': 'Ludhiana',
            'radius_km': 25
        },
        'max_members': 30,
        'min_members': 5,
        'deadline': (datetime.now() + timedelta(days=14)).isoformat()
    }
    
    result = buying_tools.create_buying_group(organizer_id, group_data)
    
    if result['success']:
        print(f"✓ Group created successfully!")
        print(f"  Group ID: {result['group_id']}")
        print(f"  Group Name: {result['group_name']}")
        print(f"  Status: {result['status']}")
        print(f"  Target Discount: {result['target_discount']}")
        print(f"  Deadline: {result['deadline']}")
        
        group_id = result['group_id']
    else:
        print(f"✗ Failed to create group: {result.get('error')}")
        return
    
    # Example 2: Find matching groups
    print("\n2. Finding Matching Groups")
    print("-" * 60)
    
    user_id = "farmer_67890"
    requirements = {
        'products': ['wheat_seeds', 'fertilizer_urea'],
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
    
    result = buying_tools.find_matching_groups(user_id, requirements)
    
    if result['success']:
        print(f"✓ Found {result['count']} matching groups")
        
        for group in result['groups']:
            print(f"\n  Group: {group['group_name']}")
            print(f"  Match Score: {group['match_score']}%")
            print(f"  Members: {group['current_members']}/{group['max_members']}")
            print(f"  Matching Products: {', '.join(group['matching_products'])}")
            print(f"  Estimated Discount: {group['estimated_discount']}")
    else:
        print(f"✗ Failed to find groups: {result.get('error')}")
    
    # Example 3: Join a buying group
    print("\n3. Joining a Buying Group")
    print("-" * 60)
    
    member_requirements = {
        'wheat_seeds': 150,
        'fertilizer_urea': 75,
        'pesticide_spray': 30
    }
    
    result = buying_tools.join_buying_group(user_id, group_id, member_requirements)
    
    if result['success']:
        print(f"✓ Successfully joined {result['group_name']}")
        print(f"  Total Members: {result['total_members']}")
        print(f"  Group Status: {result['status']}")
        print(f"\n  Total Quantities:")
        for product, qty in result['total_quantities'].items():
            print(f"    • {product}: {qty} units")
        
        if result.get('potential_savings'):
            print(f"\n  Your Potential Savings:")
            total_savings = sum(result['potential_savings'].values())
            for product, savings in result['potential_savings'].items():
                print(f"    • {product}: ₹{savings:.2f}")
            print(f"  Total Estimated Savings: ₹{total_savings:.2f}")
    else:
        print(f"✗ Failed to join group: {result.get('error')}")
    
    # Example 4: Add more members
    print("\n4. Adding More Members")
    print("-" * 60)
    
    # Simulate more farmers joining
    additional_members = [
        {
            'user_id': 'farmer_11111',
            'requirements': {'wheat_seeds': 200, 'fertilizer_urea': 100}
        },
        {
            'user_id': 'farmer_22222',
            'requirements': {'wheat_seeds': 180, 'fertilizer_urea': 90, 'pesticide_spray': 40}
        },
        {
            'user_id': 'farmer_33333',
            'requirements': {'wheat_seeds': 220, 'fertilizer_urea': 110}
        }
    ]
    
    for member in additional_members:
        result = buying_tools.join_buying_group(
            member['user_id'],
            group_id,
            member['requirements']
        )
        
        if result['success']:
            print(f"✓ {member['user_id']} joined (Total members: {result['total_members']})")
        else:
            print(f"✗ {member['user_id']} failed to join: {result.get('error')}")
    
    # Example 5: Calculate bulk pricing
    print("\n5. Calculating Bulk Pricing")
    print("-" * 60)
    
    result = buying_tools.calculate_bulk_pricing(group_id)
    
    if result['success']:
        print(f"✓ Bulk pricing calculated!")
        print(f"  Average Discount: {result['average_discount']}%")
        print(f"  Total Members: {result['total_members']}")
        
        print(f"\n  Pricing Breakdown:")
        for product, pricing in result['pricing_breakdown'].items():
            print(f"\n    {product.replace('_', ' ').title()}:")
            print(f"      Quantity: {pricing['quantity']} units")
            print(f"      Market Price: ₹{pricing['market_price_per_unit']}/unit")
            print(f"      Bulk Price: ₹{pricing['bulk_price_per_unit']}/unit")
            print(f"      Discount: {pricing['discount_percentage']}%")
            print(f"      Total Cost: ₹{pricing['total_cost']:.2f}")
            print(f"      Total Savings: ₹{pricing['total_savings']:.2f}")
        
        # Show member costs
        print(f"\n  Member Cost Breakdown:")
        for member_id, costs in result['member_costs'].items():
            print(f"\n    {member_id}:")
            print(f"      Total Cost: ₹{costs['total_cost']:.2f}")
            for product, details in costs['breakdown'].items():
                print(f"        • {product}: {details['quantity']} units × ₹{details['price_per_unit']} = ₹{details['total_cost']:.2f}")
    else:
        print(f"✗ Failed to calculate pricing: {result.get('error')}")
    
    # Example 6: Negotiate with vendors
    print("\n6. Negotiating with Vendors")
    print("-" * 60)
    
    vendor_list = [
        'Punjab Agro Supplies Ltd.',
        'Ludhiana Seeds & Fertilizers',
        'Green Valley Agricultural Inputs'
    ]
    
    result = buying_tools.negotiate_with_vendors(group_id, vendor_list)
    
    if result['success']:
        print(f"✓ Vendor negotiation initiated!")
        print(f"  Vendors Contacted: {result['vendors_contacted']}")
        print(f"  Status: {result['status']}")
        
        print(f"\n  AI-Generated Negotiation Message:")
        print(f"  {'-' * 56}")
        print(f"  {result['negotiation_message'][:300]}...")
        
        print(f"\n  Next Steps:")
        for i, step in enumerate(result['next_steps'], 1):
            print(f"    {i}. {step}")
    else:
        print(f"✗ Failed to negotiate: {result.get('error')}")
    
    # Example 7: Get group details
    print("\n7. Getting Group Details")
    print("-" * 60)
    
    result = buying_tools.get_group_details(group_id)
    
    if result['success']:
        print(f"✓ Group Details:")
        print(f"  Group ID: {result['group_id']}")
        print(f"  Group Name: {result['group_name']}")
        print(f"  Status: {result['status']}")
        print(f"  Members: {result['member_count']}/{result['max_members']}")
        print(f"  Location: {result['location']['district']}, {result['location']['state']}")
        
        print(f"\n  Target Products:")
        for product in result['target_products']:
            print(f"    • {product.replace('_', ' ').title()}")
        
        if result['total_quantities']:
            print(f"\n  Total Quantities:")
            for product, qty in result['total_quantities'].items():
                print(f"    • {product}: {qty} units")
        
        if result['bulk_pricing']:
            print(f"\n  Bulk Pricing Achieved:")
            for product, discount in result['bulk_pricing'].items():
                print(f"    • {product}: {discount}% discount")
    else:
        print(f"✗ Failed to get details: {result.get('error')}")
    
    # Example 8: Get user's groups
    print("\n8. Getting User's Groups")
    print("-" * 60)
    
    result = buying_tools.get_user_groups(user_id)
    
    if result['success']:
        print(f"✓ User's Groups: {result['count']}")
        
        for group in result['groups']:
            print(f"\n  {group['group_name']}:")
            print(f"    Status: {group['status']}")
            print(f"    Members: {group['member_count']}")
            print(f"    Role: {'Organizer' if group['is_organizer'] else 'Member'}")
            print(f"    Products: {', '.join(group['target_products'])}")
    else:
        print(f"✗ Failed to get user groups: {result.get('error')}")
    
    # Summary
    print("\n" + "="*60)
    print("Summary: Cooperative Buying Groups Benefits")
    print("="*60)
    print("""
The cooperative buying groups system enables farmers to:

1. Form Groups: Create buying groups for specific agricultural inputs
2. Match Farmers: Find groups based on location, crop type, and needs
3. Aggregate Demand: Combine orders to reach bulk pricing thresholds
4. Negotiate Prices: Use AI to negotiate with suppliers for better rates
5. Save Money: Achieve 15-30% discounts on seeds, fertilizers, and inputs
6. Share Costs: Transparent pricing and equitable cost distribution
7. Coordinate Delivery: Manage payment collection and delivery logistics
8. Track Impact: Monitor economic benefits of cooperative purchasing

This system helps small farmers access bulk pricing typically available
only to large agricultural operations, improving their profitability
and sustainability.
""")


if __name__ == '__main__':
    main()
