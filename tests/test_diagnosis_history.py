"""
Tests for Diagnosis History and Tracking Functionality
"""

import pytest
import boto3
from moto import mock_dynamodb, mock_s3
import json
from datetime import datetime, timedelta
from decimal import Decimal
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.diagnosis_history_tools import DiagnosisHistoryTools
from tools.diagnosis_history_lambda import DiagnosisHistoryService, lambda_handler


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for testing"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture
def dynamodb_tables(aws_credentials):
    """Create mock DynamoDB tables"""
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create DiagnosisHistory table
        diagnosis_table = dynamodb.create_table(
            TableName='RISE-DiagnosisHistory',
            KeySchema=[
                {'AttributeName': 'diagnosis_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'diagnosis_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'created_timestamp', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserDiagnosisIndex',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )
        
        # Create PestDiagnosisHistory table
        pest_table = dynamodb.create_table(
            TableName='RISE-PestDiagnosisHistory',
            KeySchema=[
                {'AttributeName': 'diagnosis_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'diagnosis_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'created_timestamp', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserPestDiagnosisIndex',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )
        
        yield dynamodb


@pytest.fixture
def sample_diagnoses(dynamodb_tables):
    """Create sample diagnosis records"""
    diagnosis_table = dynamodb_tables.Table('RISE-DiagnosisHistory')
    pest_table = dynamodb_tables.Table('RISE-PestDiagnosisHistory')
    
    # Create disease diagnoses
    base_timestamp = int(datetime.now().timestamp())
    
    disease_diagnoses = [
        {
            'diagnosis_id': 'diag_001',
            'user_id': 'farmer_123',
            'crop_type': 'wheat',
            'severity': 'high',
            'confidence_score': Decimal('0.85'),
            'diseases': ['Leaf Rust', 'Powdery Mildew'],
            'follow_up_status': 'pending',
            'created_timestamp': base_timestamp - 86400 * 7,  # 7 days ago
            'diagnosis_result': {
                'full_analysis': 'Detailed analysis of wheat diseases',
                'treatment_recommendations': [
                    {'type': 'chemical', 'description': 'Apply fungicide'}
                ],
                'preventive_measures': ['Crop rotation', 'Proper spacing']
            }
        },
        {
            'diagnosis_id': 'diag_002',
            'user_id': 'farmer_123',
            'crop_type': 'wheat',
            'severity': 'medium',
            'confidence_score': Decimal('0.90'),
            'diseases': ['Leaf Rust'],
            'follow_up_status': 'treatment_applied',
            'created_timestamp': base_timestamp - 86400 * 3,  # 3 days ago
            'diagnosis_result': {
                'full_analysis': 'Follow-up analysis showing improvement',
                'treatment_recommendations': [
                    {'type': 'chemical', 'description': 'Continue treatment'}
                ],
                'preventive_measures': ['Monitor regularly']
            }
        },
        {
            'diagnosis_id': 'diag_003',
            'user_id': 'farmer_123',
            'crop_type': 'wheat',
            'severity': 'low',
            'confidence_score': Decimal('0.92'),
            'diseases': ['Healthy - No disease detected'],
            'follow_up_status': 'resolved',
            'created_timestamp': base_timestamp,  # Today
            'diagnosis_result': {
                'full_analysis': 'Crop is healthy, treatment successful',
                'treatment_recommendations': [],
                'preventive_measures': ['Continue good practices']
            }
        }
    ]
    
    for diag in disease_diagnoses:
        diagnosis_table.put_item(Item=diag)
    
    # Create pest diagnoses
    pest_diagnoses = [
        {
            'diagnosis_id': 'pest_001',
            'user_id': 'farmer_123',
            'crop_type': 'rice',
            'severity': 'medium',
            'confidence_score': Decimal('0.88'),
            'pests': ['Brown Planthopper'],
            'follow_up_status': 'pending',
            'created_timestamp': base_timestamp - 86400 * 5,
            'diagnosis_result': {
                'full_analysis': 'Pest infestation detected',
                'treatment_recommendations': [
                    {'type': 'biological', 'description': 'Use natural predators'}
                ],
                'preventive_measures': ['Water management']
            }
        }
    ]
    
    for diag in pest_diagnoses:
        pest_table.put_item(Item=diag)
    
    return disease_diagnoses + pest_diagnoses


class TestDiagnosisHistoryTools:
    """Test DiagnosisHistoryTools class"""
    
    def test_get_diagnosis_history(self, dynamodb_tables, sample_diagnoses):
        """Test retrieving diagnosis history"""
        tools = DiagnosisHistoryTools(region='us-east-1')
        
        history = tools.get_diagnosis_history(user_id='farmer_123', limit=10)
        
        assert len(history) == 4  # 3 disease + 1 pest
        assert all('diagnosis_type' in diag for diag in history)
        
        # Check sorting (most recent first)
        timestamps = [diag['created_timestamp'] for diag in history]
        assert timestamps == sorted(timestamps, reverse=True)
    
    def test_get_diagnosis_history_with_filters(self, dynamodb_tables, sample_diagnoses):
        """Test filtering diagnosis history"""
        tools = DiagnosisHistoryTools(region='us-east-1')
        
        # Filter by severity
        high_severity = tools.get_diagnosis_history(
            user_id='farmer_123',
            filters={'severity': 'high'}
        )
        assert len(high_severity) == 1
        assert high_severity[0]['severity'] == 'high'
        
        # Filter by crop type
        wheat_diagnoses = tools.get_diagnosis_history(
            user_id='farmer_123',
            filters={'crop_type': 'wheat'}
        )
        assert len(wheat_diagnoses) == 3
        assert all('wheat' in diag['crop_type'] for diag in wheat_diagnoses)
        
        # Filter by follow-up status
        resolved = tools.get_diagnosis_history(
            user_id='farmer_123',
            filters={'follow_up_status': 'resolved'}
        )
        assert len(resolved) == 1
        assert resolved[0]['follow_up_status'] == 'resolved'
        
        # Filter by diagnosis type
        pests = tools.get_diagnosis_history(
            user_id='farmer_123',
            filters={'diagnosis_type': 'pest'}
        )
        assert len(pests) == 1
        assert pests[0]['diagnosis_type'] == 'pest'
    
    def test_update_follow_up_status(self, dynamodb_tables, sample_diagnoses):
        """Test updating follow-up status"""
        tools = DiagnosisHistoryTools(region='us-east-1')
        
        success = tools.update_follow_up_status(
            diagnosis_id='diag_001',
            status='improving',
            notes='Treatment showing positive results',
            diagnosis_type='disease'
        )
        
        assert success is True
        
        # Verify update
        diagnosis = tools.get_diagnosis_by_id('diag_001', 'disease')
        assert diagnosis['follow_up_status'] == 'improving'
        assert diagnosis['follow_up_notes'] == 'Treatment showing positive results'
        assert 'updated_timestamp' in diagnosis
    
    def test_get_diagnosis_by_id(self, dynamodb_tables, sample_diagnoses):
        """Test retrieving specific diagnosis"""
        tools = DiagnosisHistoryTools(region='us-east-1')
        
        diagnosis = tools.get_diagnosis_by_id('diag_001', 'disease')
        
        assert diagnosis is not None
        assert diagnosis['diagnosis_id'] == 'diag_001'
        assert diagnosis['user_id'] == 'farmer_123'
        assert diagnosis['crop_type'] == 'wheat'
    
    def test_compare_diagnoses(self, dynamodb_tables, sample_diagnoses):
        """Test diagnosis comparison for treatment progress"""
        tools = DiagnosisHistoryTools(region='us-east-1')
        
        comparison = tools.compare_diagnoses(['diag_001', 'diag_002', 'diag_003'])
        
        assert comparison['success'] is True
        assert comparison['count'] == 3
        
        progress = comparison['progress']
        assert progress['status'] == 'improving'  # high -> medium -> low
        assert progress['severity_change'] > 0  # Positive change = improvement
        assert progress['total_diagnoses'] == 3
        assert progress['days_elapsed'] > 0
    
    def test_compare_diagnoses_worsening(self, dynamodb_tables):
        """Test diagnosis comparison showing worsening condition"""
        tools = DiagnosisHistoryTools(region='us-east-1')
        
        # Create diagnoses showing worsening
        diagnosis_table = dynamodb_tables.Table('RISE-DiagnosisHistory')
        base_timestamp = int(datetime.now().timestamp())
        
        diagnoses = [
            {
                'diagnosis_id': 'diag_worse_1',
                'user_id': 'farmer_456',
                'crop_type': 'rice',
                'severity': 'low',
                'confidence_score': Decimal('0.85'),
                'diseases': ['Minor issue'],
                'follow_up_status': 'pending',
                'created_timestamp': base_timestamp - 86400 * 5,
                'diagnosis_result': {}
            },
            {
                'diagnosis_id': 'diag_worse_2',
                'user_id': 'farmer_456',
                'crop_type': 'rice',
                'severity': 'high',
                'confidence_score': Decimal('0.90'),
                'diseases': ['Severe issue'],
                'follow_up_status': 'worsened',
                'created_timestamp': base_timestamp,
                'diagnosis_result': {}
            }
        ]
        
        for diag in diagnoses:
            diagnosis_table.put_item(Item=diag)
        
        comparison = tools.compare_diagnoses(['diag_worse_1', 'diag_worse_2'])
        
        assert comparison['success'] is True
        progress = comparison['progress']
        assert progress['status'] == 'worsening'
        assert progress['severity_change'] < 0  # Negative change = worsening
    
    def test_generate_report(self, dynamodb_tables, sample_diagnoses):
        """Test report generation"""
        tools = DiagnosisHistoryTools(region='us-east-1')
        
        report = tools.generate_report('diag_001', 'disease')
        
        assert report is not None
        assert 'RISE - Crop Diagnosis Report' in report
        assert 'diag_001' in report
        assert 'wheat' in report
        assert 'high' in report.lower()
        assert 'Leaf Rust' in report
    
    def test_get_statistics(self, dynamodb_tables, sample_diagnoses):
        """Test statistics calculation"""
        tools = DiagnosisHistoryTools(region='us-east-1')
        
        stats = tools.get_statistics('farmer_123')
        
        assert stats['total_diagnoses'] == 4
        assert 'severity_distribution' in stats
        assert 'follow_up_status_distribution' in stats
        assert 'diagnosis_type_distribution' in stats
        
        # Check distributions
        assert stats['severity_distribution']['high'] == 1
        assert stats['severity_distribution']['medium'] == 2  # 1 disease + 1 pest
        assert stats['severity_distribution']['low'] == 1
        
        assert stats['diagnosis_type_distribution']['disease'] == 3
        assert stats['diagnosis_type_distribution']['pest'] == 1


class TestDiagnosisHistoryService:
    """Test DiagnosisHistoryService class (Lambda function logic)"""
    
    def test_get_diagnosis_history_with_sorting(self, dynamodb_tables, sample_diagnoses):
        """Test diagnosis history retrieval with sorting"""
        service = DiagnosisHistoryService(region='us-east-1')
        
        # Sort by confidence score
        result = service.get_diagnosis_history(
            user_id='farmer_123',
            sort_by='confidence_score',
            sort_order='desc'
        )
        
        assert result['success'] is True
        assert result['count'] > 0
        
        # Verify sorting
        scores = [diag['confidence_score'] for diag in result['diagnoses']]
        assert scores == sorted(scores, reverse=True)
    
    def test_get_diagnosis_history_with_filters_and_stats(self, dynamodb_tables, sample_diagnoses):
        """Test diagnosis history with filters and statistics"""
        service = DiagnosisHistoryService(region='us-east-1')
        
        result = service.get_diagnosis_history(
            user_id='farmer_123',
            filters={'severity': 'high'}
        )
        
        assert result['success'] is True
        assert 'statistics' in result
        assert result['statistics']['total_diagnoses'] == 1
    
    def test_update_follow_up_status_service(self, dynamodb_tables, sample_diagnoses):
        """Test follow-up status update via service"""
        service = DiagnosisHistoryService(region='us-east-1')
        
        result = service.update_follow_up_status(
            diagnosis_id='diag_001',
            status='improving',
            notes='Showing improvement',
            diagnosis_type='disease'
        )
        
        assert result['success'] is True
        assert result['diagnosis_id'] == 'diag_001'
        assert result['status'] == 'improving'
    
    def test_get_diagnosis_comparison_service(self, dynamodb_tables, sample_diagnoses):
        """Test diagnosis comparison via service"""
        service = DiagnosisHistoryService(region='us-east-1')
        
        result = service.get_diagnosis_comparison(
            diagnosis_ids=['diag_001', 'diag_002', 'diag_003']
        )
        
        assert result['success'] is True
        assert 'progress' in result
        assert 'timeline' in result
        assert len(result['timeline']) == 3
    
    def test_generate_diagnosis_report_service(self, dynamodb_tables, sample_diagnoses):
        """Test report generation via service"""
        service = DiagnosisHistoryService(region='us-east-1')
        
        result = service.generate_diagnosis_report(
            diagnosis_id='diag_001',
            diagnosis_type='disease',
            include_images=False
        )
        
        assert result['success'] is True
        assert 'report' in result
        
        report = result['report']
        assert report['diagnosis_id'] == 'diag_001'
        assert report['crop_type'] == 'wheat'
        assert report['severity'] == 'high'


class TestLambdaHandler:
    """Test Lambda handler function"""
    
    def test_lambda_get_history(self, dynamodb_tables, sample_diagnoses):
        """Test Lambda handler for get_history action"""
        event = {
            'action': 'get_history',
            'user_id': 'farmer_123',
            'limit': 10
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['count'] > 0
    
    def test_lambda_update_status(self, dynamodb_tables, sample_diagnoses):
        """Test Lambda handler for update_status action"""
        event = {
            'action': 'update_status',
            'diagnosis_id': 'diag_001',
            'status': 'improving',
            'notes': 'Treatment working well',
            'diagnosis_type': 'disease'
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
    
    def test_lambda_compare(self, dynamodb_tables, sample_diagnoses):
        """Test Lambda handler for compare action"""
        event = {
            'action': 'compare',
            'diagnosis_ids': ['diag_001', 'diag_002', 'diag_003']
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'progress' in body
    
    def test_lambda_generate_report(self, dynamodb_tables, sample_diagnoses):
        """Test Lambda handler for generate_report action"""
        event = {
            'action': 'generate_report',
            'diagnosis_id': 'diag_001',
            'diagnosis_type': 'disease'
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'report' in body
    
    def test_lambda_unknown_action(self, dynamodb_tables):
        """Test Lambda handler with unknown action"""
        event = {
            'action': 'unknown_action',
            'user_id': 'farmer_123'
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'Unknown action' in body['error']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
