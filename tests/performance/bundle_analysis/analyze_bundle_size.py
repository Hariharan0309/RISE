"""
Bundle size analysis for RISE frontend.

Analyzes and reports on:
- JavaScript bundle sizes
- CSS bundle sizes
- Image assets
- Total page weight
- Compression effectiveness
- Optimization opportunities
"""

import os
import json
import gzip
import brotli
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))


class BundleAnalyzer:
    """Analyze bundle sizes and optimization."""
    
    # Size thresholds (bytes)
    JS_BUNDLE_TARGET = 200 * 1024  # 200KB
    CSS_BUNDLE_TARGET = 50 * 1024  # 50KB
    TOTAL_PAGE_TARGET = 1 * 1024 * 1024  # 1MB
    IMAGE_TARGET = 100 * 1024  # 100KB per image
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.static_dir = self.project_root / 'static'
        self.results = {
            'javascript': [],
            'css': [],
            'images': [],
            'other': []
        }
    
    def analyze_file(self, file_path):
        """Analyze a single file."""
        if not file_path.exists():
            return None
        
        # Get file size
        original_size = file_path.stat().st_size
        
        # Calculate compressed sizes
        with open(file_path, 'rb') as f:
            content = f.read()
        
        gzip_size = len(gzip.compress(content, compresslevel=9))
        brotli_size = len(brotli.compress(content, quality=11))
        
        return {
            'path': str(file_path.relative_to(self.project_root)),
            'original_size': original_size,
            'gzip_size': gzip_size,
            'brotli_size': brotli_size,
            'gzip_ratio': (1 - gzip_size / original_size) * 100 if original_size > 0 else 0,
            'brotli_ratio': (1 - brotli_size / original_size) * 100 if original_size > 0 else 0
        }
    
    def analyze_directory(self, directory, extensions, category):
        """Analyze all files with given extensions in directory."""
        if not directory.exists():
            print(f"⚠️  Directory not found: {directory}")
            return
        
        for ext in extensions:
            for file_path in directory.rglob(f'*{ext}'):
                if file_path.is_file():
                    result = self.analyze_file(file_path)
                    if result:
                        self.results[category].append(result)
    
    def analyze_all(self):
        """Analyze all assets."""
        print(f"\n{'='*70}")
        print(f"BUNDLE SIZE ANALYSIS")
        print(f"{'='*70}\n")
        
        # Analyze JavaScript
        print("Analyzing JavaScript files...")
        self.analyze_directory(self.static_dir, ['.js'], 'javascript')
        
        # Analyze CSS
        print("Analyzing CSS files...")
        self.analyze_directory(self.static_dir, ['.css'], 'css')
        
        # Analyze Images
        print("Analyzing image files...")
        self.analyze_directory(self.static_dir, ['.jpg', '.jpeg', '.png', '.webp', '.svg'], 'images')
        
        # Analyze other assets
        print("Analyzing other assets...")
        self.analyze_directory(self.static_dir, ['.woff', '.woff2', '.ttf', '.json'], 'other')
        
        print("✅ Analysis complete\n")
    
    def format_size(self, size_bytes):
        """Format size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f}MB"
    
    def print_category_report(self, category, target_size=None):
        """Print report for a category."""
        files = self.results[category]
        
        if not files:
            print(f"  No {category} files found")
            return
        
        total_original = sum(f['original_size'] for f in files)
        total_gzip = sum(f['gzip_size'] for f in files)
        total_brotli = sum(f['brotli_size'] for f in files)
        
        print(f"\n{category.upper()} FILES:")
        print(f"{'─'*70}")
        print(f"{'File':<40} {'Original':<12} {'Gzip':<12} {'Brotli':<12}")
        print(f"{'─'*70}")
        
        for file_info in sorted(files, key=lambda x: x['original_size'], reverse=True):
            name = Path(file_info['path']).name
            if len(name) > 37:
                name = name[:34] + '...'
            
            print(f"{name:<40} "
                  f"{self.format_size(file_info['original_size']):<12} "
                  f"{self.format_size(file_info['gzip_size']):<12} "
                  f"{self.format_size(file_info['brotli_size']):<12}")
        
        print(f"{'─'*70}")
        print(f"{'TOTAL':<40} "
              f"{self.format_size(total_original):<12} "
              f"{self.format_size(total_gzip):<12} "
              f"{self.format_size(total_brotli):<12}")
        
        avg_gzip_ratio = sum(f['gzip_ratio'] for f in files) / len(files)
        avg_brotli_ratio = sum(f['brotli_ratio'] for f in files) / len(files)
        
        print(f"\nCompression ratios:")
        print(f"  Gzip: {avg_gzip_ratio:.1f}% reduction")
        print(f"  Brotli: {avg_brotli_ratio:.1f}% reduction")
        
        if target_size:
            status = "✅ PASS" if total_gzip < target_size else "❌ FAIL"
            print(f"\nTarget: {self.format_size(target_size)}")
            print(f"Actual (gzipped): {self.format_size(total_gzip)}")
            print(f"Status: {status}")
    
    def print_summary(self):
        """Print overall summary."""
        print(f"\n{'='*70}")
        print(f"OVERALL SUMMARY")
        print(f"{'='*70}\n")
        
        total_original = sum(
            sum(f['original_size'] for f in self.results[cat])
            for cat in self.results
        )
        total_gzip = sum(
            sum(f['gzip_size'] for f in self.results[cat])
            for cat in self.results
        )
        total_brotli = sum(
            sum(f['brotli_size'] for f in self.results[cat])
            for cat in self.results
        )
        
        print(f"Total page weight:")
        print(f"  Original: {self.format_size(total_original)}")
        print(f"  Gzipped: {self.format_size(total_gzip)}")
        print(f"  Brotli: {self.format_size(total_brotli)}")
        
        overall_gzip_ratio = (1 - total_gzip / total_original) * 100 if total_original > 0 else 0
        overall_brotli_ratio = (1 - total_brotli / total_original) * 100 if total_original > 0 else 0
        
        print(f"\nOverall compression:")
        print(f"  Gzip: {overall_gzip_ratio:.1f}% reduction")
        print(f"  Brotli: {overall_brotli_ratio:.1f}% reduction")
        
        print(f"\nTarget: {self.format_size(self.TOTAL_PAGE_TARGET)}")
        status = "✅ PASS" if total_gzip < self.TOTAL_PAGE_TARGET else "❌ FAIL"
        print(f"Status: {status}")
        
        # Breakdown by category
        print(f"\nBreakdown by category:")
        for category in self.results:
            if self.results[category]:
                cat_size = sum(f['gzip_size'] for f in self.results[category])
                percentage = (cat_size / total_gzip) * 100 if total_gzip > 0 else 0
                print(f"  {category.capitalize()}: {self.format_size(cat_size)} ({percentage:.1f}%)")
    
    def print_recommendations(self):
        """Print optimization recommendations."""
        print(f"\n{'='*70}")
        print(f"OPTIMIZATION RECOMMENDATIONS")
        print(f"{'='*70}\n")
        
        recommendations = []
        
        # Check JavaScript size
        js_total = sum(f['gzip_size'] for f in self.results['javascript'])
        if js_total > self.JS_BUNDLE_TARGET:
            recommendations.append(
                f"⚠️  JavaScript bundle ({self.format_size(js_total)}) exceeds target "
                f"({self.format_size(self.JS_BUNDLE_TARGET)})\n"
                f"   • Consider code splitting\n"
                f"   • Implement lazy loading\n"
                f"   • Remove unused dependencies"
            )
        
        # Check CSS size
        css_total = sum(f['gzip_size'] for f in self.results['css'])
        if css_total > self.CSS_BUNDLE_TARGET:
            recommendations.append(
                f"⚠️  CSS bundle ({self.format_size(css_total)}) exceeds target "
                f"({self.format_size(self.CSS_BUNDLE_TARGET)})\n"
                f"   • Remove unused CSS\n"
                f"   • Use critical CSS inline\n"
                f"   • Consider CSS-in-JS for component styles"
            )
        
        # Check large images
        large_images = [f for f in self.results['images'] if f['original_size'] > self.IMAGE_TARGET]
        if large_images:
            recommendations.append(
                f"⚠️  {len(large_images)} images exceed {self.format_size(self.IMAGE_TARGET)}\n"
                f"   • Compress images\n"
                f"   • Use WebP format\n"
                f"   • Implement responsive images\n"
                f"   • Use lazy loading"
            )
        
        # Check compression ratios
        for category in ['javascript', 'css']:
            files = self.results[category]
            if files:
                avg_ratio = sum(f['brotli_ratio'] for f in files) / len(files)
                if avg_ratio < 50:  # Less than 50% compression
                    recommendations.append(
                        f"⚠️  {category.capitalize()} compression ratio is low ({avg_ratio:.1f}%)\n"
                        f"   • Enable Brotli compression\n"
                        f"   • Minify source files\n"
                        f"   • Remove comments and whitespace"
                    )
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}\n")
        else:
            print("✅ No optimization recommendations - bundle sizes are optimal!\n")
    
    def generate_report(self):
        """Generate complete report."""
        self.analyze_all()
        
        # Print category reports
        self.print_category_report('javascript', self.JS_BUNDLE_TARGET)
        self.print_category_report('css', self.CSS_BUNDLE_TARGET)
        self.print_category_report('images')
        self.print_category_report('other')
        
        # Print summary
        self.print_summary()
        
        # Print recommendations
        self.print_recommendations()
        
        print(f"{'='*70}\n")


def main():
    """Main entry point."""
    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    
    print(f"Analyzing bundles in: {project_root}")
    
    analyzer = BundleAnalyzer(project_root)
    analyzer.generate_report()
    
    # Save results to JSON
    output_file = script_dir / 'bundle_analysis_results.json'
    with open(output_file, 'w') as f:
        json.dump(analyzer.results, f, indent=2)
    
    print(f"📊 Detailed results saved to: {output_file}")


if __name__ == '__main__':
    main()
