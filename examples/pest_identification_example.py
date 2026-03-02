"""
RISE Pest Identification Integration Example
Demonstrates how to use the pest identification tools in the RISE application
"""

import sys
import os
from pathlib import Path
import base64
from PIL import Image
import io

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.pest_identification_tools import PestIdentificationTools


def create_sample_image():
    """Create a sample image for testing"""
    # Create a simple test image
    img = Image.new('RGB', (800, 600), color='lightgreen')
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=85)
    img_bytes.seek(0)
    
    return img_bytes.read()


def example_basic_pest_identification():
    """Example: Basic pest identification from image"""
    print("=" * 60)
    print("Example 1: Basic Pest Identification")
    print("=" * 60)
    
    # Initialize pest identification tools
    pest_tools = PestIdentificationTools(region='us-east-1')
    
    # Create or load an image
    image_data = create_sample_image()
    
    # Analyze the image
    result = pest_tools.analyze_pest_image(
        image_data=image_data,
        user_id='farmer_001',
        crop_type='wheat',
        additional_context='Small green insects on leaves, sticky residue present'
    )
    
    # Display results
    if result['success']:
        print(f"\n✓ Analysis successful!")
        print(f"Diagnosis ID: {result['diagnosis_id']}")
        print(f"\nPests Identified: {', '.join(result['pests'])}")
        print(f"Confidence Score: {result['confidence_score']:.1%}")
        print(f"Severity: {result['severity']}")
        print(f"Lifecycle Stage: {result['lifecycle_stage']}")
        print(f"Population Density: {result['population_density']}")
        
        print(f"\n--- Biological Controls ---")
        for control in result['biological_controls']:
            print(f"  • {control['type']}: {control['description']}")
        
        print(f"\n--- Cultural Controls ---")
        for control in result['cultural_controls']:
            print(f"  • {control['type']}: {control['description']}")
        
        print(f"\n--- Chemical Treatments (Last Resort) ---")
        for treatment in result['chemical_treatments']:
            print(f"  • {treatment['type']}: {treatment['description']}")
        
        print(f"\n--- Full Analysis ---")
        print(result['full_analysis'][:500] + "..." if len(result['full_analysis']) > 500 else result['full_analysis'])
    else:
        print(f"\n✗ Analysis failed: {result.get('error')}")
        if 'validation' in result:
            print(f"Validation issues: {result['validation']['issues']}")
            print(f"Guidance: {result['validation']['guidance']}")


def example_image_quality_validation():
    """Example: Image quality validation before analysis"""
    print("\n" + "=" * 60)
    print("Example 2: Image Quality Validation")
    print("=" * 60)
    
    pest_tools = PestIdentificationTools(region='us-east-1')
    
    # Create a low-resolution image
    small_img = Image.new('RGB', (200, 150), color='green')
    small_img_bytes = io.BytesIO()
    small_img.save(small_img_bytes, format='JPEG')
    small_img_bytes.seek(0)
    
    # Validate image quality
    validation = pest_tools.validate_image_quality(small_img_bytes.read())
    
    print(f"\nImage Validation Results:")
    print(f"Valid: {validation['valid']}")
    print(f"Dimensions: {validation['dimensions']}")
    print(f"File Size: {validation['file_size_kb']:.1f} KB")
    
    if not validation['valid']:
        print(f"\nIssues Found:")
        for issue in validation['issues']:
            print(f"  • {issue}")
        
        print(f"\nGuidance:")
        for guide in validation['guidance']:
            print(f"  • {guide}")


def example_pest_diagnosis_history():
    """Example: Retrieve pest diagnosis history"""
    print("\n" + "=" * 60)
    print("Example 3: Pest Diagnosis History")
    print("=" * 60)
    
    pest_tools = PestIdentificationTools(region='us-east-1')
    
    # Get diagnosis history for a user
    history = pest_tools.get_pest_diagnosis_history('farmer_001', limit=5)
    
    print(f"\nFound {len(history)} diagnosis records:")
    
    for i, record in enumerate(history, 1):
        print(f"\n{i}. Diagnosis ID: {record.get('diagnosis_id')}")
        print(f"   Pests: {', '.join(record.get('pests', []))}")
        print(f"   Severity: {record.get('severity')}")
        print(f"   Lifecycle Stage: {record.get('lifecycle_stage')}")
        print(f"   Crop Type: {record.get('crop_type')}")
        print(f"   Status: {record.get('follow_up_status')}")


def example_follow_up_update():
    """Example: Update follow-up status after treatment"""
    print("\n" + "=" * 60)
    print("Example 4: Update Follow-up Status")
    print("=" * 60)
    
    pest_tools = PestIdentificationTools(region='us-east-1')
    
    # Update follow-up status
    success = pest_tools.update_follow_up_status(
        diagnosis_id='pest_abc123',
        status='controlled',
        notes='Applied neem oil spray for 3 days. Aphid population reduced by 80%. Will continue monitoring.'
    )
    
    if success:
        print("\n✓ Follow-up status updated successfully")
    else:
        print("\n✗ Failed to update follow-up status")


