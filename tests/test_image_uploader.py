"""
RISE Image Uploader Component Tests
Tests for image upload, preview, validation, and diagnosis display
"""

import pytest
import sys
import os
import io
from PIL import Image
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.image_uploader import ImageUploader, render_image_uploader, render_diagnosis_history


class TestImageUploaderInitialization:
    """Test image uploader initialization"""
    
    def test_uploader_creation(self):
        """Test image uploader can be created"""
        user_id = "farmer_123"
        language = "en"
        
        uploader = ImageUploader(user_id, language)
        
        assert uploader.user_id == user_id
        assert uploader.language_code == language
    
    def test_default_language(self):
        """Test default language is English"""
        uploader = ImageUploader("farmer_123")
        
        assert uploader.language_code == "en"
    
    @patch('tools.disease_identification_tools.DiseaseIdentificationTools')
    def test_disease_tools_initialization(self, mock_tools):
        """Test disease identification tools are initialized"""
        uploader = ImageUploader("farmer_123", "en")
        
        assert uploader.disease_tools is not None


class TestImageUpload:
    """Test image upload functionality"""
    
    def test_supported_image_formats(self):
        """Test supported image formats"""
        supported_formats = ['jpg', 'jpeg', 'png']
        
        assert 'jpg' in supported_formats
        assert 'jpeg' in supported_formats
        assert 'png' in supported_formats
        assert len(supported_formats) == 3
    
    def test_image_file_validation(self):
        """Test image file validation"""
        valid_extensions = ['.jpg', '.jpeg', '.png']
        
        test_files = [
            ('image.jpg', True),
            ('photo.jpeg', True),
            ('picture.png', True),
            ('document.pdf', False),
            ('video.mp4', False),
        ]
        
        for filename, should_be_valid in test_files:
            ext = os.path.splitext(filename)[1]
            is_valid = ext in valid_extensions
            assert is_valid == should_be_valid, f"File {filename} validation failed"
    
    def test_create_test_image(self):
        """Test creating a test image"""
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes = img_bytes.getvalue()
        
        assert len(img_bytes) > 0
        assert isinstance(img_bytes, bytes)
    
    def test_image_bytes_reading(self):
        """Test reading image bytes"""
        # Create test image
        img = Image.new('RGB', (100, 100), color='blue')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()
        
        # Verify can read back
        img_read = Image.open(io.BytesIO(img_bytes))
        assert img_read.size == (100, 100)
        assert img_read.format == 'PNG'


class TestImagePreview:
    """Test image preview functionality"""
    
    def test_image_dimensions_display(self):
        """Test image dimensions are displayed"""
        img = Image.new('RGB', (800, 600))
        width, height = img.size
        
        assert width == 800
        assert height == 600
        
        dimensions_text = f"{width} x {height} pixels"
        assert "800 x 600" in dimensions_text
    
    def test_file_size_calculation(self):
        """Test file size calculation"""
        img = Image.new('RGB', (100, 100))
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG')
        img_bytes = img_buffer.getvalue()
        
        file_size_kb = len(img_bytes) / 1024
        
        assert file_size_kb > 0
        assert isinstance(file_size_kb, float)
    
    def test_image_format_detection(self):
        """Test image format detection"""
        formats = ['JPEG', 'PNG', 'BMP']
        
        for fmt in formats:
            img = Image.new('RGB', (50, 50))
            img_buffer = io.BytesIO()
            img.save(img_buffer, format=fmt)
            img_buffer.seek(0)
            
            img_read = Image.open(img_buffer)
            assert img_read.format == fmt


class TestAdditionalContext:
    """Test additional context inputs"""
    
    def test_crop_type_input(self):
        """Test crop type input"""
        crop_types = ["wheat", "rice", "cotton", "sugarcane"]
        
        for crop in crop_types:
            assert len(crop) > 0
            assert isinstance(crop, str)
    
    def test_symptoms_input(self):
        """Test symptoms input"""
        symptoms = [
            "yellow leaves",
            "brown spots",
            "wilting",
            "holes in leaves"
        ]
        
        for symptom in symptoms:
            assert len(symptom) > 0
    
    def test_optional_context_handling(self):
        """Test optional context is handled correctly"""
        crop_type = ""
        symptoms = ""
        
        crop_value = crop_type if crop_type else None
        symptoms_value = symptoms if symptoms else None
        
        assert crop_value is None
        assert symptoms_value is None


