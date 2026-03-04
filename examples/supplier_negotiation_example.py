"""
Example usage of RISE Supplier Negotiation Tools
Demonstrates AI-powered supplier negotiation workflow
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.supplier_negotiation_tools import create_supplier_negotiation_tools
import json


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def main():
    """Main example workflow"""
    
    print_section("RISE AI-Powered Supplier Negotiation Example")
    
    # Initialize tools
    tools = create_supplier_negotiation_tools()
    
    # Example 1: Register a supplier
    print_section("1. Register Supplier")
    
    supplier_data = {
        'business_name': 'Punjab Agro Supplies Ltd',
        'contact_person': 'Rajesh Kumar',
        'phone_number': '+91-9876543210',
        'email': 'rajesh@punjabagrocom',
        'supplier_type': 'seeds',
        'location': {
            'state': 'Punjab',
            'district': 'Ludhiana',
            'address': 'Industrial Area, Ludhiana',
            'latitude': 30.9010,
            'longitude': 75.8573
        },
        'products_offered': ['wheat_seeds', 'rice_seeds', 'fertilizer_urea', 'fertilizer_dap'],
        'certifications': ['ISO 9001', 'Seed Certification', 'Quality Assurance'],
        'quality_standards': {
            'wheat_seeds': {'purity': '98%', 'germination': '85%'},
            'rice_seeds': {'purity': '97%', 'germination': '80%'}
        },
        'delivery_areas': ['Ludhiana_Punjab', 'Patiala_Punjab', 'Amritsar_Punjab'],
        'payment_terms': ['on_delivery', 'advance_50', 'credit_30_days'],
        'minimum_order_quantity': {
            'wheat_seeds': 100,
            'rice_seeds': 100,
            'fertilizer_urea': 200
        },
        'bulk_discount_tiers': {
            '500+': '15%',
            '1000+': '20%',
            '2000+': '25%'
        }
    }
    
    result = tools.register_supplier(supplier_data)
    print(f"Registration Result: {json.dumps(result, indent=2)}")
    
    if result['success']:
        supplier_id = result['supplier_id']
        print(f"\n✅ Supplier registered successfully: {supplier_id}")
    
    # Example 2: Find suppliers
    print_section("2. Find Matching Suppliers")
    
    product_requirements = {
        'wheat_seeds': 500,
        'fertilizer_urea': 300
    }
    
    location = {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
    
    result = tools.find_suppliers(product_requirements, location)
    print(f"Search Result: Found {result.get('count', 0)} suppliers")
    
    if result['success'] and result['suppliers']:
        print("\nTop Suppliers:")
        for i, supplier in enumerate(result['suppliers'][:3], 1):
            print(f"\n{i}. {supplier['business_name']}")
            print(f"   Match Score: {supplier['match_score']}")
            print(f"   Rating: {supplier['ratings']['average']:.1f}/5.0")
            print(f"   Matching Products: {', '.join(supplier['matching_products'])}")
            print(f"   Meets MOQ: {'Yes' if supplier['meets_moq'] else 'No'}")
            print(f"   Bulk Discount: {'Available' if supplier['bulk_discount_available'] else 'Not Available'}")
        
        # Store supplier IDs for next step
        supplier_ids = [s['supplier_id'] for s in result['suppliers'][:3]]
    else:
        print("No suppliers found. Using mock supplier IDs for demo.")
        supplier_ids = ['sup_12345678', 'sup_87654321']
    
    # Example 3: Generate bulk pricing request
    print_section("3. Generate AI-Powered Bulk Pricing Request")
    
    buyer_id = "buyer_12345"
    delivery_location = {
        'state': 'Punjab',
        'district': 'Ludhiana',
        'address': 'Village Khanna, Ludhiana'
    }
    
    result = tools.generate_bulk_pricing_request(
        buyer_id,
        product_requirements,
        supplier_ids,
        delivery_location
    )
    
    if result['success']:
        negotiation_id = result['negotiation_id']
        print(f"✅ Negotiation ID: {negotiation_id}")
        print(f"Suppliers Contacted: {result['suppliers_contacted']}")
        print(f"Status: {result['status']}")
        print(f"Deadline: {result['deadline']}")
        
        print("\n📧 Generated Request Message:")
        print("-" * 80)
        print(result['request_message'])
        print("-" * 80)
        
        print("\nNext Steps:")
        for i, step in enumerate(result['next_steps'], 1):
            print(f"{i}. {step}")
    else:
        print(f"❌ Error: {result.get('error')}")
        negotiation_id = "neg_demo123"  # Use mock ID for demo
    
    # Example 4: Submit supplier quotes (simulated)
    print_section("4. Submit Supplier Quotes (Simulated)")
    
    # Simulate quotes from 2 suppliers
    quotes = [
        {
            'supplier_id': supplier_ids[0] if supplier_ids else 'sup_12345678',
            'quote_data': {
                'product_pricing': {
                    'wheat_seeds': 45.0,
                    'fertilizer_urea': 25.0
                },
                'discount_percentage': 20,
                'total_amount': 30000,
                'payment_terms': 'advance_50',
                'delivery_timeline': '7-10 days',
                'quality_certifications': ['ISO 9001', 'Seed Certification', 'Quality Assurance'],
                'warranty_terms': '6 months quality guarantee',
                'additional_notes': 'Free delivery for orders above ₹25,000'
            }
        },
        {
            'supplier_id': supplier_ids[1] if len(supplier_ids) > 1 else 'sup_87654321',
            'quote_data': {
                'product_pricing': {
                    'wheat_seeds': 42.0,
                    'fertilizer_urea': 27.0
                },
                'discount_percentage': 25,
                'total_amount': 29100,
                'payment_terms': 'on_delivery',
                'delivery_timeline': '5-7 days',
                'quality_certifications': ['ISO 9001', 'Quality Assurance'],
                'warranty_terms': '3 months quality guarantee',
                'additional_notes': 'Bulk discount available for repeat orders'
            }
        }
    ]
    
    for i, quote in enumerate(quotes, 1):
        result = tools.submit_supplier_quote(
            negotiation_id,
            quote['supplier_id'],
            quote['quote_data']
        )
        
        if result['success']:
            print(f"✅ Quote {i} submitted: {result['quote_id']}")
            print(f"   Quotes received: {result['quotes_received']}/{result['total_suppliers']}")
        else:
            print(f"❌ Quote {i} submission failed: {result.get('error')}")
    
    # Example 5: Compare quotes with AI
    print_section("5. Compare Quotes with AI Analysis")
    
    result = tools.compare_quotes(negotiation_id)
    
    if result['success']:
        print(f"✅ Analyzed {result['quotes_count']} quotes")
        print(f"\nBest Price: ₹{result['best_price']:,.2f}")
        print(f"Best Discount: {result['best_discount']}%")
        print(f"Average Price: ₹{result['average_price']:,.2f}")
        
        if result['recommended_quote']:
            rec = result['recommended_quote']
            print(f"\n🏆 Recommended Supplier: {rec['supplier_name']}")
            print(f"   Total Amount: ₹{rec['total_amount']:,.2f}")
            print(f"   Discount: {rec['discount_percentage']}%")
            print(f"   Payment Terms: {rec['payment_terms']}")
            print(f"   Delivery: {rec['delivery_timeline']}")
            print(f"   Rating: {rec['supplier_rating']:.1f}/5.0")
            
            selected_quote_id = rec['quote_id']
        
        print("\n🤖 AI Analysis:")
        print("-" * 80)
        print(result['ai_analysis'])
        print("-" * 80)
    else:
        print(f"❌ Error: {result.get('error')}")
        selected_quote_id = "quote_demo123"  # Use mock ID for demo
    
    # Example 6: Verify quality assurance
    print_section("6. Verify Quality Assurance")
    
    supplier_id_to_verify = supplier_ids[0] if supplier_ids else 'sup_12345678'
    
    result = tools.verify_quality_assurance(supplier_id_to_verify, 'wheat_seeds')
    
    if result['success']:
        print(f"✅ Quality verification completed")
        print(f"Supplier: {result['supplier_name']}")
        print(f"Product: {result['product_name']}")
        print(f"Overall Status: {result['overall_status']}")
        print(f"Compliance Score: {result['compliance_score']}%")
        
        print("\nCertifications:")
        for cert in result['certifications']:
            print(f"  ✅ {cert}")
        
        print("\nVerification Checks:")
        for check in result['verification_checks']:
            status_icon = "✅" if check['status'] == 'pass' else "❌"
            print(f"  {status_icon} {check['certification']} - {check['status'].upper()}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Example 7: Coordinate delivery
    print_section("7. Coordinate Delivery")
    
    from datetime import datetime, timedelta
    
    delivery_details = {
        'delivery_date': (datetime.now() + timedelta(days=7)).isoformat(),
        'delivery_time_slot': 'Morning (8AM-12PM)',
        'delivery_contact': {
            'name': 'Harpreet Singh',
            'phone': '+91-9876543210'
        },
        'special_instructions': 'Please call 30 minutes before delivery. Gate access from main road.'
    }
    
    result = tools.coordinate_delivery(negotiation_id, selected_quote_id, delivery_details)
    
    if result['success']:
        print(f"✅ Delivery scheduled successfully")
        print(f"Delivery ID: {result['delivery_id']}")
        print(f"Tracking Number: {result['tracking_number']}")
        print(f"Delivery Date: {result['delivery_date']}")
        print(f"Status: {result['delivery_status']}")
        
        print("\nNext Steps:")
        for i, step in enumerate(result['next_steps'], 1):
            print(f"{i}. {step}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Example 8: Manage payment
    print_section("8. Manage Payment")
    
    payment_data = {
        'payment_method': 'bank_transfer',
        'payment_schedule': [
            {'amount': 15000, 'due_date': datetime.now().isoformat(), 'description': '50% advance'},
            {'amount': 15000, 'due_date': (datetime.now() + timedelta(days=7)).isoformat(), 'description': '50% on delivery'}
        ],
        'member_contributions': {
            'farmer_001': 6000,
            'farmer_002': 6000,
            'farmer_003': 6000,
            'farmer_004': 6000,
            'farmer_005': 6000
        }
    }
    
    result = tools.manage_payment(negotiation_id, payment_data)
    
    if result['success']:
        print(f"✅ Payment setup completed")
        print(f"Payment ID: {result['payment_id']}")
        print(f"Total Amount: ₹{result['total_amount']:,.2f}")
        print(f"Payment Status: {result['payment_status']}")
        print(f"Payment Method: {result['payment_method']}")
        print(f"Payment Terms: {result['payment_terms']}")
        print(f"Group Members: {result['member_count']}")
        
        print("\nNext Steps:")
        for i, step in enumerate(result['next_steps'], 1):
            print(f"{i}. {step}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Example 9: Get negotiation status
    print_section("9. Get Negotiation Status")
    
    result = tools.get_negotiation_status(negotiation_id)
    
    if result['success']:
        print(f"✅ Negotiation Status Retrieved")
        print(f"Negotiation ID: {result['negotiation_id']}")
        print(f"Buyer ID: {result['buyer_id']}")
        print(f"Status: {result['status']}")
        print(f"Suppliers Contacted: {result['suppliers_contacted']}")
        print(f"Quotes Received: {result['quotes_received']}")
        print(f"Selected Quote: {result['selected_quote_id']}")
        print(f"Delivery ID: {result['delivery_id']}")
        print(f"Payment ID: {result['payment_id']}")
        print(f"Deadline: {result['deadline']}")
        
        print("\nProduct Requirements:")
        for product, quantity in result['product_requirements'].items():
            print(f"  • {product}: {quantity} units")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print_section("Example Complete!")
    print("This example demonstrated the complete supplier negotiation workflow:")
    print("1. ✅ Supplier registration")
    print("2. ✅ Finding matching suppliers")
    print("3. ✅ AI-powered pricing request generation")
    print("4. ✅ Quote submission")
    print("5. ✅ AI-powered quote comparison")
    print("6. ✅ Quality assurance verification")
    print("7. ✅ Delivery coordination")
    print("8. ✅ Payment management")
    print("9. ✅ Status tracking")
    print("\nThe system helps farmers negotiate better prices and manage supplier relationships efficiently!")


if __name__ == "__main__":
    main()
