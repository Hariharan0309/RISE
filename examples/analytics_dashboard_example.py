"""
RISE Analytics Dashboard Example
Demonstrates how to use the analytics dashboard and aggregator
"""

import boto3
from datetime import datetime, timedelta
import json
from infrastructure.analytics_aggregator import AnalyticsAggregator


def example_generate_comprehensive_report():
    """Example: Generate comprehensive analytics report"""
    print("=" * 60)
    print("Example: Generate Comprehensive Analytics Report")
    print("=" * 60)
    
    aggregator = AnalyticsAggregator()
    
    # Generate report for last 30 days
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    
    print(f"\nGenerating report from {start_time.date()} to {end_time.date()}")
    
    report = aggregator.generate_comprehensive_report(start_time, end_time)
    
    print("\n📊 COMPREHENSIVE ANALYTICS REPORT")
    print("=" * 60)
    
    # User Adoption
    print("\n👥 USER ADOPTION METRICS")
    user_adoption = report['user_adoption']
    print(f"  Active Users: {user_adoption['active_users']:,}")
    print(f"  Avg Session Duration: {user_adoption['avg_session_duration_minutes']} minutes")
    print(f"  Return Rate: {user_adoption['return_rate_percent']}%")
    print(f"  Language Distribution:")
    for lang, count in user_adoption['language_distribution'].items():
        print(f"    - {lang}: {count:,} users")
    
    # Impact Metrics
    print("\n📈 IMPACT METRICS")
    impact = report['impact_metrics']
    
    yield_imp = impact['yield_improvement']
    print(f"  Yield Improvement:")
    print(f"    - Average: {yield_imp['average_percent']}%")
    print(f"    - Target: {yield_imp['target_range']}")
    print(f"    - Target Met: {'✓' if yield_imp['meets_target'] else '✗'}")
    
    cost_red = impact['cost_reduction']
    print(f"  Cost Reduction:")
    print(f"    - Total Savings: ₹{cost_red['total_savings_inr']:,.2f}")
    print(f"    - Target: {cost_red['target_range']}")
    
    market = impact['market_access']
    print(f"  Market Access:")
    print(f"    - Users: {market['users_count']:,} ({market['percent']}%)")
    print(f"    - Target Met: {'✓' if market['meets_target'] else '✗'}")
    
    scheme = impact['scheme_adoption']
    print(f"  Scheme Adoption:")
    print(f"    - Users: {scheme['users_count']:,} ({scheme['percent']}%)")
    print(f"    - Target Met: {'✓' if scheme['meets_target'] else '✗'}")
    
    # Technical Performance
    print("\n⚡ TECHNICAL PERFORMANCE")
    performance = report['technical_performance']
    
    response = performance['response_time']
    print(f"  Response Time:")
    print(f"    - Average: {response['average_ms']:.0f} ms")
    print(f"    - P99: {response['p99_ms']:.0f} ms")
    print(f"    - Target Met: {'✓' if response['meets_target'] else '✗'}")
    
    accuracy = performance['accuracy_rates']
    print(f"  Accuracy Rates:")
    print(f"    - Diagnosis: {accuracy['diagnosis_percent']}%")
    print(f"    - Pest ID: {accuracy['pest_identification_percent']}%")
    
    uptime = performance['uptime']
    print(f"  Uptime: {uptime['percent']}% (Target: {uptime['target']}%)")
    
    # Feature Adoption
    print("\n🎯 FEATURE ADOPTION (Top 5)")
    features = report['feature_adoption']
    sorted_features = sorted(
        features.items(),
        key=lambda x: x[1]['usage_count'],
        reverse=True
    )[:5]
    
    for feature, metrics in sorted_features:
        print(f"  {feature}:")
        print(f"    - Usage: {metrics['usage_count']:,}")
        print(f"    - Success Rate: {metrics['success_rate_percent']}%")
    
    # Resource Sharing
    print("\n🤝 RESOURCE SHARING")
    resource = report['resource_sharing']
    
    equipment = resource['equipment_utilization']
    print(f"  Equipment Utilization: {equipment['average_percent']}%")
    
    coop = resource['cooperative_buying']
    print(f"  Cooperative Buying:")
    print(f"    - Avg Savings: {coop['average_savings_percent']}%")
    print(f"    - Total Savings: ₹{coop['total_savings_inr']:,.2f}")
    print(f"    - Target Met: {'✓' if coop['meets_target'] else '✗'}")
    
    print("\n" + "=" * 60)
    print(f"Report generated at: {report['generated_at']}")
    print("=" * 60)


