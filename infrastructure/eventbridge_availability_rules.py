"""
RISE EventBridge Rules for Resource Availability Alerts
Configure automated alert triggers using AWS EventBridge
"""

import boto3
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AvailabilityAlertRules:
    """EventBridge rules for resource availability alerts"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize EventBridge rules manager
        
        Args:
            region: AWS region
        """
        self.region = region
        self.eventbridge = boto3.client('events', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        
        logger.info(f"EventBridge rules manager initialized in region {region}")
    
    def create_equipment_availability_rule(self,
                                          rule_name: str = "rise-equipment-availability-alerts",
                                          schedule: str = "rate(2 hours)") -> Dict[str, Any]:
        """
        Create rule for equipment availability alerts
        
        Args:
            rule_name: EventBridge rule name
            schedule: Schedule expression (rate or cron)
        
        Returns:
            Dict with rule creation result
        """
        try:
            # Create rule
            response = self.eventbridge.put_rule(
                Name=rule_name,
                Description="Trigger equipment availability alerts every 2 hours",
                ScheduleExpression=schedule,
                State='ENABLED'
            )
            
            # Add Lambda target
            lambda_arn = self._get_lambda_arn('availability-alert-lambda')
            
            self.eventbridge.put_targets(
                Rule=rule_name,
                Targets=[{
                    'Id': '1',
                    'Arn': lambda_arn,
                    'Input': json.dumps({
                        'action': 'scan_new_equipment',
                        'radius_km': 25
                    })
                }]
            )
            
            # Add Lambda permission
            self._add_lambda_permission(
                lambda_arn,
                rule_name,
                response['RuleArn']
            )
            
            logger.info(f"Equipment availability rule created: {rule_name}")
            
            return {
                'success': True,
                'rule_name': rule_name,
                'rule_arn': response['RuleArn'],
                'schedule': schedule
            }
        
        except Exception as e:
            logger.error(f"Create equipment availability rule error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_buying_group_alert_rule(self,
                                      rule_name: str = "rise-buying-group-alerts",
                                      schedule: str = "rate(6 hours)") -> Dict[str, Any]:
        """
        Create rule for bulk buying opportunity alerts
        
        Args:
            rule_name: EventBridge rule name
            schedule: Schedule expression
        
        Returns:
            Dict with rule creation result
        """
        try:
            # Create rule
            response = self.eventbridge.put_rule(
                Name=rule_name,
                Description="Trigger bulk buying opportunity alerts every 6 hours",
                ScheduleExpression=schedule,
                State='ENABLED'
            )
            
            # Add Lambda target
            lambda_arn = self._get_lambda_arn('availability-alert-lambda')
            
            self.eventbridge.put_targets(
                Rule=rule_name,
                Targets=[{
                    'Id': '1',
                    'Arn': lambda_arn,
                    'Input': json.dumps({
                        'action': 'scan_buying_groups',
                        'radius_km': 25
                    })
                }]
            )
            
            # Add Lambda permission
            self._add_lambda_permission(
                lambda_arn,
                rule_name,
                response['RuleArn']
            )
            
            logger.info(f"Buying group alert rule created: {rule_name}")
            
            return {
                'success': True,
                'rule_name': rule_name,
                'rule_arn': response['RuleArn'],
                'schedule': schedule
            }
        
        except Exception as e:
            logger.error(f"Create buying group alert rule error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_seasonal_demand_rule(self,
                                   rule_name: str = "rise-seasonal-demand-alerts",
                                   schedule: str = "rate(1 day)") -> Dict[str, Any]:
        """
        Create rule for seasonal demand prediction alerts
        
        Args:
            rule_name: EventBridge rule name
            schedule: Schedule expression
        
        Returns:
            Dict with rule creation result
        """
        try:
            # Create rule
            response = self.eventbridge.put_rule(
                Name=rule_name,
                Description="Trigger seasonal demand predictions daily",
                ScheduleExpression=schedule,
                State='ENABLED'
            )
            
            # Add Lambda target
            lambda_arn = self._get_lambda_arn('availability-alert-lambda')
            
            self.eventbridge.put_targets(
                Rule=rule_name,
                Targets=[{
                    'Id': '1',
                    'Arn': lambda_arn,
                    'Input': json.dumps({
                        'action': 'generate_seasonal_predictions',
                        'advance_notice_days': 30
                    })
                }]
            )
            
            # Add Lambda permission
            self._add_lambda_permission(
                lambda_arn,
                rule_name,
                response['RuleArn']
            )
            
            logger.info(f"Seasonal demand rule created: {rule_name}")
            
            return {
                'success': True,
                'rule_name': rule_name,
                'rule_arn': response['RuleArn'],
                'schedule': schedule
            }
        
        except Exception as e:
            logger.error(f"Create seasonal demand rule error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_advance_booking_reminder_rule(self,
                                            rule_name: str = "rise-advance-booking-reminders",
                                            schedule: str = "rate(12 hours)") -> Dict[str, Any]:
        """
        Create rule for advance booking reminders
        
        Args:
            rule_name: EventBridge rule name
            schedule: Schedule expression
        
        Returns:
            Dict with rule creation result
        """
        try:
            # Create rule
            response = self.eventbridge.put_rule(
                Name=rule_name,
                Description="Send reminders for upcoming advance bookings",
                ScheduleExpression=schedule,
                State='ENABLED'
            )
            
            # Add Lambda target
            lambda_arn = self._get_lambda_arn('availability-alert-lambda')
            
            self.eventbridge.put_targets(
                Rule=rule_name,
                Targets=[{
                    'Id': '1',
                    'Arn': lambda_arn,
                    'Input': json.dumps({
                        'action': 'send_booking_reminders',
                        'reminder_days_before': 7
                    })
                }]
            )
            
            # Add Lambda permission
            self._add_lambda_permission(
                lambda_arn,
                rule_name,
                response['RuleArn']
            )
            
            logger.info(f"Advance booking reminder rule created: {rule_name}")
            
            return {
                'success': True,
                'rule_name': rule_name,
                'rule_arn': response['RuleArn'],
                'schedule': schedule
            }
        
        except Exception as e:
            logger.error(f"Create advance booking reminder rule error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def setup_all_rules(self) -> Dict[str, Any]:
        """
        Set up all availability alert rules
        
        Returns:
            Dict with setup results
        """
        results = {
            'equipment_availability': self.create_equipment_availability_rule(),
            'buying_group_alerts': self.create_buying_group_alert_rule(),
            'seasonal_demand': self.create_seasonal_demand_rule(),
            'advance_booking_reminders': self.create_advance_booking_reminder_rule()
        }
        
        success_count = sum(1 for r in results.values() if r.get('success'))
        
        logger.info(f"Setup complete: {success_count}/{len(results)} rules created successfully")
        
        return {
            'success': success_count == len(results),
            'results': results,
            'total_rules': len(results),
            'successful_rules': success_count
        }
    
    def delete_rule(self, rule_name: str) -> Dict[str, Any]:
        """
        Delete an EventBridge rule
        
        Args:
            rule_name: Rule name to delete
        
        Returns:
            Dict with deletion result
        """
        try:
            # Remove targets first
            targets_response = self.eventbridge.list_targets_by_rule(Rule=rule_name)
            target_ids = [target['Id'] for target in targets_response.get('Targets', [])]
            
            if target_ids:
                self.eventbridge.remove_targets(
                    Rule=rule_name,
                    Ids=target_ids
                )
            
            # Delete rule
            self.eventbridge.delete_rule(Name=rule_name)
            
            logger.info(f"Rule deleted: {rule_name}")
            
            return {
                'success': True,
                'rule_name': rule_name,
                'message': 'Rule deleted successfully'
            }
        
        except Exception as e:
            logger.error(f"Delete rule error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_rules(self) -> Dict[str, Any]:
        """
        List all RISE availability alert rules
        
        Returns:
            Dict with rules list
        """
        try:
            response = self.eventbridge.list_rules(
                NamePrefix='rise-'
            )
            
            rules = response.get('Rules', [])
            
            return {
                'success': True,
                'count': len(rules),
                'rules': [{
                    'name': rule['Name'],
                    'state': rule['State'],
                    'schedule': rule.get('ScheduleExpression', 'N/A'),
                    'description': rule.get('Description', '')
                } for rule in rules]
            }
        
        except Exception as e:
            logger.error(f"List rules error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_lambda_arn(self, function_name: str) -> str:
        """Get Lambda function ARN"""
        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            return response['Configuration']['FunctionArn']
        except Exception as e:
            logger.warning(f"Get Lambda ARN error: {e}")
            # Return placeholder ARN for development
            return f"arn:aws:lambda:{self.region}:123456789012:function:{function_name}"
    
    def _add_lambda_permission(self,
                              lambda_arn: str,
                              rule_name: str,
                              rule_arn: str) -> None:
        """Add permission for EventBridge to invoke Lambda"""
        try:
            function_name = lambda_arn.split(':')[-1]
            
            self.lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=f"{rule_name}-permission",
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
                SourceArn=rule_arn
            )
        except self.lambda_client.exceptions.ResourceConflictException:
            # Permission already exists
            pass
        except Exception as e:
            logger.warning(f"Add Lambda permission error: {e}")


def setup_availability_alert_rules(region: str = "us-east-1") -> Dict[str, Any]:
    """
    Convenience function to set up all availability alert rules
    
    Args:
        region: AWS region
    
    Returns:
        Dict with setup results
    """
    rules_manager = AvailabilityAlertRules(region=region)
    return rules_manager.setup_all_rules()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set up rules
    print("Setting up availability alert rules...")
    result = setup_availability_alert_rules()
    
    if result['success']:
        print(f"✅ All {result['total_rules']} rules created successfully!")
    else:
        print(f"⚠️ {result['successful_rules']}/{result['total_rules']} rules created")
        print("Results:", json.dumps(result['results'], indent=2))
