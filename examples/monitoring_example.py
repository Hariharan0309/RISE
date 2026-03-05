"""
RISE Monitoring Example
Demonstrates how to use the monitoring system
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.cloudwatch_alarms import CloudWatchAlarmsManager
from infrastructure.custom_metrics import CustomMetricsTracker
from infrastructure.error_tracking import ErrorTracker
from infrastructure.cost_monitoring import CostMonitor
from infrastructure.monitoring_dashboard import MonitoringDashboard


def setup_monitoring_example():
    """Example: Set up complete monitoring for RISE platform"""
    
    print("=" * 60)
    print("RISE Monitoring Setup Example")
    print("=" * 60)
    
    # Configuration
    sns_topic_arn = "arn:aws:sns:us-east-1:123456789012:rise-alerts"
    account_id = "123456789012"
    region = "us-east-1"
    
    # 1. Create CloudWatch Alarms
    print("\n1. Creating CloudWatch Alarms...")
    alarm_manager = CloudWatchAlarmsManager(sns_topic_arn, region)
    
    # Create alarms for critical Lambda functions
    critical_functions = ['image_analysis', 'pest_analysis', 'weather']
    for func_key in critical_functions:
        try:
            alarms = alarm_manager.create_lambda_alarms(func_key)
            print(f"   ✓ Created {len(alarms)} alarms for {func_key}")
        except Exception as e:
            print(f"   ✗ Error creating alarms for {func_key}: {e}")
    
    # Create API Gateway alarms
    try:
        api_alarms = alarm_manager.create_api_gateway_alarms()
        print(f"   ✓ Created {len(api_alarms)} API Gateway alarms")
    except Exception as e:
        print(f"   ✗ Error creating API Gateway alarms: {e}")
    
    # Create DynamoDB alarms
    try:
        db_alarms = alarm_manager.create_dynamodb_alarms("RISE-DiagnosisHistory")
        print(f"   ✓ Created {len(db_alarms)} DynamoDB alarms")
    except Exception as e:
        print(f"   ✗ Error creating DynamoDB alarms: {e}")
    
    # 2. Set up Error Tracking
    print("\n2. Setting up Error Tracking...")
    error_tracker = ErrorTracker(region)
    
    # Create log groups for Lambda functions
    function_names = ['rise-image-analysis', 'rise-pest-analysis', 'rise-weather']
    error_tracker.create_log_groups(function_names)
    
    # Create metric filters
    for func_name in function_names:
        error_tracker.create_metric_filters(func_name)
    
    print("   ✓ Error tracking configured")
    
    # 3. Set up Cost Monitoring
    print("\n3. Setting up Cost Monitoring...")
    cost_monitor = CostMonitor(account_id, region)
    
    # Create monthly budget
    try:
        cost_monitor.create_monthly_budget(
            budget_name="RISE-Monthly-Budget",
            amount_usd=1000,
            sns_topic_arn=sns_topic_arn,
            alert_thresholds=[50, 75, 90, 100]
        )
        print("   ✓ Monthly budget created with alerts")
    except Exception as e:
        print(f"   ✗ Error creating budget: {e}")
    
    # 4. Create Monitoring Dashboards
    print("\n4. Creating Monitoring Dashboards...")
    dashboard_manager = MonitoringDashboard(region)
    
    try:
        dashboard_manager.create_all_dashboards()
        print("   ✓ All dashboards created")
    except Exception as e:
        print(f"   ✗ Error creating dashboards: {e}")
    
    print("\n" + "=" * 60)
    print("Monitoring setup complete!")
    print("=" * 60)


def track_metrics_example():
    """Example: Track custom agricultural metrics"""
    
    print("\n" + "=" * 60)
    print("Custom Metrics Tracking Example")
    print("=" * 60)
    
    metrics_tracker = CustomMetricsTracker()
    
    # 1. Track diagnosis accuracy
    print("\n1. Tracking diagnosis accuracy...")
    metrics_tracker.track_diagnosis_accuracy(
        diagnosis_id="diag_12345",
        predicted_disease="Late Blight",
        actual_disease="Late Blight",
        confidence_score=92.5,
        user_feedback="helpful"
    )
    print("   ✓ Diagnosis accuracy tracked")
    
    # 2. Track user engagement
    print("\n2. Tracking user engagement...")
    metrics_tracker.track_user_engagement(
        user_id="user_67890",
        session_duration_seconds=1200,
        features_used=["crop_diagnosis", "weather_alerts", "market_prices"],
        language="hi"
    )
    print("   ✓ User engagement tracked")
    
    # 3. Track yield improvement
    print("\n3. Tracking yield improvement...")
    metrics_tracker.track_yield_improvement(
        user_id="user_67890",
        crop_type="wheat",
        baseline_yield=2.5,
        current_yield=3.2,
        season="rabi_2024"
    )
    print("   ✓ Yield improvement tracked (28% increase)")
    
    # 4. Track cost savings
    print("\n4. Tracking cost savings...")
    metrics_tracker.track_cost_savings(
        user_id="user_67890",
        savings_type="fertilizer",
        amount_saved_inr=5000,
        category="precision_agriculture"
    )
    print("   ✓ Cost savings tracked (₹5,000)")
    
    # 5. Track equipment utilization
    print("\n5. Tracking equipment utilization...")
    metrics_tracker.track_equipment_utilization(
        resource_id="res_tractor_001",
        equipment_type="tractor",
        hours_used=120,
        hours_available=200,
        location="Punjab"
    )
    print("   ✓ Equipment utilization tracked (60%)")
    
    # 6. Track bulk purchase savings
    print("\n6. Tracking bulk purchase savings...")
    metrics_tracker.track_bulk_purchase_savings(
        group_id="group_12345",
        product_type="fertilizer",
        retail_price=1000,
        bulk_price=750,
        quantity=100,
        location="Uttar Pradesh"
    )
    print("   ✓ Bulk purchase savings tracked (25% savings)")
    
    print("\n" + "=" * 60)
    print("Metrics tracking complete!")
    print("=" * 60)


def analyze_errors_example():
    """Example: Analyze errors and trends"""
    
    print("\n" + "=" * 60)
    print("Error Analysis Example")
    print("=" * 60)
    
    error_tracker = ErrorTracker()
    
    # 1. Analyze error trends
    print("\n1. Analyzing error trends...")
    try:
        trends = error_tracker.analyze_error_trends(
            function_name="rise-image-analysis",
            hours=24
        )
        
        print(f"   Function: {trends['function_name']}")
        print(f"   Total errors (24h): {trends['total_errors']}")
        print(f"   Average errors per 5min: {trends['average_errors_per_5min']:.2f}")
        print(f"   Max errors per 5min: {trends['max_errors_per_5min']}")
    except Exception as e:
        print(f"   ✗ Error analyzing trends: {e}")
    
    # 2. Get top errors
    print("\n2. Getting top errors...")
    try:
        top_errors = error_tracker.get_top_errors(
            function_name="rise-image-analysis",
            hours=24,
            limit=5
        )
        
        print(f"   Top {len(top_errors)} errors:")
        for i, error in enumerate(top_errors, 1):
            print(f"   {i}. Count: {error['count']}")
            print(f"      Message: {error['error_message'][:100]}...")
    except Exception as e:
        print(f"   ✗ Error getting top errors: {e}")
    
    print("\n" + "=" * 60)
    print("Error analysis complete!")
    print("=" * 60)


def cost_analysis_example():
    """Example: Analyze costs and get recommendations"""
    
    print("\n" + "=" * 60)
    print("Cost Analysis Example")
    print("=" * 60)
    
    account_id = "123456789012"
    cost_monitor = CostMonitor(account_id)
    
    # 1. Get current month cost
    print("\n1. Getting current month cost...")
    try:
        current_cost = cost_monitor.get_current_month_cost()
        
        print(f"   Total cost: ${current_cost['total_cost_usd']:.2f}")
        print(f"   Period: {current_cost['period']['start']} to {current_cost['period']['end']}")
        print("\n   Service breakdown:")
        for service, cost in sorted(current_cost['service_costs'].items(), 
                                    key=lambda x: x[1], reverse=True)[:5]:
            print(f"   - {service}: ${cost:.2f}")
    except Exception as e:
        print(f"   ✗ Error getting current cost: {e}")
    
    # 2. Get cost forecast
    print("\n2. Getting cost forecast...")
    try:
        forecast = cost_monitor.get_cost_forecast(30)
        
        print(f"   Forecast (30 days): ${forecast['forecast_cost_usd']:.2f}")
        print(f"   Period: {forecast['start_date']} to {forecast['end_date']}")
    except Exception as e:
        print(f"   ✗ Error getting forecast: {e}")
    
    # 3. Get optimization recommendations
    print("\n3. Getting optimization recommendations...")
    try:
        recommendations = cost_monitor.get_cost_optimization_recommendations()
        
        if recommendations:
            print(f"   Found {len(recommendations)} recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"\n   {i}. {rec['service']}")
                print(f"      Current cost: ${rec['current_cost']:.2f}")
                print(f"      Recommendation: {rec['recommendation']}")
                print(f"      Potential savings: {rec['potential_savings_percent']}%")
        else:
            print("   No recommendations at this time")
    except Exception as e:
        print(f"   ✗ Error getting recommendations: {e}")
    
    # 4. Generate comprehensive report
    print("\n4. Generating comprehensive cost report...")
    try:
        report = cost_monitor.generate_cost_report()
        
        print(f"   Report date: {report['report_date']}")
        print(f"   Budget: ${report['budget_amount_usd']:.2f}")
        print(f"   Budget utilization: {report['budget_utilization_percent']:.1f}%")
        print(f"   Current month cost: ${report['current_month_cost']['total_cost_usd']:.2f}")
        print(f"   30-day forecast: ${report['forecast_next_30_days']['forecast_cost_usd']:.2f}")
    except Exception as e:
        print(f"   ✗ Error generating report: {e}")
    
    print("\n" + "=" * 60)
    print("Cost analysis complete!")
    print("=" * 60)


def main():
    """Run all monitoring examples"""
    
    print("\n" + "=" * 60)
    print("RISE MONITORING SYSTEM - EXAMPLES")
    print("=" * 60)
    
    # Note: These examples require AWS credentials and permissions
    print("\nNote: These examples require:")
    print("- AWS credentials configured")
    print("- Appropriate IAM permissions")
    print("- Existing Lambda functions and resources")
    print("\nRunning in demo mode...\n")
    
    # Run examples
    try:
        setup_monitoring_example()
    except Exception as e:
        print(f"Setup example error: {e}")
    
    try:
        track_metrics_example()
    except Exception as e:
        print(f"Metrics example error: {e}")
    
    try:
        analyze_errors_example()
    except Exception as e:
        print(f"Error analysis example error: {e}")
    
    try:
        cost_analysis_example()
    except Exception as e:
        print(f"Cost analysis example error: {e}")
    
    print("\n" + "=" * 60)
    print("All examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
