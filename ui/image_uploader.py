"""
RISE Image Uploader Component
Streamlit component for uploading and analyzing crop images
"""

import streamlit as st
import base64
from PIL import Image
import io
from typing import Optional, Dict, Any, List
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.disease_identification_tools import DiseaseIdentificationTools


class ImageUploader:
    """Image uploader component for crop disease identification"""
    
    def __init__(self, user_id: str, language_code: str = 'en'):
        """
        Initialize image uploader
        
        Args:
            user_id: User ID for tracking
            language_code: User's language preference
        """
        self.user_id = user_id
        self.language_code = language_code
        self.disease_tools = DiseaseIdentificationTools()
    
    def render(self) -> Optional[Dict[str, Any]]:
        """
        Render image upload interface
        
        Returns:
            Diagnosis results if analysis completed, None otherwise
        """
        st.markdown("### 📸 Crop Disease Identification")
        st.markdown("Upload a photo of your crop to identify diseases and get treatment recommendations")
        
        # Create tabs for different input methods
        tab1, tab2 = st.tabs(["📁 Upload Image", "📷 Take Photo"])
        
        with tab1:
            result = self._render_file_upload()
        
        with tab2:
            result = self._render_camera_input()
        
        return result
    
    def _render_file_upload(self) -> Optional[Dict[str, Any]]:
        """Render file upload interface"""
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose an image of your crop",
            type=['jpg', 'jpeg', 'png'],
            help="Upload a clear photo of the affected crop or leaves",
            key="file_uploader"
        )
        
        if uploaded_file is not None:
            return self._process_image(uploaded_file)
        
        return None
    
    def _render_camera_input(self) -> Optional[Dict[str, Any]]:
        """Render camera input interface"""
        
        # Camera input
        camera_photo = st.camera_input(
            "Take a photo of your crop",
            help="Ensure good lighting and focus on affected areas",
            key="camera_input"
        )
        
        if camera_photo is not None:
            return self._process_image(camera_photo)
        
        return None
    
    def _process_image(self, image_file) -> Optional[Dict[str, Any]]:
        """Process uploaded image"""
        
        try:
            # Read image bytes
            image_bytes = image_file.read()
            
            # Display image preview
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.image(image_bytes, caption="Uploaded Image", use_container_width=True)
            
            with col2:
                st.markdown("#### Image Details")
                
                # Get image info
                img = Image.open(io.BytesIO(image_bytes))
                width, height = img.size
                file_size_kb = len(image_bytes) / 1024
                
                st.markdown(f"**Dimensions:** {width} x {height} pixels")
                st.markdown(f"**File Size:** {file_size_kb:.1f} KB")
                st.markdown(f"**Format:** {img.format}")
            
            # Additional context inputs
            st.markdown("---")
            st.markdown("#### Additional Information (Optional)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                crop_type = st.text_input(
                    "Crop Type",
                    placeholder="e.g., wheat, rice, cotton",
                    help="What crop is shown in the image?",
                    key="crop_type_input"
                )
            
            with col2:
                symptoms = st.text_input(
                    "Observed Symptoms",
                    placeholder="e.g., yellow leaves, brown spots",
                    help="Describe what you're seeing",
                    key="symptoms_input"
                )
            
            # Analyze button
            if st.button("🔍 Analyze Image", type="primary", use_container_width=True):
                return self._analyze_image(
                    image_bytes=image_bytes,
                    crop_type=crop_type if crop_type else None,
                    additional_context=symptoms if symptoms else None
                )
        
        except Exception as e:
            st.error(f"Error processing image: {e}")
        
        return None
    
    def _analyze_image(self,
                      image_bytes: bytes,
                      crop_type: Optional[str],
                      additional_context: Optional[str]) -> Optional[Dict[str, Any]]:
        """Analyze image for disease identification"""
        
        with st.spinner("🔬 Analyzing image... This may take 10-15 seconds..."):
            try:
                # Analyze with disease identification tools
                result = self.disease_tools.analyze_crop_image(
                    image_data=image_bytes,
                    user_id=self.user_id,
                    crop_type=crop_type,
                    additional_context=additional_context
                )
                
                if result['success']:
                    self._display_diagnosis(result)
                    return result
                else:
                    # Handle errors
                    if result.get('error') == 'poor_image_quality':
                        self._display_quality_issues(result.get('validation', {}))
                    else:
                        st.error(f"Analysis failed: {result.get('error', 'Unknown error')}")
            
            except Exception as e:
                st.error(f"Error during analysis: {e}")
        
        return None
    
    def _display_diagnosis(self, result: Dict[str, Any]):
        """Display diagnosis results"""
        
        st.markdown("---")
        st.markdown("## 🔬 Diagnosis Results")
        
        # Severity indicator
        severity = result.get('severity', 'unknown')
        severity_colors = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }
        severity_icon = severity_colors.get(severity, '⚪')
        
        st.markdown(f"### {severity_icon} Severity: {severity.upper()}")
        
        # Confidence score
        confidence = result.get('confidence_score', 0.0)
        st.progress(confidence, text=f"Confidence: {confidence*100:.1f}%")
        
        st.markdown("---")
        
        # Diseases detected
        diseases = result.get('diseases', [])
        
        if diseases:
            st.markdown("### 🦠 Diseases Detected")
            
            for i, disease in enumerate(diseases, 1):
                if disease.lower() == 'healthy - no disease detected':
                    st.success(f"✅ {disease}")
                else:
                    st.warning(f"{i}. {disease}")
            
            # Multiple issues warning
            if result.get('multiple_issues', False):
                st.info("⚠️ Multiple issues detected. Recommendations are prioritized by urgency.")
        
        st.markdown("---")
        
        # Full analysis
        with st.expander("📋 Detailed Analysis", expanded=True):
            full_analysis = result.get('full_analysis', '')
            st.markdown(full_analysis)
        
        # Treatment recommendations
        treatments = result.get('treatment_recommendations', [])
        if treatments:
            with st.expander("💊 Treatment Recommendations", expanded=True):
                for treatment in treatments:
                    st.markdown(f"**{treatment.get('type', 'Treatment').title()}:**")
                    st.markdown(treatment.get('description', ''))
                    st.markdown("")
        
        # Preventive measures
        prevention = result.get('preventive_measures', [])
        if prevention:
            with st.expander("🛡️ Preventive Measures"):
                for measure in prevention:
                    st.markdown(f"- {measure}")
        
        # Diagnosis ID for reference
        st.markdown("---")
        st.caption(f"Diagnosis ID: {result.get('diagnosis_id', 'N/A')}")
        st.caption(f"Stored in: {result.get('s3_key', 'N/A')}")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Download Report", use_container_width=True):
                self._download_report(result)
        
        with col2:
            if st.button("📤 Share with Expert", use_container_width=True):
                st.info("Feature coming soon: Share diagnosis with agricultural experts")
        
        with col3:
            if st.button("🔄 Analyze Another", use_container_width=True):
                st.rerun()
    
    def _display_quality_issues(self, validation: Dict[str, Any]):
        """Display image quality issues and guidance"""
        
        st.warning("⚠️ Image Quality Issues Detected")
        
        issues = validation.get('issues', [])
        guidance = validation.get('guidance', [])
        
        if issues:
            st.markdown("**Issues:**")
            for issue in issues:
                st.markdown(f"- {issue.replace('_', ' ').title()}")
        
        if guidance:
            st.markdown("**Recommendations:**")
            for guide in guidance:
                st.markdown(f"✓ {guide}")
        
        st.info("Please upload a better quality image for accurate diagnosis.")
    
    def _download_report(self, result: Dict[str, Any]):
        """Generate and download diagnosis report"""
        
        # Create text report
        report = f"""
RISE - Crop Disease Diagnosis Report
=====================================

Diagnosis ID: {result.get('diagnosis_id', 'N/A')}
Date: {result.get('timestamp', 'N/A')}
User ID: {self.user_id}

SEVERITY: {result.get('severity', 'unknown').upper()}
CONFIDENCE: {result.get('confidence_score', 0.0)*100:.1f}%

DISEASES DETECTED:
{chr(10).join(f"- {d}" for d in result.get('diseases', []))}

DETAILED ANALYSIS:
{result.get('full_analysis', '')}

---
Generated by RISE - Rural Innovation and Sustainable Ecosystem
"""
        
        # Create download button
        st.download_button(
            label="Download Report as Text",
            data=report,
            file_name=f"diagnosis_{result.get('diagnosis_id', 'report')}.txt",
            mime="text/plain"
        )
    
    def render_history(self):
        """Render enhanced diagnosis history with filtering and tracking"""
        
        st.markdown("### 📜 Diagnosis History & Treatment Tracking")
        
        try:
            from tools.diagnosis_history_tools import DiagnosisHistoryTools
            history_tools = DiagnosisHistoryTools()
            
            # Filters section
            with st.expander("🔍 Filters & Options", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    severity_filter = st.selectbox(
                        "Severity",
                        ["All", "Low", "Medium", "High", "Critical"],
                        key="severity_filter"
                    )
                
                with col2:
                    status_filter = st.selectbox(
                        "Follow-up Status",
                        ["All", "Pending", "Treatment Applied", "Improving", "Worsened", "Resolved"],
                        key="status_filter"
                    )
                
                with col3:
                    type_filter = st.selectbox(
                        "Diagnosis Type",
                        ["All", "Disease", "Pest"],
                        key="type_filter"
                    )
            
            # Build filters dict
            filters = {}
            if severity_filter != "All":
                filters['severity'] = severity_filter.lower()
            if status_filter != "All":
                filters['follow_up_status'] = status_filter.lower().replace(' ', '_')
            if type_filter != "All":
                filters['diagnosis_type'] = type_filter.lower()
            
            # Get history with filters
            history = history_tools.get_diagnosis_history(
                user_id=self.user_id,
                limit=20,
                filters=filters if filters else None
            )
            
            if not history:
                st.info("No diagnoses found matching your filters. Try adjusting the filters or upload a new image!")
                return
            
            # Statistics summary
            stats = history_tools.get_statistics(self.user_id)
            if stats.get('total_diagnoses', 0) > 0:
                st.markdown("#### 📊 Your Diagnosis Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Diagnoses", stats['total_diagnoses'])
                
                with col2:
                    severity_dist = stats.get('severity_distribution', {})
                    critical_count = severity_dist.get('critical', 0) + severity_dist.get('high', 0)
                    st.metric("High Priority", critical_count)
                
                with col3:
                    status_dist = stats.get('follow_up_status_distribution', {})
                    resolved_count = status_dist.get('resolved', 0)
                    st.metric("Resolved", resolved_count)
                
                with col4:
                    improving_count = status_dist.get('improving', 0)
                    st.metric("Improving", improving_count)
                
                st.markdown("---")
            
            # Comparison mode
            st.markdown("#### 🔄 Treatment Progress Tracking")
            
            if len(history) >= 2:
                with st.expander("📈 Compare Diagnoses for Progress Tracking"):
                    st.markdown("Select 2 or more diagnoses to track treatment progress over time")
                    
                    # Create selection options
                    diagnosis_options = {}
                    for diag in history:
                        date_str = datetime.fromtimestamp(diag.get('created_timestamp', 0)).strftime('%Y-%m-%d')
                        label = f"{date_str} - {diag.get('crop_type', 'Unknown')} ({diag.get('severity', 'unknown')})"
                        diagnosis_options[label] = diag.get('diagnosis_id')
                    
                    selected_labels = st.multiselect(
                        "Select diagnoses to compare",
                        list(diagnosis_options.keys()),
                        key="compare_diagnoses"
                    )
                    
                    if len(selected_labels) >= 2:
                        selected_ids = [diagnosis_options[label] for label in selected_labels]
                        
                        if st.button("📊 Generate Progress Report", use_container_width=True):
                            self._display_comparison(history_tools, selected_ids)
            
            st.markdown("---")
            st.markdown("#### 📋 Diagnosis Records")
            
            # Display history
            for diagnosis in history:
                self._render_diagnosis_card(diagnosis, history_tools)
        
        except Exception as e:
            st.error(f"Error loading history: {e}")
            import traceback
            st.error(traceback.format_exc())
    
    def _render_diagnosis_card(self, diagnosis: Dict[str, Any], history_tools):
        """Render individual diagnosis card with actions"""
        
        # Format date
        date_str = datetime.fromtimestamp(diagnosis.get('created_timestamp', 0)).strftime('%Y-%m-%d %H:%M')
        
        # Severity icon
        severity_icons = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }
        severity_icon = severity_icons.get(diagnosis.get('severity', 'low'), '⚪')
        
        # Status icon
        status_icons = {
            'pending': '⏳',
            'treatment_applied': '💊',
            'improving': '📈',
            'worsened': '📉',
            'resolved': '✅'
        }
        status_icon = status_icons.get(diagnosis.get('follow_up_status', 'pending'), '⏳')
        
        # Type icon
        type_icon = '🦠' if diagnosis.get('diagnosis_type') == 'disease' else '🐛'
        
        with st.expander(
            f"{type_icon} {date_str} - {diagnosis.get('crop_type', 'Unknown')} "
            f"{severity_icon} {diagnosis.get('severity', 'unknown').title()} "
            f"{status_icon} {diagnosis.get('follow_up_status', 'pending').replace('_', ' ').title()}"
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Diagnosis ID:** `{diagnosis.get('diagnosis_id')}`")
                st.markdown(f"**Type:** {diagnosis.get('diagnosis_type', 'unknown').title()}")
                st.markdown(f"**Confidence:** {diagnosis.get('confidence_score', 0)*100:.1f}%")
                
                # Diseases/Pests
                items = diagnosis.get('diseases', []) or diagnosis.get('pests', [])
                if items:
                    st.markdown(f"**Identified:** {', '.join(items)}")
            
            with col2:
                # Follow-up status update
                new_status = st.selectbox(
                    "Update Status",
                    ["pending", "treatment_applied", "improving", "worsened", "resolved"],
                    index=["pending", "treatment_applied", "improving", "worsened", "resolved"].index(
                        diagnosis.get('follow_up_status', 'pending')
                    ),
                    key=f"status_{diagnosis.get('diagnosis_id')}"
                )
                
                notes = st.text_area(
                    "Notes",
                    value=diagnosis.get('follow_up_notes', ''),
                    key=f"notes_{diagnosis.get('diagnosis_id')}",
                    height=80
                )
                
                if st.button("💾 Update", key=f"update_{diagnosis.get('diagnosis_id')}", use_container_width=True):
                    success = history_tools.update_follow_up_status(
                        diagnosis_id=diagnosis.get('diagnosis_id'),
                        status=new_status,
                        notes=notes if notes else None,
                        diagnosis_type=diagnosis.get('diagnosis_type', 'disease')
                    )
                    
                    if success:
                        st.success("✅ Status updated!")
                        st.rerun()
                    else:
                        st.error("❌ Update failed")
            
            # Action buttons
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 View Full Report", key=f"report_{diagnosis.get('diagnosis_id')}", use_container_width=True):
                    report = history_tools.generate_report(
                        diagnosis_id=diagnosis.get('diagnosis_id'),
                        diagnosis_type=diagnosis.get('diagnosis_type', 'disease')
                    )
                    if report:
                        st.text_area("Report", report, height=400, key=f"report_text_{diagnosis.get('diagnosis_id')}")
                        st.download_button(
                            "📥 Download Report",
                            report,
                            file_name=f"diagnosis_{diagnosis.get('diagnosis_id')}.txt",
                            mime="text/plain",
                            key=f"download_{diagnosis.get('diagnosis_id')}"
                        )
            
            with col2:
                if st.button("📋 View Details", key=f"details_{diagnosis.get('diagnosis_id')}", use_container_width=True):
                    st.json(diagnosis)
            
            with col3:
                if st.button("🖼️ View Image", key=f"image_{diagnosis.get('diagnosis_id')}", use_container_width=True):
                    st.info("Image viewing feature - requires S3 presigned URL implementation")
    
    def _display_comparison(self, history_tools, diagnosis_ids: List[str]):
        """Display diagnosis comparison for treatment progress"""
        
        comparison = history_tools.compare_diagnoses(diagnosis_ids)
        
        if not comparison.get('success'):
            st.error(f"Comparison failed: {comparison.get('error')}")
            return
        
        st.markdown("### 📊 Treatment Progress Report")
        
        progress = comparison.get('progress', {})
        
        # Progress status
        status = progress.get('status', 'unknown')
        status_colors = {
            'improving': '🟢',
            'stable': '🟡',
            'worsening': '🔴',
            'insufficient_data': '⚪'
        }
        status_icon = status_colors.get(status, '⚪')
        
        st.markdown(f"## {status_icon} Status: {status.upper()}")
        
        if status != 'insufficient_data':
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Severity Change",
                    f"{progress.get('severity_change', 0):+d}",
                    delta="Improving" if progress.get('severity_change', 0) > 0 else "Worsening" if progress.get('severity_change', 0) < 0 else "Stable"
                )
            
            with col2:
                st.metric(
                    "Days Elapsed",
                    f"{progress.get('days_elapsed', 0):.1f}"
                )
            
            with col3:
                st.metric(
                    "Total Diagnoses",
                    progress.get('total_diagnoses', 0)
                )
            
            # Timeline
            st.markdown("---")
            st.markdown("### 📅 Treatment Timeline")
            
            diagnoses = comparison.get('diagnoses', [])
            for i, diag in enumerate(diagnoses, 1):
                date_str = datetime.fromtimestamp(diag.get('created_timestamp', 0)).strftime('%Y-%m-%d %H:%M')
                
                severity_icons = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'}
                severity_icon = severity_icons.get(diag.get('severity', 'low'), '⚪')
                
                st.markdown(
                    f"**{i}. {date_str}** {severity_icon} "
                    f"Severity: {diag.get('severity', 'unknown').title()} | "
                    f"Status: {diag.get('follow_up_status', 'pending').replace('_', ' ').title()}"
                )
        else:
            st.info(progress.get('message', 'Insufficient data for comparison'))


def render_image_uploader(user_id: str, language_code: str = 'en') -> Optional[Dict[str, Any]]:
    """
    Convenience function to render image uploader
    
    Args:
        user_id: User ID
        language_code: Language preference
    
    Returns:
        Diagnosis results if available
    """
    uploader = ImageUploader(user_id, language_code)
    return uploader.render()


def render_diagnosis_history(user_id: str, language_code: str = 'en'):
    """
    Convenience function to render diagnosis history
    
    Args:
        user_id: User ID
        language_code: Language preference
    """
    uploader = ImageUploader(user_id, language_code)
    uploader.render_history()