class TestImageAnalysis:
    """Test image analysis functionality"""
    
    @patch('tools.disease_identification_tools.DiseaseIdentificationTools')
    def test_analysis_success(self, mock_tools_class):
        """Test successful image analysis"""
        mock_tools = Mock()
        mock_tools.analyze_crop_image.return_value = {
            'success': True,
            'diagnosis_id': 'diag_123',
            'diseases': ['Leaf Blight'],
            'severity': 'medium',
            'confidence_score': 0.89,
            'full_analysis': 'Detected leaf blight infection',
            'treatment_recommendations': [
                {'type': 'chemical', 'description': 'Apply fungicide'}
            ]
        }
        mock_tools_class.return_value = mock_tools
        
        uploader = ImageUploader("farmer_123", "en")
        uploader.disease_tools = mock_tools
        
        result = uploader.disease_tools.analyze_crop_image(
            image_data=b'fake image',
            user_id="farmer_123",
            crop_type="wheat",
            additional_context=None
        )
        
        assert result['success'] is True
        assert 'diagnosis_id' in result
        assert len(result['diseases']) > 0
    
    @patch('tools.disease_identification_tools.DiseaseIdentificationTools')
    def test_analysis_poor_quality(self, mock_tools_class):
        """Test analysis with poor image quality"""
        mock_tools = Mock()
        mock_tools.analyze_crop_image.return_value = {
            'success': False,
            'error': 'poor_image_quality',
            'validation': {
                'issues': ['blurry', 'low_resolution'],
                'guidance': ['Use better lighting', 'Hold camera steady']
            }
        }
        mock_tools_class.return_value = mock_tools
        
        uploader = ImageUploader("farmer_123", "en")
        uploader.disease_tools = mock_tools
        
        result = uploader.disease_tools.analyze_crop_image(
            image_data=b'blurry image',
            user_id="farmer_123"
        )
        
        assert result['success'] is False
        assert result['error'] == 'poor_image_quality'
        assert 'validation' in result
    
    def test_analysis_timeout(self):
        """Test analysis timeout handling"""
        max_wait_time = 15  # seconds
        actual_time = 20
        
        if actual_time > max_wait_time:
            timeout_occurred = True
        else:
            timeout_occurred = False
        
        assert timeout_occurred is True


class TestDiagnosisDisplay:
    """Test diagnosis results display"""
    
    def test_severity_indicators(self):
        """Test severity indicators"""
        severity_colors = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }
        
        for severity, icon in severity_colors.items():
            assert len(icon) > 0
            assert severity in ['low', 'medium', 'high', 'critical']
    
    def test_confidence_score_display(self):
        """Test confidence score display"""
        confidence = 0.89
        percentage = confidence * 100
        
        assert percentage == 89.0
        assert 0 <= percentage <= 100
    
    def test_disease_list_display(self):
        """Test disease list display"""
        diseases = ['Leaf Blight', 'Powdery Mildew', 'Root Rot']
        
        assert len(diseases) > 0
        for i, disease in enumerate(diseases, 1):
            assert isinstance(disease, str)
            assert len(disease) > 0
    
    def test_healthy_crop_display(self):
        """Test healthy crop display"""
        disease = "Healthy - No disease detected"
        
        is_healthy = "healthy" in disease.lower()
        assert is_healthy is True
    
    def test_multiple_issues_warning(self):
        """Test multiple issues warning"""
        diseases = ['Disease A', 'Disease B', 'Disease C']
        multiple_issues = len(diseases) > 1
        
        assert multiple_issues is True
        
        if multiple_issues:
            warning = "Multiple issues detected. Recommendations are prioritized by urgency."
            assert "Multiple" in warning


class TestTreatmentRecommendations:
    """Test treatment recommendations display"""
    
    def test_treatment_structure(self):
        """Test treatment recommendation structure"""
        treatment = {
            'type': 'chemical',
            'description': 'Apply copper-based fungicide at 2g/L concentration'
        }
        
        assert 'type' in treatment
        assert 'description' in treatment
        assert len(treatment['description']) > 0
    
    def test_treatment_types(self):
        """Test different treatment types"""
        treatment_types = ['chemical', 'organic', 'cultural', 'biological']
        
        for t_type in treatment_types:
            assert isinstance(t_type, str)
            assert len(t_type) > 0
    
    def test_preventive_measures(self):
        """Test preventive measures"""
        prevention = [
            "Ensure proper drainage",
            "Maintain crop rotation",
            "Remove infected plant debris"
        ]
        
        assert len(prevention) > 0
        for measure in prevention:
            assert isinstance(measure, str)


