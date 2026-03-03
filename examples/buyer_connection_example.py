"""
RISE Direct Buyer Connection Example
Demonstrates buyer registration, crop listing, matching, and transaction flow
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.buyer_connection_tools import create_buyer_connection_tools
import json


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def main():
    """Run buyer connection examples"""
    
    # Initialize tools
    print("Initializing RISE Direct Buyer Connection Tools...")
    buyer_tools = create_buyer_connection_tools(region='us-east-1')
    print("✓ Tools initialized successfully\n")
    
    # Example 1: Register a Buyer
    print_section("Example 1: Register a Buyer")
    
    buyer_data = {
        'business_name': 'Fresh Produce Traders Pvt Ltd',
        'contact_person': 'Rajesh Kumar',
        'phone_number': '+919876543210',
        'email': 'rajesh@freshproduce.com',
        'business_type': 'wholesaler',
        'location': {
            'state': 'Delhi',
            'district': 'Central Delhi',
            'address': 'Azadpur Mandi, Delhi',
            'latitude': 28.7041,
            'longitude': 77.1025
        },
        'crop_interests': ['wheat', 'rice', 'potato', 'onion'],
        'quality_requirements': {
            'wheat': {'min_grade': 'grade_a'},
            'rice': {'min_grade': 'grade_a'}
        },
        'payment_terms': 'advance_50_percent',
        'verification_documents': ['gst_certificate', 'trade_license']
    }
    
    print("Registering buyer:")
    print(json.dumps(buyer_data, indent=2))
    
    buyer_result = buyer_tools.register_buyer(buyer_data)
    
    if buyer_result['success']:
        print(f"\n✓ Buyer registered successfully!")
        print(f"  Buyer ID: {buyer_result['buyer_id']}")
        print(f"  Status: {buyer_result['verification_status']}")
        print(f"  Message: {buyer_result['message']}")
    else:
        print(f"\n✗ Registration failed: {buyer_result.get('error')}")
    
    # Example 2: Create a Crop Listing
    print_section("Example 2: Create a Crop Listing")
    
    farmer_id = 'farmer_12345'
    listing_data = {
        'crop_name': 'wheat',
        'quantity': 150,
        'unit': 'quintal',
        'quality_grade': 'grade_a',
        'expected_price': 2500,
        'harvest_date': '2024-04-15',
        'available_from': '2024-04-20',
        'location': {
            'state': 'Uttar Pradesh',
            'district': 'Ghaziabad',
            'latitude': 28.6692,
            'longitude': 77.4538
        },
        'description': 'High quality wheat from well-maintained farm. Organic farming practices used.',
        'certifications': ['organic_certified'],
        'images': ['wheat_field_1.jpg', 'wheat_sample_1.jpg']
    }
    
    print(f"Creating crop listing for farmer: {farmer_id}")
    print(json.dumps(listing_data, indent=2))
    
    listing_result = buyer_tools.create_crop_listing(farmer_id, listing_data)
    
    if listing_result['success']:
        print(f"\n✓ Crop listing created successfully!")
        print(f"  Listing ID: {listing_result['listing_id']}")
        print(f"  Status: {listing_result['status']}")
        print(f"  Potential Matches: {listing_result['potential_matches']}")
        
        if listing_result['matches']:
            print(f"\n  Top Matched Buyers:")
            for i, match in enumerate(listing_result['matches'][:3], 1):
                print(f"\n  {i}. {match['business_name']}")
                print(f"     Type: {match['business_type']}")
                print(f"     Match Score: {match['match_score']}")
                print(f"     Distance: {match['distance_km']:.1f} km")
                print(f"     Rating: {match['ratings'].get('average', 0)}/5")
                print(f"     Payment Terms: {match['payment_terms']}")
    else:
        print(f"\n✗ Listing creation failed: {listing_result.get('error')}")
    
    # Example 3: Get Quality Standards
    print_section("Example 3: Get Quality Standards")
    
    crop_name = 'wheat'
    print(f"Fetching quality standards for: {crop_name}")
    
    standards_result = buyer_tools.get_quality_standards(crop_name)
    
    if standards_result['success']:
        standards = standards_result['standards']
        print(f"\n✓ Quality standards retrieved for {crop_name.title()}:")
        print(f"\n  Available Grades: {', '.join(standards['grades'])}")
        
        print(f"\n  Quality Parameters:")
        for param, values in standards['parameters'].items():
            param_name = param.replace('_', ' ').title()
            if 'max' in values:
                print(f"    • {param_name}: Max {values['max']}{values.get('unit', '')}")
            elif 'min' in values:
                print(f"    • {param_name}: Min {values['min']}{values.get('unit', '')}")
            elif 'requirement' in values:
                print(f"    • {param_name}: {values['requirement']}")
        
        print(f"\n  Premium Grade Criteria:")
        for param, values in standards['premium_criteria'].items():
            param_name = param.replace('_', ' ').title()
            if 'max' in values:
                print(f"    • {param_name}: Max {values['max']}")
            elif 'min' in values:
                print(f"    • {param_name}: Min {values['min']}")
    else:
        print(f"\n✗ Failed to fetch standards: {standards_result.get('error')}")
    
    # Example 4: Get Price Benchmarks
    print_section("Example 4: Get Price Benchmarks for Negotiation")
    
    location = {
        'state': 'Uttar Pradesh',
        'district': 'Ghaziabad',
        'latitude': 28.6692,
        'longitude': 77.4538
    }
    
    print(f"Fetching price benchmarks for: {crop_name}")
    print(f"Location: {location['district']}, {location['state']}")
    
    benchmarks_result = buyer_tools.get_price_benchmarks(crop_name, location)
    
    if benchmarks_result['success']:
        print(f"\n✓ Price benchmarks retrieved:")
        print(f"\n  Market Average: ₹{benchmarks_result['market_average']:.2f}/{benchmarks_result['unit']}")
        print(f"  Market Range: ₹{benchmarks_result['market_range']['min']} - ₹{benchmarks_result['market_range']['max']}")
        
        fair_range = benchmarks_result['fair_price_range']
        print(f"\n  Fair Price Range for Negotiation:")
        print(f"    • Minimum: ₹{fair_range['min']}/{benchmarks_result['unit']}")
        print(f"    • Recommended: ₹{fair_range['recommended']}/{benchmarks_result['unit']}")
        print(f"    • Maximum: ₹{fair_range['max']}/{benchmarks_result['unit']}")
        
        print(f"\n  Last Updated: {benchmarks_result['last_updated']}")
    else:
        print(f"\n✗ Failed to fetch benchmarks: {benchmarks_result.get('error')}")
    
    # Example 5: Initiate a Transaction
    print_section("Example 5: Initiate a Transaction")
    
    if listing_result['success'] and listing_result['matches']:
        listing_id = listing_result['listing_id']
        buyer_id = listing_result['matches'][0]['buyer_id']
        
        negotiation_data = {
            'agreed_price': 2550,
            'quantity': 150,
            'payment_terms': 'advance_50_percent',
            'delivery_date': '2024-04-25',
            'delivery_location': {
                'address': 'Azadpur Mandi, Delhi',
                'latitude': 28.7041,
                'longitude': 77.1025
            }
        }
        
        print(f"Initiating transaction:")
        print(f"  Listing ID: {listing_id}")
        print(f"  Buyer ID: {buyer_id}")
        print(f"  Agreed Price: ₹{negotiation_data['agreed_price']}/quintal")
        print(f"  Quantity: {negotiation_data['quantity']} quintal")
        print(f"  Payment Terms: {negotiation_data['payment_terms']}")
        
        transaction_result = buyer_tools.initiate_transaction(
            listing_id,
            buyer_id,
            negotiation_data
        )
        
        if transaction_result['success']:
            print(f"\n✓ Transaction initiated successfully!")
            print(f"  Transaction ID: {transaction_result['transaction_id']}")
            print(f"  Status: {transaction_result['status']}")
            print(f"  Payment Status: {transaction_result['payment_status']}")
            
            print(f"\n  Next Steps:")
            for i, step in enumerate(transaction_result['next_steps'], 1):
                print(f"    {i}. {step}")
        else:
            print(f"\n✗ Transaction failed: {transaction_result.get('error')}")
    else:
        print("Skipping transaction example (no listing or matches available)")
    
    # Example 6: Multiple Crop Listings
    print_section("Example 6: Multiple Crop Listings")
    
    crops_to_list = [
        {
            'crop_name': 'rice',
            'quantity': 200,
            'quality_grade': 'premium',
            'expected_price': 3000,
            'location': {
                'state': 'Punjab',
                'district': 'Ludhiana',
                'latitude': 30.9010,
                'longitude': 75.8573
            }
        },
        {
            'crop_name': 'potato',
            'quantity': 300,
            'quality_grade': 'grade_a',
            'expected_price': 1200,
            'location': {
                'state': 'Uttar Pradesh',
                'district': 'Agra',
                'latitude': 27.1767,
                'longitude': 78.0081
            }
        }
    ]
    
    print("Creating multiple crop listings:\n")
    
    for crop_data in crops_to_list:
        result = buyer_tools.create_crop_listing(f"farmer_{crop_data['crop_name']}", crop_data)
        
        if result['success']:
            print(f"✓ {crop_data['crop_name'].title()}: {result['potential_matches']} potential buyers found")
        else:
            print(f"✗ {crop_data['crop_name'].title()}: Failed to create listing")
    
    print("\n" + "="*60)
    print("  Examples completed successfully!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