def example_user_adoption_metrics():
    """Example: Get user adoption metrics only"""
    print("\n" + "=" * 60)
    print("Example: User Adoption Metrics")
    print("=" * 60)
    
    aggregator = AnalyticsAggregator()
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    metrics = aggregator.get_user_adoption_metrics(start_time, end_time)
    
    print(f"\n📊 User Adoption (Last 7 Days)")
    print(f"  Active Users: {metrics['active_users']:,}")
    print(f"  Avg Session Duration: {metrics['avg_session_duration_minutes']} min")
    print(f"  Return Rate: {metrics['return_rate_percent']}%")
    print(f"\n  Language Distribution:")
    for lang, count in metrics['language_distribution'].items():
        percentage = (count / metrics['active_users'] * 100) if metrics['active_users'] > 0 else 0
        print(f"    {lang}: {count:,} ({percentage:.1f}%)")


def example_impact_metrics():
    """Example: Get impact metrics only"""
    print("\n" + "=" * 60)
    print("Example: Impact Metrics")
    print("=" * 60)
    
    aggregator = AnalyticsAggregator()
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    
    metrics = aggregator.get_impact_metrics(start_time, end_time)
    
    print(f"\n📈 Impact Metrics (Last 30 Days)")
    
    yield_data = metrics['yield_improvement']
    print(f"\n  🌾 Yield Improvement:")
    print(f"    Average: {yield_data['average_percent']}%")
    print(f"    Range: {yield_data['minimum_percent']}% - {yield_data['maximum_percent']}%")
    print(f"    Target: {yield_data['target_range']}")
    print(f"    Status: {'✓ Target Met' if yield_data['meets_target'] else '✗ Below Target'}")
    
    cost_data = metrics['cost_reduction']
    print(f"\n  💰 Cost Reduction:")
    print(f"    Total Savings: ₹{cost_data['total_savings_inr']:,.2f}")
    print(f"    Target: {cost_data['target_range']} reduction")
    
    market_data = metrics['market_access']
    print(f"\n  🏪 Market Access:")
    print(f"    Users: {market_data['users_count']:,}")
    print(f"    Percentage: {market_data['percent']}%")
    print(f"    Status: {'✓ Target Met' if market_data['meets_target'] else '✗ Below Target'}")
    
    scheme_data = metrics['scheme_adoption']
    print(f"\n  🏛️ Scheme Adoption:")
    print(f"    Users: {scheme_data['users_count']:,}")
    print(f"    Percentage: {scheme_data['percent']}%")
    print(f"    Status: {'✓ Target Met' if scheme_data['meets_target'] else '✗ Below Target'}")


def example_performance_metrics():
    """Example: Get technical performance metrics"""
    print("\n" + "=" * 60)
    print("Example: Technical Performance Metrics")
    print("=" * 60)
    
    aggregator = AnalyticsAggregator()
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)
    
    metrics = aggregator.get_technical_performance_metrics(start_time, end_time)
    
    print(f"\n⚡ Technical Performance (Last 24 Hours)")
    
    response = metrics['response_time']
    print(f"\n  ⏱️ Response Time:")
    print(f"    Average: {response['average_ms']:.0f} ms")
    print(f"    P99: {response['p99_ms']:.0f} ms")
    print(f"    Target: {response['target_ms']} ms")
    print(f"    Status: {'✓ Target Met' if response['meets_target'] else '✗ Exceeds Target'}")
    
    accuracy = metrics['accuracy_rates']
    print(f"\n  🎯 Accuracy Rates:")
    print(f"    Diagnosis: {accuracy['diagnosis_percent']}% (Target: {accuracy['diagnosis_target']}%)")
    print(f"    Pest ID: {accuracy['pest_identification_percent']}% (Target: {accuracy['pest_target']}%)")
    print(f"    Diagnosis Status: {'✓' if accuracy['diagnosis_meets_target'] else '✗'}")
    print(f"    Pest ID Status: {'✓' if accuracy['pest_meets_target'] else '✗'}")
    
    uptime = metrics['uptime']
    print(f"\n  🟢 System Uptime:")
    print(f"    Current: {uptime['percent']}%")
    print(f"    Target: {uptime['target']}%")
    print(f"    Status: {'✓ Target Met' if uptime['meets_target'] else '✗ Below Target'}")