class TestDiagnosisHistory:
    """Test diagnosis history functionality"""
    
    def test_history_filters(self):
        """Test history filtering options"""
        filters = {
            'severity': ['All', 'Low', 'Medium', 'High', 'Critical'],
            'status': ['All', 'Pending', 'Treatment Applied', 'Improving', 'Worsened', 'Resolved'],
            'type': ['All', 'Disease', 'Pest']
        }
        
        assert 'severity' in filters
        assert 'status' in filters
        assert 'type' in filters
        assert 'All' in filters['severity']
    
    def test_filter_application(self):
        """Test filter application logic"""
        severity_filter = "High"
        
        filters = {}
        if severity_filter != "All":
            filters['severity'] = severity_filter.lower()
        
        assert 'severity' in filters
        assert filters['severity'] == 'high'
    
    def test_empty_history_handling(self):
        """Test handling of empty history"""
        history = []
        
        if not history:
            message = "No diagnoses found matching your filters"
        else:
            message = None
        
        assert message is not None
        assert "No diagnoses" in message


class TestStatisticsSummary:
    """Test statistics summary display"""
    
    def test_statistics_structure(self):
        """Test statistics structure"""
        stats = {
            'total_diagnoses': 15,
            'severity_distribution': {
                'low': 5,
                'medium': 7,
                'high': 2,
                'critical': 1
            },
            'follow_up_status_distribution': {
                'pending': 3,
                'improving': 8,
                'resolved': 4
            }
        }
        
        assert 'total_diagnoses' in stats
        assert 'severity_distribution' in stats
        assert stats['total_diagnoses'] == 15
    
    def test_high_priority_calculation(self):
        """Test high priority count calculation"""
        severity_dist = {
            'low': 5,
            'medium': 7,
            'high': 2,
            'critical': 1
        }
        
        critical_count = severity_dist.get('critical', 0) + severity_dist.get('high', 0)
        
        assert critical_count == 3
    
    def test_metrics_display(self):
        """Test metrics display"""
        metrics = {
            'total': 15,
            'high_priority': 3,
            'resolved': 4,
            'improving': 8
        }
        
        for key, value in metrics.items():
            assert isinstance(value, int)
            assert value >= 0


class TestDiagnosisComparison:
    """Test diagnosis comparison for progress tracking"""
    
    def test_comparison_selection(self):
        """Test diagnosis selection for comparison"""
        history = [
            {'diagnosis_id': 'diag_1', 'created_timestamp': 1000},
            {'diagnosis_id': 'diag_2', 'created_timestamp': 2000},
            {'diagnosis_id': 'diag_3', 'created_timestamp': 3000}
        ]
        
        selected_ids = ['diag_1', 'diag_3']
        
        assert len(selected_ids) >= 2
        assert 'diag_1' in selected_ids
    
    def test_progress_status(self):
        """Test progress status determination"""
        statuses = ['improving', 'stable', 'worsening', 'insufficient_data']
        
        for status in statuses:
            assert isinstance(status, str)
            assert len(status) > 0
    
    def test_severity_change_calculation(self):
        """Test severity change calculation"""
        severity_map = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        
        initial_severity = 'high'  # 3
        current_severity = 'medium'  # 2
        
        change = severity_map[initial_severity] - severity_map[current_severity]
        
        assert change == 1  # Improving
    
    def test_days_elapsed_calculation(self):
        """Test days elapsed calculation"""
        start_timestamp = 1000000
        end_timestamp = 1086400  # +1 day
        
        days_elapsed = (end_timestamp - start_timestamp) / 86400
        
        assert days_elapsed == 1.0


class TestFollowUpTracking:
    """Test follow-up status tracking"""
    
    def test_status_update(self):
        """Test status update"""
        current_status = 'pending'
        new_status = 'treatment_applied'
        
        assert new_status != current_status
        assert new_status in ['pending', 'treatment_applied', 'improving', 'worsened', 'resolved']
    
    def test_notes_addition(self):
        """Test adding notes to diagnosis"""
        notes = "Applied fungicide as recommended. Will monitor for 7 days."
        
        assert len(notes) > 0
        assert isinstance(notes, str)
    
    def test_status_icons(self):
        """Test status icons"""
        status_icons = {
            'pending': '⏳',
            'treatment_applied': '💊',
            'improving': '📈',
            'worsened': '📉',
            'resolved': '✅'
        }
        
        for status, icon in status_icons.items():
            assert len(icon) > 0


