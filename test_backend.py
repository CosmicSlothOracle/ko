#!/usr/bin/env python3
"""
Backend Test Suite for KOSGE Website
Tests all major functionality and catches potential bugs
"""

import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_participants, save_participants, validate_email, validate_participant_data
from cms import ContentManager
from config import validate_config, init_directories, init_participants_file


class TestBackendConfig(unittest.TestCase):
    """Test configuration and initialization"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_upload_folder = os.environ.get('UPLOAD_FOLDER')
        self.original_participants_file = os.environ.get('PARTICIPANTS_FILE')
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        if self.original_upload_folder:
            os.environ['UPLOAD_FOLDER'] = self.original_upload_folder
        if self.original_participants_file:
            os.environ['PARTICIPANTS_FILE'] = self.original_participants_file
    
    def test_config_validation(self):
        """Test configuration validation"""
        errors = validate_config()
        # Should not have critical errors in test environment
        self.assertIsInstance(errors, list)
    
    def test_directory_creation(self):
        """Test directory creation functionality"""
        test_upload_dir = os.path.join(self.temp_dir, 'uploads')
        test_content_dir = os.path.join(self.temp_dir, 'content')
        
        # Mock the config values
        with patch('config.UPLOAD_FOLDER', test_upload_dir):
            with patch('config.BASE_DIR', self.temp_dir):
                init_directories()
                
                self.assertTrue(os.path.exists(test_upload_dir))
                self.assertTrue(os.path.exists(test_content_dir))
    
    def test_participants_file_creation(self):
        """Test participants file creation"""
        test_file = os.path.join(self.temp_dir, 'participants.json')
        
        with patch('config.PARTICIPANTS_FILE', test_file):
            init_participants_file()
            
            self.assertTrue(os.path.exists(test_file))
            with open(test_file, 'r') as f:
                content = f.read()
                self.assertEqual(content, '[]')


class TestBackendValidation(unittest.TestCase):
    """Test validation functions"""
    
    def test_email_validation(self):
        """Test email validation"""
        # Valid emails
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org'
        ]
        
        # Invalid emails
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'user@',
            'user@.com'
        ]
        
        for email in valid_emails:
            self.assertTrue(validate_email(email), f"Valid email failed: {email}")
        
        for email in invalid_emails:
            self.assertFalse(validate_email(email), f"Invalid email passed: {email}")
    
    def test_participant_data_validation(self):
        """Test participant data validation"""
        # Valid data
        valid_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'message': 'Test message'
        }
        
        errors = validate_participant_data(valid_data)
        self.assertEqual(len(errors), 0)
        
        # Invalid data
        invalid_data = {
            'name': 'A',  # Too short
            'email': 'invalid-email',
            'message': 'x' * 1001  # Too long
        }
        
        errors = validate_participant_data(invalid_data)
        self.assertGreater(len(errors), 0)
        self.assertIn('Name must be at least 2 characters long', errors)
        self.assertIn('Invalid email format', errors)
        self.assertIn('Message must be less than 1000 characters', errors)


class TestBackendDataHandling(unittest.TestCase):
    """Test data handling functions"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, 'participants.json')
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_load_participants_empty_file(self):
        """Test loading participants from empty file"""
        with open(self.test_file, 'w') as f:
            f.write('[]')
        
        with patch('app.PARTICIPANTS_FILE', self.test_file):
            participants = load_participants()
            self.assertEqual(participants, [])
    
    def test_load_participants_invalid_json(self):
        """Test loading participants from invalid JSON"""
        with open(self.test_file, 'w') as f:
            f.write('invalid json')
        
        with patch('app.PARTICIPANTS_FILE', self.test_file):
            participants = load_participants()
            self.assertEqual(participants, [])
    
    def test_save_participants(self):
        """Test saving participants"""
        test_data = [
            {'name': 'Test User', 'email': 'test@example.com'}
        ]
        
        with patch('app.PARTICIPANTS_FILE', self.test_file):
            save_participants(test_data)
            
            with open(self.test_file, 'r') as f:
                saved_data = json.load(f)
                self.assertEqual(saved_data, test_data)


class TestBackendAPI(unittest.TestCase):
    """Test API endpoints"""
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('participants_count', data)
    
    def test_login_endpoint_valid(self):
        """Test login with valid credentials"""
        response = self.app.post('/api/login', 
                               json={'username': 'admin', 'password': 'kosge2024!'})
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('token', data)
    
    def test_login_endpoint_invalid(self):
        """Test login with invalid credentials"""
        response = self.app.post('/api/login', 
                               json={'username': 'admin', 'password': 'wrong'})
        self.assertEqual(response.status_code, 401)
    
    def test_login_endpoint_no_data(self):
        """Test login without data"""
        response = self.app.post('/api/login')
        self.assertEqual(response.status_code, 400)
    
    def test_add_participant_valid(self):
        """Test adding valid participant"""
        participant_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'message': 'Test message'
        }
        
        response = self.app.post('/api/participants', json=participant_data)
        self.assertEqual(response.status_code, 201)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
    
    def test_add_participant_invalid(self):
        """Test adding invalid participant"""
        participant_data = {
            'name': 'A',  # Too short
            'email': 'invalid-email'
        }
        
        response = self.app.post('/api/participants', json=participant_data)
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Validation failed', data['error'])


class TestCMS(unittest.TestCase):
    """Test CMS functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cms = ContentManager(self.temp_dir)
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_create_content(self):
        """Test content creation"""
        success = self.cms.create_content('test-section', 'Test Title', 'Test content')
        self.assertTrue(success)
        
        # Check if file was created
        file_path = os.path.join(self.temp_dir, 'de', 'test-section.md')
        self.assertTrue(os.path.exists(file_path))
    
    def test_get_content(self):
        """Test content retrieval"""
        # Create content first
        self.cms.create_content('test-section', 'Test Title', 'Test content')
        
        # Retrieve content
        content = self.cms.get_content('test-section')
        self.assertIsNotNone(content)
        self.assertEqual(content['content'], 'Test content')
        self.assertIn('html', content)
    
    def test_update_content(self):
        """Test content update"""
        # Create content first
        self.cms.create_content('test-section', 'Test Title', 'Test content')
        
        # Update content
        success = self.cms.update_content('test-section', 'Updated content')
        self.assertTrue(success)
        
        # Verify update
        content = self.cms.get_content('test-section')
        self.assertEqual(content['content'], 'Updated content')
    
    def test_list_sections(self):
        """Test listing sections"""
        # Create some content
        self.cms.create_content('section1', 'Title 1', 'Content 1')
        self.cms.create_content('section2', 'Title 2', 'Content 2')
        
        sections = self.cms.list_sections()
        self.assertEqual(len(sections), 2)
        section_names = [s['section'] for s in sections]
        self.assertIn('section1', section_names)
        self.assertIn('section2', section_names)


class TestErrorHandling(unittest.TestCase):
    """Test error handling"""
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_file_not_found(self):
        """Test handling of non-existent files"""
        response = self.app.get('/api/uploads/nonexistent.png')
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_file_type(self):
        """Test handling of invalid file types"""
        response = self.app.post('/api/banners', 
                               data={'file': (b'test', 'test.txt')})
        self.assertEqual(response.status_code, 400)
    
    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        response = self.app.post('/api/participants', 
                               data='invalid json',
                               content_type='application/json')
        self.assertEqual(response.status_code, 400)


def run_tests():
    """Run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestBackendConfig,
        TestBackendValidation,
        TestBackendDataHandling,
        TestBackendAPI,
        TestCMS,
        TestErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"{'='*50}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return len(result.failures) + len(result.errors) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)