def example_feature_adoption():
    """Example: Get feature adoption metrics"""
    print("\n" + "=" * 60)
    print("Example: Feature Adoption Metrics")
    print("=" * 60)
    
    aggregator = AnalyticsAggregator()
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    metrics = aggregator.get_feature_adoption_metrics(start_time, end_time)
    
    print(f"\n🎯 Feature Adoption (Last 7 Days)")
    print(f"\n{'Feature':<30} {'Usage':<10} {'Success Rate'}")
    print("-" * 60)
    
    # Sort by usage count
    sorted_features = sorted(
        metrics.items(),
        key=lambda x: x[1]['usage_count'],
        reverse=True
    )
    
    for feature, data in sorted_features:
        feature_name = feature.replace('_', ' ').title()
        usage = data['usage_count']
        success = data['success_rate_percent']
        print(f"{feature_name:<30} {usage:<10,} {success}%")


def example_resource_sharing():
    """Example: Get resource sharing metrics"""
    print("\n" + "=" * 60)
    print("Example: Resource Sharing Metrics")
    print("=" * 60)
    
    aggregator = AnalyticsAggregator()
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    
    metrics = aggregator.get_resource_sharing_metrics(start_time, end_time)
    
    print(f"\n🤝 Resource Sharing (Last 30 Days)")
    
    equipment = metrics['equipment_utilization']
    print(f"\n  🚜 Equipment Utilization:")
    print(f"    Average: {equipment['average_percent']}%")
    print(f"    Description: {equipment['description']}")
    
    coop = metrics['cooperative_buying']
    print(f"\n  🛒 Cooperative Buying:")
    print(f"    Avg Savings: {coop['average_savings_percent']}%")
    print(f"    Total Savings: ₹{coop['total_savings_inr']:,.2f}")
    print(f"    Target: {coop['target_range']}")
    print(f"    Status: {'✓ Target Met' if coop['meets_target'] else '✗ Below Target'}")


def example_lambda_invocation():
    """Example: Invoke analytics Lambda function"""
    print("\n" + "=" * 60)
    print("Example: Lambda Function Invocation")
    print("=" * 60)
    
    lambda_client = boto3.client('lambda')
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    payload = {
        'action': 'generate_report',
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat()
    }
    
    print(f"\nInvoking Lambda function: rise-analytics-aggregator")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = lambda_client.invoke(
            FunctionName='rise-analytics-aggregator',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"\nResponse Status Code: {result['statusCode']}")
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            print(f"\nReport generated successfully!")
            print(f"Active Users: {body['user_adoption']['active_users']:,}")
            print(f"Yield Improvement: {body['impact_metrics']['yield_improvement']['average_percent']}%")
        else:
            print(f"Error: {result.get('body', 'Unknown error')}")
    
    except Exception as e:
        print(f"\nError invoking Lambda: {str(e)}")
        print("Note: Make sure the Lambda function is deployed and you have proper AWS credentials")


def example_run_streamlit_dashboard():
    """Example: Instructions for running Streamlit dashboard"""
    print("\n" + "=" * 60)
    print("Example: Running Streamlit Analytics Dashboard")
    print("=" * 60)
    
    print("""
To run the analytics dashboard:

1. Make sure you have Streamlit installed:
   pip install streamlit plotly

2. Run the dashboard:
   streamlit run ui/analytics_dashboard.py

3. The dashboard will open in your browser at http://localhost:8501

4. Features:
   - Select time period (Last 24 Hours, 7 Days, 30 Days, or Custom)
   - View overview metrics
   - Explore detailed metrics in tabs:
     * User Adoption
     * Impact Metrics
     * Performance
     * Feature Adoption
     * Resource Sharing
   - Refresh data with the button in sidebar
   - Interactive charts and visualizations

5. The dashboard will fetch real data from CloudWatch and DynamoDB
   or use mock data if AWS services are not available.
    """)


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("RISE ANALYTICS DASHBOARD EXAMPLES")
    print("=" * 60)
    
    # Run examples
    example_generate_comprehensive_report()
    example_user_adoption_metrics()
    example_impact_metrics()
    example_performance_metrics()
    example_feature_adoption()
    example_resource_sharing()
    example_lambda_invocation()
    example_run_streamlit_dashboard()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