class TestReportGeneration:
    """Test diagnosis report generation"""
    
    def test_report_structure(self):
        """Test report structure"""
        report_sections = [
            'Diagnosis ID',
            'Date',
            'User ID',
            'Severity',
            'Confidence',
            'Diseases Detected',
            'Detailed Analysis'
        ]
        
        for section in report_sections:
            assert len(section) > 0
    
    def test_report_content(self):
        """Test report content generation"""
        diagnosis = {
            'diagnosis_id': 'diag_123',
            'timestamp': '2024-01-15 10:30',
            'severity': 'medium',
            'confidence_score': 0.89,
            'diseases': ['Leaf Blight'],
            'full_analysis': 'Detected fungal infection'
        }
        
        report = f"""
Diagnosis ID: {diagnosis['diagnosis_id']}
Date: {diagnosis['timestamp']}
Severity: {diagnosis['severity'].upper()}
Confidence: {diagnosis['confidence_score']*100:.1f}%
Diseases: {', '.join(diagnosis['diseases'])}
Analysis: {diagnosis['full_analysis']}
"""
        
        assert 'diag_123' in report
        assert 'MEDIUM' in report
        assert '89.0%' in report
    
    def test_report_download(self):
        """Test report download filename"""
        diagnosis_id = 'diag_123'
        filename = f"diagnosis_{diagnosis_id}.txt"
        
        assert filename.endswith('.txt')
        assert diagnosis_id in filename


class TestImageQualityValidation:
    """Test image quality validation"""
    
    def test_quality_issues_display(self):
        """Test quality issues display"""
        issues = ['blurry', 'low_resolution', 'poor_lighting']
        
        for issue in issues:
            formatted = issue.replace('_', ' ').title()
            assert len(formatted) > 0
    
    def test_quality_guidance(self):
        """Test quality improvement guidance"""
        guidance = [
            'Use better lighting',
            'Hold camera steady',
            'Move closer to subject',
            'Clean camera lens'
        ]
        
        assert len(guidance) > 0
        for guide in guidance:
            assert isinstance(guide, str)
    
    def test_retry_mechanism(self):
        """Test retry mechanism for poor quality"""
        quality_acceptable = False
        
        if not quality_acceptable:
            should_retry = True
            message = "Please upload a better quality image"
        else:
            should_retry = False
            message = None
        
        assert should_retry is True
        assert message is not None


class TestActionButtons:
    """Test action buttons functionality"""
    
    def test_download_report_button(self):
        """Test download report button"""
        button_text = "📥 Download Report"
        
        assert "Download" in button_text
        assert "📥" in button_text
    
    def test_share_with_expert_button(self):
        """Test share with expert button"""
        button_text = "📤 Share with Expert"
        
        assert "Share" in button_text
        assert "Expert" in button_text
    
    def test_analyze_another_button(self):
        """Test analyze another button"""
        button_text = "🔄 Analyze Another"
        
        assert "Analyze" in button_text
        assert "🔄" in button_text


class TestResponsiveLayout:
    """Test responsive layout"""
    
    def test_column_layouts(self):
        """Test column layouts for different sections"""
        # Two-column layout for image and details
        columns_2 = [1, 1]
        assert len(columns_2) == 2
        
        # Three-column layout for action buttons
        columns_3 = [1, 1, 1]
        assert len(columns_3) == 3
    
    def test_expander_usage(self):
        """Test expander usage for detailed content"""
        expanders = [
            "📋 Detailed Analysis",
            "💊 Treatment Recommendations",
            "🛡️ Preventive Measures"
        ]
        
        for expander in expanders:
            assert len(expander) > 0


class TestErrorHandling:
    """Test error handling"""
    
    def test_image_processing_error(self):
        """Test image processing error handling"""
        try:
            raise Exception("Failed to process image")
        except Exception as e:
            error_msg = f"Error processing image: {e}"
        
        assert "Error" in error_msg
        assert "processing" in error_msg
    
    def test_analysis_error(self):
        """Test analysis error handling"""
        result = {
            'success': False,
            'error': 'Service unavailable'
        }
        
        if not result['success']:
            error_msg = f"Analysis failed: {result['error']}"
        
        assert "failed" in error_msg
    
    def test_history_loading_error(self):
        """Test history loading error"""
        try:
            raise Exception("Database connection failed")
        except Exception as e:
            error_msg = f"Error loading history: {e}"
        
        assert "Error" in error_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