def example_pest_knowledge_base():
    """Example: Add and retrieve pest knowledge"""
    print("\n" + "=" * 60)
    print("Example 5: Pest Knowledge Base")
    print("=" * 60)
    
    pest_tools = PestIdentificationTools(region='us-east-1')
    
    # Add pest knowledge
    print("\nAdding pest knowledge to database...")
    success = pest_tools.add_pest_knowledge(
        pest_name='Aphids',
        scientific_name='Aphis gossypii',
        common_hosts=['cotton', 'wheat', 'vegetables', 'fruit trees'],
        lifecycle_info={
            'egg_duration': '4-10 days',
            'nymph_duration': '7-10 days',
            'adult_lifespan': '20-30 days',
            'reproduction': 'parthenogenetic (asexual)',
            'generations_per_year': '10-20',
            'overwintering': 'eggs on woody plants'
        },
        control_methods={
            'biological': [
                'Ladybugs (Coccinellidae)',
                'Lacewings (Chrysoperla)',
                'Parasitic wasps (Aphidius)',
                'Hoverfly larvae'
            ],
            'cultural': [
                'Crop rotation',
                'Remove weeds and alternate hosts',
                'Use reflective mulches',
                'Maintain plant vigor',
                'Companion planting with garlic, chives'
            ],
            'biopesticides': [
                'Neem oil (Azadirachtin)',
                'Insecticidal soap',
                'Horticultural oils',
                'Beauveria bassiana (fungal)'
            ],
            'chemical': [
                'Imidacloprid (systemic)',
                'Pyrethroids (contact)',
                'Use only as last resort'
            ]
        }
    )
    
    if success:
        print("✓ Pest knowledge added successfully")
    
    # Retrieve pest knowledge
    print("\nRetrieving pest knowledge...")
    knowledge = pest_tools.get_pest_knowledge('Aphids')
    
    if knowledge:
        print(f"\n--- Pest Information: {knowledge['pest_name']} ---")
        print(f"Scientific Name: {knowledge['scientific_name']}")
        print(f"Common Hosts: {', '.join(knowledge['common_hosts'])}")
        
        print(f"\nLifecycle Information:")
        for key, value in knowledge['lifecycle_info'].items():
            print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        print(f"\nControl Methods:")
        for method_type, methods in knowledge['control_methods'].items():
            print(f"  {method_type.upper()}:")
            for method in methods:
                print(f"    - {method}")


def example_integrated_workflow():
    """Example: Complete integrated pest management workflow"""
    print("\n" + "=" * 60)
    print("Example 6: Integrated Pest Management Workflow")
    print("=" * 60)
    
    pest_tools = PestIdentificationTools(region='us-east-1')
    
    print("\nStep 1: Farmer uploads pest image")
    image_data = create_sample_image()
    
    print("Step 2: Validate image quality")
    validation = pest_tools.validate_image_quality(image_data)
    
    if not validation['valid']:
        print(f"✗ Image quality issues: {validation['issues']}")
        print("Please retake photo following guidance:")
        for guide in validation['guidance']:
            print(f"  • {guide}")
        return
    
    print("✓ Image quality acceptable")
    
    print("\nStep 3: Analyze pest image")
    result = pest_tools.analyze_pest_image(
        image_data=image_data,
        user_id='farmer_001',
        crop_type='wheat',
        additional_context='Noticed yesterday, spreading quickly'
    )
    
    if not result['success']:
        print(f"✗ Analysis failed: {result.get('error')}")
        return
    
    print(f"✓ Pest identified: {', '.join(result['pests'])}")
    print(f"  Severity: {result['severity']}")
    print(f"  Lifecycle Stage: {result['lifecycle_stage']}")
    print(f"  Population Density: {result['population_density']}")
    
    print("\nStep 4: Provide IPM recommendations")
    print("\n🌱 PRIORITY 1: Biological Controls (Try First)")
    for control in result['biological_controls']:
        print(f"  • {control['description']}")
    
    print("\n🌾 PRIORITY 2: Cultural Controls")
    for control in result['cultural_controls']:
        print(f"  • {control['description']}")
    
    print("\n⚠️  PRIORITY 3: Chemical Treatments (Last Resort)")
    for treatment in result['chemical_treatments']:
        print(f"  • {treatment['description']}")
    
    print("\nStep 5: Farmer implements biological control")
    print("  → Applied neem oil spray")
    print("  → Introduced ladybugs")
    
    print("\nStep 6: Update follow-up status after 3 days")
    pest_tools.update_follow_up_status(
        diagnosis_id=result['diagnosis_id'],
        status='improving',
        notes='Biological controls working. Pest population reduced by 60%.'
    )
    print("✓ Follow-up recorded")
    
    print("\n✓ IPM workflow completed successfully!")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("RISE Pest Identification System - Examples")
    print("=" * 60)
    
    try:
        # Run examples
        example_basic_pest_identification()
        example_image_quality_validation()
        example_pest_diagnosis_history()
        example_follow_up_update()
        example_pest_knowledge_base()
        example_integrated_workflow()
        
        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
