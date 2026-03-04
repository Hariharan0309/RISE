"""
RISE EventBridge Rules for Resource Alert System
Automated scheduling for unused equipment monitoring
"""

from aws_cdk import (
    Duration,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_,
    aws_iam as iam,
)
from constructs import Construct


class ResourceAlertRules(Construct):
    """EventBridge rules for resource alert automation"""
    
    def __init__(self, scope: Construct, construct_id: str, 
                 alert_lambda: lambda_.Function, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Daily unused equipment check (runs at 9 AM IST)
        self.daily_check_rule = events.Rule(
            self, "DailyUnusedEquipmentCheck",
            rule_name="RISE-DailyUnusedEquipmentCheck",
            description="Daily check for unused equipment (9 AM IST)",
            schedule=events.Schedule.cron(
                minute="30",
                hour="3",  # 9 AM IST = 3:30 AM UTC
                day="*",
                month="*",
                year="*"
            ),
            enabled=True
        )
        
        # Add Lambda target
        self.daily_check_rule.add_target(
            targets.LambdaFunction(
                alert_lambda,
                event=events.RuleTargetInput.from_object({
                    "action": "send_batch_alerts",
                    "days_threshold": 30,
                    "source": "eventbridge-daily"
                })
            )
        )
        
        # Weekly comprehensive check (runs every Monday at 10 AM IST)
        self.weekly_check_rule = events.Rule(
            self, "WeeklyUnusedEquipmentCheck",
            rule_name="RISE-WeeklyUnusedEquipmentCheck",
            description="Weekly comprehensive unused equipment check (Monday 10 AM IST)",
            schedule=events.Schedule.cron(
                minute="30",
                hour="4",  # 10 AM IST = 4:30 AM UTC
                week_day="MON",
                month="*",
                year="*"
            ),
            enabled=True
        )
        
        self.weekly_check_rule.add_target(
            targets.LambdaFunction(
                alert_lambda,
                event=events.RuleTargetInput.from_object({
                    "action": "send_batch_alerts",
                    "days_threshold": 30,
                    "source": "eventbridge-weekly"
                })
            )
        )
        
        # Monthly deep analysis (runs on 1st of every month at 11 AM IST)
        self.monthly_analysis_rule = events.Rule(
            self, "MonthlyResourceAnalysis",
            rule_name="RISE-MonthlyResourceAnalysis",
            description="Monthly resource utilization analysis (1st of month, 11 AM IST)",
            schedule=events.Schedule.cron(
                minute="30",
                hour="5",  # 11 AM IST = 5:30 AM UTC
                day="1",
                month="*",
                year="*"
            ),
            enabled=True
        )
        
        self.monthly_analysis_rule.add_target(
            targets.LambdaFunction(
                alert_lambda,
                event=events.RuleTargetInput.from_object({
                    "action": "send_batch_alerts",
                    "days_threshold": 60,  # 60 days for monthly check
                    "source": "eventbridge-monthly"
                })
            )
        )
        
        # Seasonal equipment check (runs at start of farming seasons)
        # Kharif season (June-July) and Rabi season (October-November)
        self.seasonal_check_rule = events.Rule(
            self, "SeasonalEquipmentCheck",
            rule_name="RISE-SeasonalEquipmentCheck",
            description="Seasonal equipment availability check",
            schedule=events.Schedule.cron(
                minute="0",
                hour="4",  # 9:30 AM IST
                day="1,15",  # 1st and 15th of month
                month="6,7,10,11",  # Kharif and Rabi seasons
                year="*"
            ),
            enabled=True
        )
        
        self.seasonal_check_rule.add_target(
            targets.LambdaFunction(
                alert_lambda,
                event=events.RuleTargetInput.from_object({
                    "action": "send_batch_alerts",
                    "days_threshold": 15,  # More frequent during seasons
                    "source": "eventbridge-seasonal"
                })
            )
        )
        
        # Grant Lambda permissions to be invoked by EventBridge
        alert_lambda.add_permission(
            "AllowEventBridgeInvoke",
            principal=iam.ServicePrincipal("events.amazonaws.com"),
            action="lambda:InvokeFunction"
        )


def create_alert_rules(scope: Construct, alert_lambda: lambda_.Function) -> ResourceAlertRules:
    """
    Factory function to create resource alert EventBridge rules
    
    Args:
        scope: CDK construct scope
        alert_lambda: Lambda function for alerts
    
    Returns:
        ResourceAlertRules instance
    """
    return ResourceAlertRules(scope, "ResourceAlertRules", alert_lambda=alert_lambda)
