"""
RISE Best Practice Sharing Example
Demonstrates how to use the best practice sharing tools
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.best_practice_tools import BestPracticeTools
import json


def main():
    """Run best practice sharing examples"""
    
    print("=" * 80)
    print("RISE Best Practice Sharing Examples")
    print("=" * 80)
    
    # Initialize tools
    best_practice_tools = BestPracticeTools(region='us-east-1')
    
    # Example 1: Submit a new practice
    print("\n1. Submitting a New Best Practice")
    print("-" * 80)
    
    practice_data = {
        'user_id': 'farmer_ravi_001',
        'title': 'जैविक खाद से गेहूं की उपज बढ़ाना',
        'description': 'यह विधि जैविक खाद का उपयोग करके गेहूं की उपज में 20-25% की वृद्धि करती है। मैंने इसे पिछले 3 सालों से अपने खेत में सफलतापूर्वक उपयोग किया है।',
        'language': 'hi',
        'category': {
            'crop_type': 'wheat',
            'practice_type': 'organic_farming',
            'region': 'north_india'
        },
        'steps': [
            'खेत की तैयारी के समय 5 टन प्रति एकड़ गोबर की खाद मिलाएं',
            'बुवाई से पहले बीजों को जैविक कल्चर से उपचारित करें',
            'फसल की वृद्धि के दौरान वर्मीकम्पोस्ट का छिड़काव करें (2 टन प्रति एकड़)',
            'नीम की खली का उपयोग कीट नियंत्रण के लिए करें (50 किलो प्रति एकड़)',
            'फसल के बाद हरी खाद के लिए मूंग या ढैंचा उगाएं'
        ],
        'expected_benefits': {
            'yield_increase': 22.5,
            'cost_reduction': 15,
            'soil_health_improvement': 'high',
            'sustainability_score': 9
        },
        'resources_needed': [
            'गोबर की खाद (5 टन/एकड़)',
            'वर्मीकम्पोस्ट (2 टन/एकड़)',
            'नीम की खली (50 किलो/एकड़)',
            'जैविक कल्चर',
            'हरी खाद के बीज'
        ]
    }
    
    result = best_practice_tools.submit_practice(**practice_data)
    
    if result['success']:
        print(f"✅ Practice submitted successfully!")
        print(f"   Practice ID: {result['practice_id']}")
        print(f"   Validation Score: {result['validation_score']}/100")
        print(f"   Scientific References: {len(result.get('scientific_references', []))}")
        
        if result.get('scientific_references'):
            print("\n   References found:")
            for ref in result['scientific_references'][:3]:
                print(f"   • {ref}")
        
        practice_id = result['practice_id']
    else:
        print(f"❌ Failed to submit practice: {result.get('error')}")
        if result.get('suggestions'):
            print("\n   Suggestions:")
            for suggestion in result['suggestions']:
                print(f"   • {suggestion}")
        return
    
    # Example 2: Browse practices
    print("\n\n2. Browsing Best Practices")
    print("-" * 80)
    
    result = best_practice_tools.get_practices(
        category={'crop_type': 'wheat'},
        sort_by='success_rate',
        limit=5
    )
    
    if result['success']:
        print(f"Found {result['count']} wheat farming practices")
        print("\nTop practices by success rate:")
        
        for i, practice in enumerate(result['practices'][:3], 1):
            print(f"\n{i}. {practice['title']}")
            print(f"   Success Rate: {practice.get('avg_success_rate', 0):.1f}%")
            print(f"   Adoptions: {practice.get('adoption_count', 0)}")
            print(f"   Validation: {practice.get('validation_score', 0)}/100")
    
    # Example 3: Get practice details
    print("\n\n3. Getting Practice Details")
    print("-" * 80)
    
    result = best_practice_tools.get_practice(practice_id)
    
    if result['success']:
        practice = result['practice']
        print(f"Practice: {practice['title']}")
        print(f"\nDescription:")
        print(f"{practice['description']}")
        
        print(f"\nImplementation Steps:")
        for i, step in enumerate(practice['steps'], 1):
            print(f"{i}. {step}")
        
        print(f"\nExpected Benefits:")
        benefits = practice['expected_benefits']
        print(f"• Yield Increase: +{benefits.get('yield_increase', 0)}%")
        print(f"• Cost Reduction: -{benefits.get('cost_reduction', 0)}%")
        print(f"• Soil Health: {benefits.get('soil_health_improvement', 'N/A')}")
        print(f"• Sustainability: {benefits.get('sustainability_score', 0)}/10")
    
    # Example 4: Adopt a practice
    print("\n\n4. Adopting a Practice")
    print("-" * 80)
    
    result = best_practice_tools.adopt_practice(
        practice_id=practice_id,
        user_id='farmer_lakshmi_002',
        implementation_date='2024-11-01',
        notes='Planning to implement on 3 acres. Will track results carefully.'
    )
    
    if result['success']:
        print(f"✅ Practice adopted successfully!")
        print(f"   Adoption ID: {result['adoption_id']}")
        print(f"   Start tracking your implementation progress")
        
        adoption_id = result['adoption_id']
    
    # Example 5: Submit feedback
    print("\n\n5. Submitting Feedback on Adopted Practice")
    print("-" * 80)
    
    result = best_practice_tools.submit_feedback(
        adoption_id=adoption_id,
        user_id='farmer_lakshmi_002',
        success=True,
        feedback='बहुत अच्छे परिणाम मिले! मेरी गेहूं की उपज 24% बढ़ गई और लागत में भी 18% की कमी आई। मिट्टी की गुणवत्ता में भी सुधार दिखाई दे रहा है।',
        results={
            'yield_change': 24.0,
            'cost_change': -18.0,
            'soil_quality_improvement': True,
            'implementation_difficulty': 'medium',
            'time_to_results': '4 months'
        }
    )
    
    if result['success']:
        print(f"✅ Feedback submitted successfully!")
        print(f"   Your feedback helps other farmers make informed decisions")
    
    # Example 6: Get practice analytics
    print("\n\n6. Viewing Practice Analytics")
    print("-" * 80)
    
    result = best_practice_tools.get_adoption_analytics(practice_id)
    
    if result['success']:
        analytics = result['analytics']
        
        print(f"Practice Analytics:")
        print(f"\nAdoption Metrics:")
        print(f"• Total Adoptions: {analytics['total_adoptions']}")
        print(f"• Completed: {analytics['completed_adoptions']}")
        print(f"• Successful: {analytics['successful_adoptions']}")
        print(f"• Success Rate: {analytics['success_rate']:.1f}%")
        
        print(f"\nAverage Impact:")
        print(f"• Yield Change: {analytics['avg_yield_change']:+.1f}%")
        print(f"• Cost Change: {analytics['avg_cost_change']:+.1f}%")
        
        print(f"\nTrend: {analytics['adoption_trend'].title()}")
        print(f"Validation Score: {analytics['validation_score']}/100")
    
    # Example 7: Search practices
    print("\n\n7. Searching for Practices")
    print("-" * 80)
    
    result = best_practice_tools.search_practices(
        query='organic pest control',
        limit=5
    )
    
    if result['success']:
        print(f"Found {result['count']} practices matching 'organic pest control'")
        
        for i, practice in enumerate(result['practices'][:3], 1):
            print(f"\n{i}. {practice['title']}")
            print(f"   Category: {practice['category'].get('practice_type', 'N/A')}")
            print(f"   Success Rate: {practice.get('avg_success_rate', 0):.1f}%")
    
    # Example 8: Translate practice
    print("\n\n8. Translating Practice to English")
    print("-" * 80)
    
    result = best_practice_tools.translate_practice(
        practice_id=practice_id,
        target_language='en'
    )
    
    if result['success'] and result.get('translated'):
        practice = result['practice']
        print(f"Translated Practice:")
        print(f"Title: {practice['title']}")
        print(f"\nDescription:")
        print(f"{practice['description']}")
        
        print(f"\nSteps:")
        for i, step in enumerate(practice['steps'][:3], 1):
            print(f"{i}. {step}")
    
    # Example 9: Get user contributions
    print("\n\n9. Viewing User Contributions")
    print("-" * 80)
    
    result = best_practice_tools.get_user_contributions('farmer_ravi_001')
    
    if result['success']:
        contributions = result['contributions']
        
        print(f"User Contribution Summary:")
        print(f"• Total Practices Shared: {contributions['total_practices']}")
        print(f"• Total Adoptions: {contributions['total_adoptions']}")
        print(f"• Successful Implementations: {contributions['total_successful']}")
        print(f"• Average Success Rate: {contributions['avg_success_rate']:.1f}%")
        
        if contributions.get('most_popular_practice'):
            most_popular = contributions['most_popular_practice']
            print(f"\nMost Popular Practice:")
            print(f"• {most_popular['title']}")
            print(f"• {most_popular['adoptions']} adoptions")
    
    print("\n" + "=" * 80)
    print("Examples completed successfully!")
    print("=" * 80)


if __name__ == '__main__':
    main()
