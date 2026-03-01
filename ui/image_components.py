"""
Image upload and processing components for Streamlit UI
Handles image upload, preview, quality validation, and S3 storage
"""

import streamlit as st
from PIL import Image
import boto3
from typing import Optional, Tuple
import io
import os
from datetime import datetime
import base64


def render_image_upload() -> Optional[Tuple[Image.Image, bytes]]:
    """
    Render image upload component with camera/file upload
    
    Returns:
        Tuple of (PIL Image, image bytes) if uploaded, None otherwise
    """
    st.markdown("### 📸 Upload Crop Image")
    
    # File uploader with camera option
    uploaded_file = st.file_uploader(
        "Take a photo or upload from gallery",
        type=['jpg', 'jpeg', 'png'],
        help="Upload a clear photo of your crop for diagnosis"
    )
    
    if uploaded_file is not None:
        # Read image bytes
        image_bytes = uploaded_file.read()
        
        # Open with PIL
        try:
            image = Image.open(io.BytesIO(image_bytes))
            return image, image_bytes
        except Exception as e:
            st.error(f"Failed to load image: {str(e)}")
            return None
    
    return None


def render_image_preview(image: Image.Image) -> None:
    """
    Render image preview with quality indicators
    
    Args:
        image: PIL Image to preview
    """
    st.markdown("### 🖼️ Image Preview")
    
    # Display image
    st.image(image, use_container_width=True, caption="Uploaded Image")
    
    # Show image info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Width", f"{image.width}px")
    with col2:
        st.metric("Height", f"{image.height}px")
    with col3:
        st.metric("Format", image.format or "Unknown")


def validate_image_quality(image: Image.Image) -> Tuple[bool, str]:
    """
    Validate image quality for crop diagnosis
    
    Args:
        image: PIL Image to validate
    
    Returns:
        Tuple of (is_valid, message)
    """
    # Check minimum resolution
    min_width = 300
    min_height = 300
    
    if image.width < min_width or image.height < min_height:
        return False, f"Image resolution too low. Minimum {min_width}x{min_height}px required."
    
    # Check maximum file size (already handled by Streamlit, but double-check)
    max_pixels = 4096 * 4096
    if image.width * image.height > max_pixels:
        return False, "Image resolution too high. Please use a smaller image."
    
    # Check if image is too dark or too bright
    try:
        # Convert to grayscale and check brightness
        grayscale = image.convert('L')
        pixels = list(grayscale.getdata())
        avg_brightness = sum(pixels) / len(pixels)
        
        if avg_brightness < 30:
            return False, "Image is too dark. Please take photo in better lighting."
        elif avg_brightness > 225:
            return False, "Image is too bright. Please avoid direct sunlight."
    except:
        pass  # Skip brightness check if it fails
    
    # Check if image is blurry (basic check using edge detection)
    try:
        from PIL import ImageFilter
        edges = image.filter(ImageFilter.FIND_EDGES)
        edge_pixels = list(edges.convert('L').getdata())
        edge_strength = sum(edge_pixels) / len(edge_pixels)
        
        if edge_strength < 5:
            return False, "Image appears blurry. Please take a clearer photo focusing on the affected area."
    except:
        pass  # Skip blur check if it fails
    
    return True, "Image quality is good!"


def upload_image_to_s3(image_bytes: bytes, user_id: str, filename: str) -> Optional[str]:
    """
    Upload image to S3 for processing
    
    Args:
        image_bytes: Image data as bytes
        user_id: User identifier
        filename: Original filename
    
    Returns:
        S3 URL if successful, None otherwise
    """
    try:
        s3_client = boto3.client('s3')
        bucket_name = os.getenv('S3_BUCKET_NAME', 'missionai-images')
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = filename.split('.')[-1] if '.' in filename else 'jpg'
        s3_filename = f"images/{user_id}/{timestamp}.{ext}"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_filename,
            Body=image_bytes,
            ContentType=f'image/{ext}'
        )
        
        # Generate URL
        url = f"s3://{bucket_name}/{s3_filename}"
        return url
        
    except Exception as e:
        st.error(f"Failed to upload image: {str(e)}")
        return None


def render_image_quality_feedback(is_valid: bool, message: str) -> None:
    """
    Render image quality validation feedback
    
    Args:
        is_valid: Whether image passed quality checks
        message: Feedback message
    """
    if is_valid:
        st.success(f"✅ {message}")
    else:
        st.warning(f"⚠️ {message}")
        
        # Show tips for better photos
        with st.expander("📖 Tips for better photos"):
            st.markdown("""
            **For best results:**
            - Take photos in good natural lighting (avoid direct sunlight)
            - Focus on the affected area of the crop
            - Keep the camera steady to avoid blur
            - Fill the frame with the crop/leaf
            - Minimum resolution: 300x300 pixels
            - Avoid shadows and reflections
            """)


def compress_image(image: Image.Image, max_size_kb: int = 500) -> bytes:
    """
    Compress image to reduce file size
    
    Args:
        image: PIL Image to compress
        max_size_kb: Maximum file size in KB
    
    Returns:
        Compressed image bytes
    """
    # Start with high quality
    quality = 95
    
    while quality > 20:
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=quality, optimize=True)
        size_kb = len(buffer.getvalue()) / 1024
        
        if size_kb <= max_size_kb:
            return buffer.getvalue()
        
        quality -= 5
    
    # If still too large, resize
    buffer = io.BytesIO()
    max_dimension = 1024
    image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    image.save(buffer, format='JPEG', quality=85, optimize=True)
    return buffer.getvalue()


def render_image_upload_with_validation() -> Optional[Tuple[str, Image.Image]]:
    """
    Render complete image upload flow with validation and S3 upload
    
    Returns:
        Tuple of (S3 URL, PIL Image) if successful, None otherwise
    """
    result = render_image_upload()
    
    if result is None:
        return None
    
    image, image_bytes = result
    
    # Show preview
    render_image_preview(image)
    
    # Validate quality
    is_valid, message = validate_image_quality(image)
    render_image_quality_feedback(is_valid, message)
    
    if not is_valid:
        return None
    
    # Upload to S3
    if st.button("✅ Use this image", type="primary"):
        with st.spinner("Uploading image..."):
            user_id = st.session_state.get('user_id', 'anonymous')
            s3_url = upload_image_to_s3(image_bytes, user_id, "crop_image.jpg")
            
            if s3_url:
                st.success("Image uploaded successfully!")
                return s3_url, image
            else:
                st.error("Failed to upload image. Please try again.")
                return None
    
    return None
