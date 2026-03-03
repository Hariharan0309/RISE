"""
RISE Local Economy Tracking Example
Demonstrates how to use local economy tracking tools
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.local_economy_tools import LocalEconomyTools


def example_calculate_economic_impact():
    """Example: Calculate economic impact for a location"""
    print("="*60)
    print("Example 1: Calculate Economic Impact for Location")
    print("="*60)
    
    # Initialize tools
    economy_tools = LocalEconomyTools(region='us-east-1')
    
    # Define location
    location = {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
    
    # Define time period (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    time_period = {
        'start': start_date.isoformat(),
        'end': end_date.isoformat()
    }
    
    # Calculate economic impact
    result = economy_tools.calculate_economic_impact(location, time_period)
    
    if result['success']:
        print(f"\n✅ Economic Impact for {location['district']}, {location['state']}")
        print(f"Time Period: {time_period['start'][:10]} to {time_period['end'][:10]}")
        
        metrics = result['metrics']
        summary = result['summary']
        
        print(f"\n📈 Summary:")
        print(f"  Total Economic Benefit: ₹{metrics['total_economic_benefit']:,.2f}")
        print(f"  Farmers Benefited: {summary['total_farmers_benefited']}")
        print(f"  Total Transactions: {summary['total_transactions']}")
        print(f"  Avg Savings per Farmer: ₹{summary['average_savings_per_farmer']:,.2f}")
        print(f"  Engagement Level: {summary['engagement_level']}")
        
        print(f"\n🚜 Equipment Utilization:")
        utilization = metrics['equipment_utilization_rate']
        print(f"  Overall Rate: {utilization['overall_rate']}%")
        print(f"  Total Equipment: {utilization['total_equipment']}")
        
        print(f"\n💰 Cost Savings:")
        cost_savings = metrics['cost_savings']
        print(f"  Total: ₹{cost_savings['total']:,.2f}")
        print(f"  From Equipment Sharing: ₹{cost_savings['from_equipment_sharing']:,.2f}")
        
        print(f"\n💵 Additional Income:")
        income = metrics['additional_income']
        print(f"  Total: ₹{income['total']:,.2f}")
        print(f"  From Equipment Sharing: ₹{income['from_equipment_sharing']:,.2f}")
        
        print(f"\n🤝 Cooperative Buying Savings:")
        coop_savings = metrics['cooperative_buying_savings']
        print(f"  Total: ₹{coop_savings['total']:,.2f}")
        print(f"  Active Groups: {coop_savings['group_count']}")
        
        print(f"\n🌱 Sustainability Metrics:")
        sustainability = metrics['sustainability_metrics']
        print(f"  Equipment Purchases Avoided: {sustainability['equipment_purchases_avoided']}")
        print(f"  CO₂ Savings: {sustainability['estimated_co2_savings_kg']:,.0f} kg")
        print(f"  Resource Efficiency: {sustainability['resource_efficiency_score']}%")
        print(f"  Sustainability Level: {sustainability['sustainability_level']}")
    else:
        print(f"\n❌ Error: {result['error']}")


def example_track_user_savings():
    """Example: Track cost savings for a specific farmer"""
    print("\n" + "="*60)
    print("Example 2: Track Cost Savings for Farmer")
    print("="*60)
    
    # Initialize tools
    economy_tools = LocalEconomyTools(region='us-east-1')
    
    # User ID
    user_id = 'farmer_12345'
    
    # Time period (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    time_period = {
        'start': start_date.isoformat(),
        'end': end_date.isoformat()
    }
    
    # Track cost savings
    result = economy_tools.track_cost_savings(user_id, time_period)
    
    if result['success']:
        print(f"\n✅ Cost Savings for User: {user_id}")
        print(f"Time Period: {time_period['start'][:10]} to {time_period['end'][:10]}")
        
        savings = result['savings_breakdown']
        
        print(f"\n💰 Total Savings: ₹{savings['total_savings']:,.2f}")
        
        print(f"\n🚜 Equipment Rental Savings:")
        rental = savings['equipment_rental_savings']
        print(f"  Rental Cost: ₹{rental['rental_cost']:,.2f}")
        print(f"  vs Purchase Cost: ₹{rental['vs_purchase']:,.2f}")
        print(f"  Savings: ₹{rental['total']:,.2f}")
        print(f"  Bookings: {rental['booking_count']}")
        
        print(f"\n🤝 Cooperative Buying Savings:")
        buying = savings['cooperative_buying_savings']
        print(f"  Savings: ₹{buying['total']:,.2f}")
        print(f"  Groups Joined: {buying['group_count']}")
    else:
        print(f"\n❌ Error: {result['error']}")


def example_track_user_income():
    """Example: Track additional income for a farmer"""
    print("\n" + "="*60)
    print("Example 3: Track Additional Income for Farmer")
    print("="*60)
    
    # Initialize tools
    economy_tools = LocalEconomyTools(region='us-east-1')
    
    # User ID
    user_id = 'farmer_12345'
    
    # Time period (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    time_period = {
        'start': start_date.isoformat(),
        'end': end_date.isoformat()
    }
    
    # Track additional income
    result = economy_tools.track_additional_income(user_id, time_period)
    
    if result['success']:
        print(f"\n✅ Additional Income for User: {user_id}")
        print(f"Time Period: {time_period['start'][:10]} to {time_period['end'][:10]}")
        
        income = result['income_breakdown']
        projections = result['projections']
        
        print(f"\n💵 Total Income: ₹{income['total_income']:,.2f}")
        print(f"Total Bookings: {income['total_bookings']}")
        print(f"Completed Bookings: {income['completed_bookings']}")
        
        print(f"\n📊 Income by Equipment Type:")
        by_type = income['by_equipment_type']
        if by_type:
            for equipment_type, data in by_type.items():
                print(f"  {equipment_type.title()}: ₹{data['total']:,.2f} ({data['count']} bookings)")
        else:
            print("  No income data available")
        
        print(f"\n📈 Projections:")
        print(f"  Monthly: ₹{projections['monthly']:,.2f}")
        print(f"  Annual: ₹{projections['annual']:,.2f}")
    else:
        print(f"\n❌ Error: {result['error']}")


def example_resource_utilization():
    """Example: Calculate resource utilization rates"""
    print("\n" + "="*60)
    print("Example 4: Calculate Resource Utilization")
    print("="*60)
    
    # Initialize tools
    economy_tools = LocalEconomyTools(region='us-east-1')
    
    # Define location
    location = {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
    
    # Calculate resource utilization
    result = economy_tools.calculate_resource_utilization(location)
    
    if result['success']:
        print(f"\n✅ Resource Utilization for {location['district']}, {location['state']}")
        
        metrics = result['utilization_metrics']
        
        print(f"\n📊 Overall Utilization Rate: {metrics['overall_rate']}%")
        print(f"Total Equipment: {metrics['total_equipment']}")
        
        print(f"\n🚜 Utilization by Equipment Type:")
        by_type = metrics['by_type']
        if by_type:
            for equipment_type, data in by_type.items():
                print(f"  {equipment_type.title()}: {data['rate']}% ({data['utilized']}/{data['total']})")
        else:
            print("  No equipment data available")
    else:
        print(f"\n❌ Error: {result['error']}")


def example_sustainability_metrics():
    """Example: Generate sustainability metrics"""
    print("\n" + "="*60)
    print("Example 5: Generate Sustainability Metrics")
    print("="*60)
    
    # Initialize tools
    economy_tools = LocalEconomyTools(region='us-east-1')
    
    # Define location
    location = {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
    
    # Generate sustainability metrics
    result = economy_tools.generate_sustainability_metrics(location)
    
    if result['success']:
        print(f"\n✅ Sustainability Metrics for {location['district']}, {location['state']}")
        
        metrics = result['sustainability_metrics']
        
        print(f"\n🌱 Environmental Impact:")
        print(f"  Equipment Purchases Avoided: {metrics['equipment_purchases_avoided']}")
        print(f"  CO₂ Savings: {metrics['estimated_co2_savings_kg']:,.0f} kg")
        print(f"  Resource Efficiency Score: {metrics['resource_efficiency_score']}%")
        print(f"  Shared Equipment Count: {metrics['shared_equipment_count']}")
        print(f"  Sustainability Level: {metrics['sustainability_level']}")
    else:
        print(f"\n❌ Error: {result['error']}")


def example_community_network():
    """Example: Get community network visualization data"""
    print("\n" + "="*60)
    print("Example 6: Get Community Network Data")
    print("="*60)
    
    # Initialize tools
    economy_tools = LocalEconomyTools(region='us-east-1')
    
    # Define location
    location = {
        'state': 'Punjab',
        'district': 'Ludhiana'
    }
    
    # Get community network data
    result = economy_tools.get_community_network_data(location)
    
    if result['success']:
        print(f"\n✅ Community Network for {location['district']}, {location['state']}")
        
        stats = result['statistics']
        
        print(f"\n👥 Network Statistics:")
        print(f"  Total Users: {stats['total_users']}")
        print(f"  Active Participants: {stats['active_participants']}")
        print(f"  Total Connections: {stats['total_connections']}")
        print(f"  Equipment Sharing Connections: {stats['equipment_sharing_connections']}")
        print(f"  Buying Group Connections: {stats['buying_group_connections']}")
        
        network = result['network']
        print(f"\n🔗 Network Nodes: {len(network['nodes'])}")
        print(f"Network Connections: {len(network['connections'])}")
    else:
        print(f"\n❌ Error: {result['error']}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("RISE Local Economy Tracking Examples")
    print("="*60)
    
    try:
        # Run examples
        example_calculate_economic_impact()
        example_track_user_savings()
        example_track_user_income()
        example_resource_utilization()
        example_sustainability_metrics()
        example_community_network()
        
        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
