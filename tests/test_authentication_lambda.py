"""
Unit Tests for Authentication and Authorization Logic in Lambda Functions
Tests user authentication, session management, and access control
"""

import unittest
import json
import jwt
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import boto3
from moto import mock_dynamodb, mock_cognito_idp
import os


class MockAuthenticationLambda:
    """Mock authentication Lambda function for testing"""
    
    def __init__(self):
        self.cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.user_pool_id = 'us-east-1_test123'
        self.client_id = 'test_client_id'
        self.jwt_secret = 'test_secret_key'
    
    def authenticate_user(self, username, password):
        """Authenticate user with Cognito"""
        try:
            response = self.cognito_client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            
            return {
                'success': True,
                'access_token': response['AuthenticationResult']['AccessToken'],
                'id_token': response['AuthenticationResult']['IdToken'],
                'refresh_token': response['AuthenticationResult']['RefreshToken'],
                'expires_in': response['AuthenticationResult']['ExpiresIn']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_token(self, token):
        """Validate JWT token"""
        try:
            # In real implementation, would validate with Cognito
            # For testing, use simple JWT validation
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Check expiration
            if payload.get('exp', 0) < time.time():
                return {'valid': False, 'error': 'Token expired'}
            
            return {
                'valid': True,
                'user_id': payload.get('sub'),
                'username': payload.get('username'),
                'groups': payload.get('cognito:groups', [])
            }
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'valid': False, 'error': 'Invalid token'}
    
    def check_user_permissions(self, user_id, resource, action):
        """Check user permissions for resource access"""
        # Mock permission checking logic
        permissions = {
            'farmer': ['read_own_data', 'write_own_data', 'upload_images'],
            'expert': ['read_own_data', 'write_own_data', 'read_all_data', 'provide_advice'],
            'admin': ['read_all_data', 'write_all_data', 'manage_users', 'system_admin']
        }
        
        # Get user role from DynamoDB (mocked)
        try:
            table = self.dynamodb.Table('RISE-UserProfiles')
            response = table.get_item(Key={'user_id': user_id})
            
            if 'Item' not in response:
                return {'authorized': False, 'error': 'User not found'}
            
            user_role = response['Item'].get('role', 'farmer')
            user_permissions = permissions.get(user_role, [])
            
            required_permission = f"{action}_{resource}"
            
            return {
                'authorized': required_permission in user_permissions or 'admin' in user_permissions,
                'user_role': user_role,
                'permissions': user_permissions
            }
        except Exception as e:
            return {'authorized': False, 'error': str(e)}
    
    def create_session(self, user_id, device_info=None):
        """Create user session"""
        session_id = f"sess_{int(time.time())}_{user_id}"
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'created_at': int(time.time()),
            'expires_at': int(time.time()) + 3600,  # 1 hour
            'device_info': device_info or {},
            'active': True
        }
        
        try:
            table = self.dynamodb.Table('RISE-UserSessions')
            table.put_item(Item=session_data)
            
            return {
                'success': True,
                'session_id': session_id,
                'expires_at': session_data['expires_at']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_session(self, session_id):
        """Validate user session"""
        try:
            table = self.dynamodb.Table('RISE-UserSessions')
            response = table.get_item(Key={'session_id': session_id})
            
            if 'Item' not in response:
                return {'valid': False, 'error': 'Session not found'}
            
            session = response['Item']
            
            # Check if session is active and not expired
            if not session.get('active', False):
                return {'valid': False, 'error': 'Session inactive'}
            
            if session.get('expires_at', 0) < time.time():
                return {'valid': False, 'error': 'Session expired'}
            
            return {
                'valid': True,
                'user_id': session['user_id'],
                'created_at': session['created_at'],
                'expires_at': session['expires_at']
            }
        except Exception as e:
            return {'valid': False, 'error': str(e)}


class TestAuthenticationLambda(unittest.TestCase):
    """Test cases for authentication Lambda functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.auth_lambda = MockAuthenticationLambda()
        self.test_user_id = 'test_farmer_001'
        self.test_username = 'test_farmer'
        self.test_password = 'TestPassword123!'
    
    @mock_cognito_idp
    def test_successful_authentication(self):
        """Test successful user authentication"""
        # Mock Cognito response
        with patch.object(self.auth_lambda.cognito_client, 'admin_initiate_auth') as mock_auth:
            mock_auth.return_value = {
                'AuthenticationResult': {
                    'AccessToken': 'mock_access_token',
                    'IdToken': 'mock_id_token',
                    'RefreshToken': 'mock_refresh_token',
                    'ExpiresIn': 3600
                }
            }
            
            result = self.auth_lambda.authenticate_user(self.test_username, self.test_password)
            
            self.assertTrue(result['success'])
            self.assertIn('access_token', result)
            self.assertIn('id_token', result)
            self.assertIn('refresh_token', result)
            self.assertEqual(result['expires_in'], 3600)
    
    @mock_cognito_idp
    def test_failed_authentication(self):
        """Test failed authentication with invalid credentials"""
        with patch.object(self.auth_lambda.cognito_client, 'admin_initiate_auth') as mock_auth:
            mock_auth.side_effect = Exception('Invalid credentials')
            
            result = self.auth_lambda.authenticate_user(self.test_username, 'wrong_password')
            
            self.assertFalse(result['success'])
            self.assertIn('error', result)
    
    def test_valid_token_validation(self):
        """Test validation of valid JWT token"""
        # Create a test token
        payload = {
            'sub': self.test_user_id,
            'username': self.test_username,
            'exp': int(time.time()) + 3600,  # Expires in 1 hour
            'cognito:groups': ['farmers']
        }
        
        token = jwt.encode(payload, self.auth_lambda.jwt_secret, algorithm='HS256')
        
        result = self.auth_lambda.validate_token(token)
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['user_id'], self.test_user_id)
        self.assertEqual(result['username'], self.test_username)
        self.assertIn('farmers', result['groups'])
    
    def test_expired_token_validation(self):
        """Test validation of expired JWT token"""
        # Create an expired token
        payload = {
            'sub': self.test_user_id,
            'username': self.test_username,
            'exp': int(time.time()) - 3600,  # Expired 1 hour ago
        }
        
        token = jwt.encode(payload, self.auth_lambda.jwt_secret, algorithm='HS256')
        
        result = self.auth_lambda.validate_token(token)
        
        self.assertFalse(result['valid'])
        self.assertIn('expired', result['error'].lower())
    
    def test_invalid_token_validation(self):
        """Test validation of invalid JWT token"""
        invalid_token = 'invalid.jwt.token'
        
        result = self.auth_lambda.validate_token(invalid_token)
        
        self.assertFalse(result['valid'])
        self.assertIn('invalid', result['error'].lower())
    
    @mock_dynamodb
    def test_user_permissions_farmer(self):
        """Test permission checking for farmer role"""
        # Create mock DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='RISE-UserProfiles',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Add test user
        table.put_item(Item={
            'user_id': self.test_user_id,
            'role': 'farmer',
            'name': 'Test Farmer'
        })
        
        # Test farmer permissions
        result = self.auth_lambda.check_user_permissions(self.test_user_id, 'own_data', 'read')
        self.assertTrue(result['authorized'])
        self.assertEqual(result['user_role'], 'farmer')
        
        # Test unauthorized action
        result = self.auth_lambda.check_user_permissions(self.test_user_id, 'all_data', 'read')
        self.assertFalse(result['authorized'])
    
    @mock_dynamodb
    def test_user_permissions_expert(self):
        """Test permission checking for expert role"""
        # Create mock DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='RISE-UserProfiles',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Add test expert user
        table.put_item(Item={
            'user_id': 'expert_001',
            'role': 'expert',
            'name': 'Test Expert'
        })
        
        # Test expert permissions
        result = self.auth_lambda.check_user_permissions('expert_001', 'all_data', 'read')
        self.assertTrue(result['authorized'])
        self.assertEqual(result['user_role'], 'expert')
        
        # Test unauthorized action for expert
        result = self.auth_lambda.check_user_permissions('expert_001', 'users', 'manage')
        self.assertFalse(result['authorized'])
    
    @mock_dynamodb
    def test_user_permissions_admin(self):
        """Test permission checking for admin role"""
        # Create mock DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='RISE-UserProfiles',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Add test admin user
        table.put_item(Item={
            'user_id': 'admin_001',
            'role': 'admin',
            'name': 'Test Admin'
        })
        
        # Test admin permissions (should have access to everything)
        result = self.auth_lambda.check_user_permissions('admin_001', 'users', 'manage')
        self.assertTrue(result['authorized'])
        self.assertEqual(result['user_role'], 'admin')
        
        result = self.auth_lambda.check_user_permissions('admin_001', 'all_data', 'write')
        self.assertTrue(result['authorized'])
    
    @mock_dynamodb
    def test_user_not_found_permissions(self):
        """Test permission checking for non-existent user"""
        # Create empty mock DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='RISE-UserProfiles',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        result = self.auth_lambda.check_user_permissions('nonexistent_user', 'own_data', 'read')
        
        self.assertFalse(result['authorized'])
        self.assertIn('User not found', result['error'])
    
    @mock_dynamodb
    def test_session_creation(self):
        """Test user session creation"""
        # Create mock DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='RISE-UserSessions',
            KeySchema=[{'AttributeName': 'session_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'session_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        device_info = {
            'device_type': 'mobile',
            'os': 'Android',
            'app_version': '1.0.0'
        }
        
        result = self.auth_lambda.create_session(self.test_user_id, device_info)
        
        self.assertTrue(result['success'])
        self.assertIn('session_id', result)
        self.assertIn('expires_at', result)
        self.assertGreater(result['expires_at'], int(time.time()))
    
    @mock_dynamodb
    def test_valid_session_validation(self):
        """Test validation of valid session"""
        # Create mock DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='RISE-UserSessions',
            KeySchema=[{'AttributeName': 'session_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'session_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create a valid session
        session_id = 'test_session_123'
        table.put_item(Item={
            'session_id': session_id,
            'user_id': self.test_user_id,
            'created_at': int(time.time()),
            'expires_at': int(time.time()) + 3600,
            'active': True
        })
        
        result = self.auth_lambda.validate_session(session_id)
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['user_id'], self.test_user_id)
    
    @mock_dynamodb
    def test_expired_session_validation(self):
        """Test validation of expired session"""
        # Create mock DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='RISE-UserSessions',
            KeySchema=[{'AttributeName': 'session_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'session_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create an expired session
        session_id = 'expired_session_123'
        table.put_item(Item={
            'session_id': session_id,
            'user_id': self.test_user_id,
            'created_at': int(time.time()) - 7200,
            'expires_at': int(time.time()) - 3600,  # Expired 1 hour ago
            'active': True
        })
        
        result = self.auth_lambda.validate_session(session_id)
        
        self.assertFalse(result['valid'])
        self.assertIn('expired', result['error'].lower())
    
    @mock_dynamodb
    def test_inactive_session_validation(self):
        """Test validation of inactive session"""
        # Create mock DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='RISE-UserSessions',
            KeySchema=[{'AttributeName': 'session_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'session_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create an inactive session
        session_id = 'inactive_session_123'
        table.put_item(Item={
            'session_id': session_id,
            'user_id': self.test_user_id,
            'created_at': int(time.time()),
            'expires_at': int(time.time()) + 3600,
            'active': False  # Inactive session
        })
        
        result = self.auth_lambda.validate_session(session_id)
        
        self.assertFalse(result['valid'])
        self.assertIn('inactive', result['error'].lower())
    
    def test_nonexistent_session_validation(self):
        """Test validation of non-existent session"""
        result = self.auth_lambda.validate_session('nonexistent_session')
        
        self.assertFalse(result['valid'])
        self.assertIn('not found', result['error'].lower())


if __name__ == '__main__':
    unittest.main(verbosity=2)