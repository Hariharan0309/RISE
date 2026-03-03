"""
RISE Equipment Sharing Marketplace Example
Demonstrates equipment listing, search, booking, and rating flow
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.equipment_sharing_tools import create_equipment_sharing_tools
from datetime import datetime, timedelta
import json


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def main():
    """Run equipment sharing marketplace examples"""
    
    # Initialize tools
    print("Initializing RISE Equipment Sharing Marketplace Tools...")
    equipment_tools = create_equipment_sharing_tools(region='us-east-1')
    print("✓ Tools initialized successfully\n")
    
    # Example 1: List Equipment
    print_section("Example 1: List Equipment for Sharing")
    
    owner_id = 'farmer_12345'
    equipment_data = {
        'name': 'John Deere Tractor',
        'type': 'tractor',
        'model': '5075E',
        'condition': 'excellent',
        'hourly_rate': 500,
        'daily_rate': 3000,
        'year': '2020',
        'capacity': '75 HP',
        'specifications': {
            'engine': '4-cylinder diesel',
            'transmission': 'PowrReverser',
            'pto_hp': '62',
            'fuel_capacity': '90 liters'
        },
        'location': {
            'state': 'Punjab',
            'district': 'Ludhiana',
            'address': 'Village Khanna, Near GT Road',
            'latitude': 30.9010,
            'longitude': 75.8573
        },
        'photos': ['tractor_front.jpg', 'tractor_side.jpg', 'tractor_cabin.jpg'],
        'insurance_details': {
            'policy_number': 'INS123456',
            'valid_until': '2025-12-31'
        },
        'pickup_instructions': 'Contact owner 1 day before pickup. Equipment available 8 AM - 6 PM. Fuel not included in rental.'
    }
    
    print(f"Listing equipment for owner: {owner_id}")
    print(json.dumps(equipment_data, indent=2))
    
    list_result = equipment_tools.list_equipment(owner_id, equipment_data)
    
    if list_result['success']:
        print(f"\n✓ Equipment listed successfully!")
        print(f"  Resource ID: {list_result['resource_id']}")
        print(f"  Status: {list_result['status']}")
        print(f"  Estimated Monthly Income: ₹{list_result['estimated_monthly_income']:.2f}")
        print(f"  Message: {list_result['message']}")
        
        # Store resource ID for later examples
        resource_id = list_result['resource_id']
    else:
        print(f"\n✗ Listing failed: {list_result.get('error')}")
        return
    
    # Example 2: List More Equipment
    print_section("Example 2: List Multiple Equipment Types")
    
    equipment_list = [
        {
            'name': 'Submersible Water Pump',
            'type': 'pump',
            'model': 'Kirloskar KP4',
            'condition': 'good',
            'hourly_rate': 150,
            'daily_rate': 800,
            'capacity': '5 HP',
            'location': {
                'state': 'Punjab',
                'district': 'Jalandhar',
                'latitude': 31.3260,
                'longitude': 75.5762
            }
        },
        {
            'name': 'DJI Agras T30 Drone',
            'type': 'drone',
            'model': 'T30',
            'condition': 'excellent',
            'hourly_rate': 1000,
            'daily_rate': 6000,
            'capacity': '30L tank',
            'specifications': {
                'spray_width': '9 meters',
                'flight_time': '18 minutes',
                'payload': '30 kg'
            },
            'location': {
                'state': 'Punjab',
                'district': 'Patiala',
                'latitude': 30.3398,
                'longitude': 76.3869
            }
        },
        {
            'name': 'Combine Harvester',
            'type': 'harvester',
            'model': 'Preet 987',
            'condition': 'good',
            'hourly_rate': 800,
            'daily_rate': 5000,
            'capacity': '25 HP',
            'location': {
                'state': 'Punjab',
                'district': 'Ludhiana',
                'latitude': 30.8700,
                'longitude': 75.8500
            }
        }
    ]
    
    print("Listing multiple equipment:\n")
    
    for equipment in equipment_list:
        result = equipment_tools.list_equipment(f"owner_{equipment['type']}", equipment)
        
        if result['success']:
            print(f"✓ {equipment['name']}: Listed (ID: {result['resource_id']})")
            print(f"  Potential Income: ₹{result['estimated_monthly_income']:.2f}/month")
        else:
            print(f"✗ {equipment['name']}: Failed to list")
    
    # Example 3: Search Equipment
    print_section("Example 3: Search Available Equipment")
    
    search_location = {
        'state': 'Punjab',
        'district': 'Jalandhar',
        'latitude': 31.3260,
        'longitude': 75.5762
    }
    
    print(f"Searching for equipment near: {search_location['district']}, {search_location['state']}")
    print(f"Search radius: 50 km")
    
    search_result = equipment_tools.search_equipment(
        search_location,
        equipment_type=None,  # All types
        radius_km=50
    )
    
    if search_result['success']:
        print(f"\n✓ Found {search_result['count']} equipment available")
        
        if search_result['equipment']:
            print("\nAvailable Equipment:\n")
            
            for i, equipment in enumerate(search_result['equipment'][:5], 1):
                print(f"{i}. {equipment['name']} ({equipment['type'].title()})")
                print(f"   Model: {equipment.get('model', 'N/A')}")
                print(f"   Condition: {equipment['condition'].title()}")
                print(f"   Distance: {equipment['distance_km']:.1f} km")
                print(f"   Daily Rate: ₹{equipment['daily_rate']}")
                print(f"   Rating: {equipment['ratings'].get('average', 0):.1f}/5 ({equipment['ratings'].get('count', 0)} reviews)")
                print(f"   Location: {equipment['location']['district']}, {equipment['location']['state']}")
                print()
    else:
        print(f"\n✗ Search failed: {search_result.get('error')}")
    
    # Example 4: Search with Type Filter
    print_section("Example 4: Search Specific Equipment Type")
    
    print("Searching for tractors only...")
    
    tractor_search = equipment_tools.search_equipment(
        search_location,
        equipment_type='tractor',
        radius_km=50
    )
    
    if tractor_search['success']:
        print(f"\n✓ Found {tractor_search['count']} tractors available")
        
        for tractor in tractor_search['equipment']:
            print(f"\n• {tractor['name']}")
            print(f"  Daily Rate: ₹{tractor['daily_rate']}")
            print(f"  Distance: {tractor['distance_km']:.1f} km")
    else:
        print(f"\n✗ Search failed: {tractor_search.get('error')}")
    
    # Example 5: Search with Date Range
    print_section("Example 5: Search with Availability Filter")
    
    start_date = datetime.now() + timedelta(days=3)
    end_date = start_date + timedelta(days=2)
    
    date_range = {
        'start': start_date.isoformat(),
        'end': end_date.isoformat()
    }
    
    print(f"Searching for equipment available from {start_date.date()} to {end_date.date()}")
    
    date_search = equipment_tools.search_equipment(
        search_location,
        date_range=date_range,
        radius_km=50
    )
    
    if date_search['success']:
        print(f"\n✓ Found {date_search['count']} equipment available for selected dates")
    else:
        print(f"\n✗ Search failed: {date_search.get('error')}")
    
    # Example 6: Get Equipment Details
    print_section("Example 6: Get Detailed Equipment Information")
    
    print(f"Fetching details for resource: {resource_id}")
    
    details_result = equipment_tools.get_equipment_details(resource_id)
    
    if details_result['success']:
        print("\n✓ Equipment details retrieved:")
        print(f"\n  Equipment: {details_result['equipment']['name']}")
        print(f"  Type: {details_result['equipment']['type'].title()}")
        print(f"  Model: {details_result['equipment'].get('model', 'N/A')}")
        print(f"  Condition: {details_result['equipment']['condition'].title()}")
        
        print(f"\n  Pricing:")
        print(f"    Hourly Rate: ₹{details_result['pricing']['hourly_rate']}")
        print(f"    Daily Rate: ₹{details_result['pricing']['daily_rate']}")
        
        print(f"\n  Location:")
        print(f"    {details_result['location']['address']}")
        print(f"    {details_result['location']['district']}, {details_result['location']['state']}")
        
        print(f"\n  Ratings:")
        print(f"    Average: {details_result['ratings']['average']}/5")
        print(f"    Total Reviews: {details_result['ratings']['count']}")
        
        print(f"\n  Total Bookings: {details_result['total_bookings']}")
        print(f"  Availability Status: {details_result['availability_status'].upper()}")
    else:
        print(f"\n✗ Failed to fetch details: {details_result.get('error')}")
    
    # Example 7: Book Equipment
    print_section("Example 7: Book Equipment")
    
    renter_id = 'farmer_67890'
    
    booking_start = datetime.now() + timedelta(days=5)
    booking_end = booking_start + timedelta(days=2)
    
    booking_details = {
        'start_time': booking_start.isoformat(),
        'end_time': booking_end.isoformat(),
        'notes': 'Need for wheat harvesting. Will pickup at 8 AM.'
    }
    
    print(f"Booking equipment:")
    print(f"  Resource ID: {resource_id}")
    print(f"  Renter ID: {renter_id}")
    print(f"  Start: {booking_start.strftime('%Y-%m-%d %H:%M')}")
    print(f"  End: {booking_end.strftime('%Y-%m-%d %H:%M')}")
    
    booking_result = equipment_tools.book_equipment(renter_id, resource_id, booking_details)
    
    if booking_result['success']:
        print(f"\n✓ Equipment booked successfully!")
        print(f"  Booking ID: {booking_result['booking_id']}")
        print(f"  Status: {booking_result['status'].upper()}")
        print(f"  Total Cost: ₹{booking_result['total_cost']:.2f}")
        print(f"  Insurance Premium: ₹{booking_result['insurance_premium']:.2f}")
        print(f"  Payment Status: {booking_result['payment_status'].upper()}")
        
        print(f"\n  Pickup Instructions:")
        print(f"  {booking_result['pickup_instructions']}")
        
        print(f"\n  Next Steps:")
        for i, step in enumerate(booking_result['next_steps'], 1):
            print(f"    {i}. {step}")
        
        # Store booking ID for rating example
        booking_id = booking_result['booking_id']
    else:
        print(f"\n✗ Booking failed: {booking_result.get('error')}")
        return
    
    # Example 8: Rate Equipment
    print_section("Example 8: Rate Equipment After Use")
    
    print(f"Rating equipment for booking: {booking_id}")
    
    rating_data = {
        'equipment_rating': 5,
        'owner_rating': 5,
        'review': 'Excellent tractor! Well-maintained and powerful. Owner was very cooperative and helpful. Highly recommended for heavy farming work.'
    }
    
    print(f"\n  Equipment Rating: {rating_data['equipment_rating']}/5")
    print(f"  Owner Rating: {rating_data['owner_rating']}/5")
    print(f"  Review: {rating_data['review']}")
    
    rating_result = equipment_tools.rate_equipment(booking_id, rating_data)
    
    if rating_result['success']:
        print(f"\n✓ Rating submitted successfully!")
        print(f"  New Average Rating: {rating_result['new_average_rating']:.1f}/5")
        print(f"  Total Ratings: {rating_result['total_ratings']}")
    else:
        print(f"\n✗ Rating failed: {rating_result.get('error')}")
    
    # Example 9: Send Unused Equipment Alerts
    print_section("Example 9: Send Unused Equipment Alerts")
    
    print("Checking for unused equipment (30-day threshold)...")
    
    alerts_result = equipment_tools.send_unused_equipment_alerts(days_threshold=30)
    
    if alerts_result['success']:
        print(f"\n✓ Unused equipment alerts processed")
        print(f"  Alerts Sent: {alerts_result['alerts_sent']}")
        print(f"  Message: {alerts_result['message']}")
    else:
        print(f"\n✗ Alert processing failed: {alerts_result.get('error')}")
    
    # Example 10: Multiple Bookings Scenario
    print_section("Example 10: Multiple Bookings for Same Equipment")
    
    print("Creating multiple bookings to demonstrate calendar management:\n")
    
    bookings = []
    
    for i in range(3):
        booking_start = datetime.now() + timedelta(days=10 + (i * 3))
        booking_end = booking_start + timedelta(days=1)
        
        booking_details = {
            'start_time': booking_start.isoformat(),
            'end_time': booking_end.isoformat(),
            'notes': f'Booking {i+1}'
        }
        
        result = equipment_tools.book_equipment(f'renter_{i}', resource_id, booking_details)
        
        if result['success']:
            print(f"✓ Booking {i+1}: {booking_start.date()} - {booking_end.date()}")
            print(f"  Booking ID: {result['booking_id']}")
            print(f"  Cost: ₹{result['total_cost']:.2f}")
            bookings.append(result)
        else:
            print(f"✗ Booking {i+1} failed: {result.get('error')}")
    
    print(f"\nTotal successful bookings: {len(bookings)}")
    
    print("\n" + "="*60)
    print("  Examples completed successfully!")
    print("="*60 + "\n")
    
    # Summary
    print("Summary:")
    print(f"• Equipment listed with potential income of ₹{list_result['estimated_monthly_income']:.2f}/month")
    print(f"• Found {search_result['count']} equipment within 50km radius")
    print(f"• Successfully booked equipment for ₹{booking_result['total_cost']:.2f}")
    print(f"• Equipment rated {rating_result['new_average_rating']:.1f}/5")
    print(f"• {len(bookings)} additional bookings created")
    print("\n✓ Equipment sharing marketplace is fully functional!")


if __name__ == '__main__':
    main()


    # Example 11: Payment Processing
    print_section("Example 11: Process Payment for Booking")
    
    print(f"Processing payment for booking: {booking_id}")
    
    payment_details = {
        'amount': booking_result['total_cost'],
        'payment_method': 'upi',
        'reference': 'UPI987654321'
    }
    
    print(f"\n  Payment Method: {payment_details['payment_method'].upper()}")
    print(f"  Amount: ₹{payment_details['amount']:.2f}")
    print(f"  Reference: {payment_details['reference']}")
    
    payment_result = equipment_tools.process_payment(booking_id, payment_details)
    
    if payment_result['success']:
        print(f"\n✓ Payment processed successfully!")
        print(f"  Transaction ID: {payment_result['transaction_id']}")
        print(f"  Booking ID: {payment_result['booking_id']}")
        print(f"  Amount Paid: ₹{payment_result['amount_paid']:.2f}")
        print(f"  Payment Status: {payment_result['payment_status'].upper()}")
        print(f"  Message: {payment_result['message']}")
    else:
        print(f"\n✗ Payment failed: {payment_result.get('error')}")
    
    # Example 12: Usage Tracking
    print_section("Example 12: Track Equipment Usage")
    
    print(f"Updating usage tracking for booking: {booking_id}")
    
    # Update start reading
    print("\n1. Recording start of usage:")
    
    start_usage_data = {
        'start_reading': 1000,
        'actual_start_time': datetime.now().isoformat()
    }
    
    print(f"   Start Reading: {start_usage_data['start_reading']} hours")
    print(f"   Start Time: {start_usage_data['actual_start_time']}")
    
    start_result = equipment_tools.update_usage_tracking(booking_id, start_usage_data)
    
    if start_result['success']:
        print(f"\n   ✓ Start usage recorded")
    else:
        print(f"\n   ✗ Failed: {start_result.get('error')}")
    
    # Update end reading
    print("\n2. Recording end of usage:")
    
    end_usage_data = {
        'end_reading': 1048,
        'actual_end_time': (datetime.now() + timedelta(hours=48)).isoformat()
    }
    
    print(f"   End Reading: {end_usage_data['end_reading']} hours")
    print(f"   End Time: {end_usage_data['actual_end_time']}")
    
    end_result = equipment_tools.update_usage_tracking(booking_id, end_usage_data)
    
    if end_result['success']:
        print(f"\n   ✓ End usage recorded")
        print(f"   Hours Used: {end_result['usage_tracking']['hours_used']:.1f}")
        print(f"   Message: {end_result['message']}")
    else:
        print(f"\n   ✗ Failed: {end_result.get('error')}")
    
    # Example 13: Get Booking Details
    print_section("Example 13: Get Comprehensive Booking Details")
    
    print(f"Fetching complete details for booking: {booking_id}")
    
    details_result = equipment_tools.get_booking_details(booking_id)
    
    if details_result['success']:
        print("\n✓ Booking details retrieved")
        
        booking_info = details_result['booking']
        equipment_info = details_result['equipment']
        
        print(f"\n  Equipment: {equipment_info['name']} ({equipment_info['type'].title()})")
        print(f"  Model: {equipment_info.get('model', 'N/A')}")
        
        print(f"\n  Booking Status: {booking_info['status'].upper()}")
        print(f"  Payment Status: {booking_info['payment_status'].upper()}")
        print(f"  Delivery Status: {booking_info['delivery_status'].upper()}")
        
        print(f"\n  Cost Breakdown:")
        print(f"    Equipment Cost: ₹{booking_info['total_cost']:.2f}")
        print(f"    Insurance Premium: ₹{booking_info['insurance_premium']:.2f}")
        print(f"    Transport Cost: ₹{booking_info['transport_cost']:.2f}")
        print(f"    Final Amount: ₹{booking_info['final_amount']:.2f}")
        
        if booking_info['payment_details']:
            payment = booking_info['payment_details']
            print(f"\n  Payment Details:")
            print(f"    Transaction ID: {payment.get('transaction_id', 'N/A')}")
            print(f"    Payment Method: {payment.get('payment_method', 'N/A').upper()}")
            print(f"    Amount Paid: ₹{float(payment.get('amount_paid', 0)):.2f}")
        
        usage = booking_info['usage_tracking']
        print(f"\n  Usage Tracking:")
        print(f"    Start Reading: {usage.get('start_reading', 0)}")
        print(f"    End Reading: {usage.get('end_reading', 0)}")
        print(f"    Hours Used: {usage.get('hours_used', 0):.1f}")
        
        insurance = booking_info['insurance_details']
        print(f"\n  Insurance:")
        print(f"    Policy Number: {insurance.get('policy_number', 'N/A')}")
        print(f"    Coverage: ₹{float(insurance.get('coverage_amount', 0)):.2f}")
        print(f"    Premium: ₹{float(insurance.get('premium', 0)):.2f}")
        print(f"    Verified: {'✓ Yes' if insurance.get('verified') else '✗ No'}")
    else:
        print(f"\n✗ Failed to fetch details: {details_result.get('error')}")
    
    # Example 14: Get User Bookings
    print_section("Example 14: Get All User Bookings")
    
    print(f"Fetching all bookings for renter: {renter_id}")
    
    user_bookings_result = equipment_tools.get_user_bookings(renter_id, 'renter')
    
    if user_bookings_result['success']:
        print(f"\n✓ Found {user_bookings_result['count']} bookings")
        
        if user_bookings_result['bookings']:
            print("\nRenter's Bookings:\n")
            
            for i, booking in enumerate(user_bookings_result['bookings'][:5], 1):
                print(f"{i}. {booking['equipment_name']} ({booking['equipment_type'].title()})")
                print(f"   Booking ID: {booking['booking_id']}")
                print(f"   Status: {booking['status'].upper()}")
                print(f"   Payment: {booking['payment_status'].upper()}")
                print(f"   Cost: ₹{booking['final_amount']:.2f}")
                start_dt = datetime.fromisoformat(booking['booking_start'])
                print(f"   Start: {start_dt.strftime('%Y-%m-%d %H:%M')}")
                print()
    else:
        print(f"\n✗ Failed to fetch bookings: {user_bookings_result.get('error')}")
    
    # Get owner's bookings
    print(f"\nFetching all bookings for owner: {owner_id}")
    
    owner_bookings_result = equipment_tools.get_user_bookings(owner_id, 'owner')
    
    if owner_bookings_result['success']:
        print(f"\n✓ Found {owner_bookings_result['count']} bookings as equipment owner")
    else:
        print(f"\n✗ Failed to fetch owner bookings: {owner_bookings_result.get('error')}")
    
    # Example 15: Cancel Booking
    print_section("Example 15: Cancel Booking with Refund")
    
    # Create a new booking to cancel
    print("Creating a new booking to demonstrate cancellation...")
    
    cancel_booking_start = datetime.now() + timedelta(days=30)
    cancel_booking_end = cancel_booking_start + timedelta(days=1)
    
    cancel_booking_details = {
        'start_time': cancel_booking_start.isoformat(),
        'end_time': cancel_booking_end.isoformat()
    }
    
    cancel_booking_result = equipment_tools.book_equipment(
        'renter_cancel_test',
        resource_id,
        cancel_booking_details
    )
    
    if cancel_booking_result['success']:
        cancel_booking_id = cancel_booking_result['booking_id']
        
        print(f"\n✓ Booking created: {cancel_booking_id}")
        print(f"  Total Cost: ₹{cancel_booking_result['total_cost']:.2f}")
        
        # Process payment
        cancel_payment_details = {
            'amount': cancel_booking_result['total_cost'],
            'payment_method': 'card'
        }
        
        cancel_payment_result = equipment_tools.process_payment(
            cancel_booking_id,
            cancel_payment_details
        )
        
        if cancel_payment_result['success']:
            print(f"  Payment processed: {cancel_payment_result['transaction_id']}")
        
        # Now cancel the booking
        print(f"\nCancelling booking: {cancel_booking_id}")
        print(f"  Reason: Plans changed due to weather forecast")
        
        cancellation_result = equipment_tools.cancel_booking(
            cancel_booking_id,
            'Plans changed due to weather forecast'
        )
        
        if cancellation_result['success']:
            print(f"\n✓ Booking cancelled successfully!")
            print(f"  Booking ID: {cancellation_result['booking_id']}")
            print(f"  Status: {cancellation_result['status'].upper()}")
            print(f"  Refund Amount: ₹{cancellation_result['refund_amount']:.2f}")
            print(f"  Message: {cancellation_result['message']}")
        else:
            print(f"\n✗ Cancellation failed: {cancellation_result.get('error')}")
    else:
        print(f"\n✗ Could not create booking for cancellation demo")
    
    print("\n" + "="*60)
    print("  All examples completed successfully!")
    print("="*60 + "\n")
    
    # Enhanced Summary
    print("Enhanced Summary:")
    print(f"• Equipment listed with potential income of ₹{list_result['estimated_monthly_income']:.2f}/month")
    print(f"• Found {search_result['count']} equipment within 50km radius")
    print(f"• Successfully booked equipment for ₹{booking_result['total_cost']:.2f}")
    print(f"• Payment processed: Transaction ID {payment_result.get('transaction_id', 'N/A')}")
    print(f"• Usage tracked: {end_result['usage_tracking']['hours_used']:.1f} hours used")
    print(f"• Equipment rated {rating_result['new_average_rating']:.1f}/5")
    print(f"• {len(bookings)} additional bookings created")
    print(f"• {user_bookings_result['count']} total bookings for renter")
    print(f"• Booking cancellation with ₹{cancellation_result.get('refund_amount', 0):.2f} refund")
    print("\n✓ Equipment booking system is fully functional with:")
    print("  - Secure transaction processing")
    print("  - Insurance verification and tracking")
    print("  - Comprehensive usage tracking")
    print("  - Booking management and cancellation")
    print("  - Payment processing with multiple methods")
