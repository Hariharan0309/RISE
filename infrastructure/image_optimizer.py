"""
RISE Image Optimization Service
Handles WebP conversion, progressive loading, and image compression
"""

import io
import base64
from typing import Dict, Any, Optional, Tuple
from PIL import Image
import os


class ImageProcessor:
    """Process and optimize images for rural networks"""
    
    SUPPORTED_FORMATS = ['JPEG', 'PNG', 'WEBP', 'BMP', 'TIFF']
    
    @staticmethod
    def optimize_image(
        image_data: bytes,
        target_width: Optional[int] = None,
        quality: int = 75,
        output_format: str = 'WEBP'
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Optimize image with resizing and format conversion
        
        Args:
            image_data: Original image bytes
            target_width: Target width (maintains aspect ratio)
            quality: Output quality (1-100)
            output_format: Output format ('WEBP', 'JPEG', etc.)
        
        Returns:
            Tuple of (optimized_bytes, metadata)
        """
        # Open image
        img = Image.open(io.BytesIO(image_data))
        original_format = img.format
        original_size = len(image_data)
        original_width, original_height = img.size
        
        # Convert RGBA to RGB if saving as JPEG
        if output_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize if target width specified
        if target_width and target_width < original_width:
            aspect_ratio = original_height / original_width
            target_height = int(target_width * aspect_ratio)
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Save optimized image
        output_buffer = io.BytesIO()
        
        if output_format == 'WEBP':
            img.save(
                output_buffer,
                format='WEBP',
                quality=quality,
                method=6,  # Best compression
                lossless=False
            )
        elif output_format == 'JPEG':
            img.save(
                output_buffer,
                format='JPEG',
                quality=quality,
                optimize=True,
                progressive=True
            )
        else:
            img.save(output_buffer, format=output_format, quality=quality)
        
        optimized_data = output_buffer.getvalue()
        optimized_size = len(optimized_data)
        
        # Calculate savings
        savings_percent = ((original_size - optimized_size) / original_size * 100) if original_size > 0 else 0
        
        metadata = {
            'original_format': original_format,
            'output_format': output_format,
            'original_size_bytes': original_size,
            'optimized_size_bytes': optimized_size,
            'savings_bytes': original_size - optimized_size,
            'savings_percent': round(savings_percent, 2),
            'original_dimensions': {'width': original_width, 'height': original_height},
            'output_dimensions': {'width': img.width, 'height': img.height},
            'quality': quality
        }
        
        return optimized_data, metadata
    
    @staticmethod
    def create_progressive_versions(
        image_data: bytes,
        sizes: list = [320, 640, 1024],
        quality: int = 75
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create multiple progressive versions of an image
        
        Args:
            image_data: Original image bytes
            sizes: List of target widths
            quality: Output quality
        
        Returns:
            Dict mapping size to optimized image data and metadata
        """
        versions = {}
        
        for size in sizes:
            optimized_data, metadata = ImageProcessor.optimize_image(
                image_data,
                target_width=size,
                quality=quality,
                output_format='WEBP'
            )
            
            versions[f"{size}w"] = {
                'data': optimized_data,
                'metadata': metadata,
                'base64': base64.b64encode(optimized_data).decode('utf-8')
            }
        
        return versions
    
    @staticmethod
    def create_placeholder(
        image_data: bytes,
        width: int = 20,
        quality: int = 10
    ) -> str:
        """
        Create tiny placeholder image for progressive loading
        
        Args:
            image_data: Original image bytes
            width: Placeholder width (very small)
            quality: Placeholder quality (very low)
        
        Returns:
            Base64 encoded placeholder image
        """
        optimized_data, _ = ImageProcessor.optimize_image(
            image_data,
            target_width=width,
            quality=quality,
            output_format='WEBP'
        )
        
        return base64.b64encode(optimized_data).decode('utf-8')
    
    @staticmethod
    def get_image_info(image_data: bytes) -> Dict[str, Any]:
        """
        Get image information without processing
        
        Args:
            image_data: Image bytes
        
        Returns:
            Image information dict
        """
        img = Image.open(io.BytesIO(image_data))
        
        return {
            'format': img.format,
            'mode': img.mode,
            'size_bytes': len(image_data),
            'width': img.width,
            'height': img.height,
            'aspect_ratio': round(img.width / img.height, 2) if img.height > 0 else 0
        }
    
    @staticmethod
    def validate_image(image_data: bytes, max_size_mb: int = 5) -> Tuple[bool, Optional[str]]:
        """
        Validate image data
        
        Args:
            image_data: Image bytes
            max_size_mb: Maximum allowed size in MB
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check size
        size_mb = len(image_data) / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f"Image too large: {size_mb:.2f}MB (max {max_size_mb}MB)"
        
        # Try to open image
        try:
            img = Image.open(io.BytesIO(image_data))
            
            # Check format
            if img.format not in ImageProcessor.SUPPORTED_FORMATS:
                return False, f"Unsupported format: {img.format}"
            
            # Check dimensions
            if img.width < 100 or img.height < 100:
                return False, f"Image too small: {img.width}x{img.height} (min 100x100)"
            
            if img.width > 10000 or img.height > 10000:
                return False, f"Image too large: {img.width}x{img.height} (max 10000x10000)"
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid image: {str(e)}"


class S3ImageOptimizer:
    """Optimize images stored in S3"""
    
    def __init__(self, s3_client=None, bucket_name: str = None):
        """
        Initialize S3 image optimizer
        
        Args:
            s3_client: Boto3 S3 client
            bucket_name: S3 bucket name
        """
        self.s3_client = s3_client
        self.bucket_name = bucket_name or os.environ.get('S3_BUCKET_NAME')
    
    def optimize_and_upload(
        self,
        image_data: bytes,
        s3_key: str,
        network_type: str = '3g',
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Optimize image and upload multiple versions to S3
        
        Args:
            image_data: Original image bytes
            s3_key: Base S3 key (without size suffix)
            network_type: Network type for optimization
            metadata: Additional S3 metadata
        
        Returns:
            Dict with S3 keys and URLs for all versions
        """
        from network_optimization import NetworkOptimizer
        
        # Get adaptive config
        config = NetworkOptimizer.get_adaptive_config(network_type)
        
        # Create progressive versions
        sizes = [320, 640, 1024]  # Standard sizes
        versions = ImageProcessor.create_progressive_versions(
            image_data,
            sizes=sizes,
            quality=config['image_quality']
        )
        
        # Create placeholder
        placeholder = ImageProcessor.create_placeholder(image_data)
        
        results = {
            'original_key': s3_key,
            'versions': {},
            'placeholder': placeholder
        }
        
        # Upload each version to S3
        if self.s3_client and self.bucket_name:
            for size_key, version_data in versions.items():
                # Create S3 key with size suffix
                key_parts = s3_key.rsplit('.', 1)
                versioned_key = f"{key_parts[0]}_{size_key}.webp"
                
                # Upload to S3
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=versioned_key,
                    Body=version_data['data'],
                    ContentType='image/webp',
                    Metadata=metadata or {},
                    CacheControl='public, max-age=31536000'  # 1 year
                )
                
                results['versions'][size_key] = {
                    'key': versioned_key,
                    'url': f"https://{self.bucket_name}.s3.amazonaws.com/{versioned_key}",
                    'metadata': version_data['metadata']
                }
        
        return results


# Export main classes
__all__ = [
    'ImageProcessor',
    'S3ImageOptimizer'
]
