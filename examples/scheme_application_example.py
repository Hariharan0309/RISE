"""
RISE Scheme Application Example
Demonstrates usage of scheme application assistance tools
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.scheme_application_tools import SchemeApplicationTools
import json


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def example_generate_wizard():
    """Example: Generate application wizard"""
    print_section("Example 1: Generate Application Wizard")
    
    tools = SchemeApplicationTools(region='us-east-1')
    
    # Generate wizard for PM-KISAN scheme
    result = tools.generate_application_wizard(
        user_id='user_12345',
        scheme_id='SCH_PM_KISAN',
        language='hi'
    )
    
    if result['success']:
        print(f"✅ Wizard generated for: {result['scheme_name']}")
        print(f"Total Steps: {result['total_steps']}")
        print(f"Estimated Time: {result['estimated_time_minutes']} minutes")
        print(f"Language: {result['language']}")
        print("\nWizard Steps:")
        
        for step in result['wizard_steps']:
            print(f"\n  Step {step['step_number']}: {step['title']}")
            print(f"  Description: {step['description']}")
            print(f"  Time: {step['estimated_time_minutes']} minutes")
            print(f"  Instructions:")
            for instruction in step['instructions'][:3]:
                print(f"    - {instruction}")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_validate_documents():
    """Example: Validate documents"""
    print_section("Example 2: Validate Documents")
    
    tools = SchemeApplicationTools(region='us-east-1')
    
    # Sample documents
    documents = [
        {
            'name': 'Aadhaar Card',
            'format': 'pdf',
            'size_mb': 1.5,
            's3_key': 'documents/aadhaar_123.pdf'
        },
        {
            'name': 'Land Records',
            'format': 'pdf',
            'size_mb': 3.2,
            's3_key': 'documents/land_records_123.pdf'
        },
        {
            'name': 'Bank Passbook',
            'format': 'jpg',
            'size_mb': 1.0,
            's3_key': 'documents/bank_passbook_123.jpg'
        }
    ]
    
    result = tools.validate_documents(documents, 'SCH_PM_KISAN')
    
    if result['success']:
        print(f"Validation Status: {'✅ All Valid' if result['all_valid'] else '⚠️ Issues Found'}")
        print(f"Total Documents: {result['total_documents']}")
        print(f"Required Documents: {result['required_documents']}")
        
        print("\nValidation Results:")
        for validation in result['validation_results']:
            status = "✅" if validation['valid'] else "❌"
            print(f"  {status} {validation['document_name']}")
            if not validation['valid']:
                for issue in validation['issues']:
                    print(f"      - {issue}")
        
        if result['missing_documents']:
            print("\n⚠️ Missing Documents:")
            for doc in result['missing_documents']:
                print(f"  - {doc}")
        
        print(f"\nSummary: {result['validation_summary']}")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_submit_application():
    """Example: Submit application"""
    print_section("Example 3: Submit Application")
    
    tools = SchemeApplicationTools(region='us-east-1')
    
    # Application data
    application_data = {
        'personal_info': {
            'full_name': 'Ravi Kumar',
            'father_name': 'Ram Kumar',
            'date_of_birth': '1985-05-15',
            'gender': 'Male'
        },
        'contact_info': {
            'mobile': '+91 9876543210',
            'email': 'ravi.kumar@example.com',
            'address': 'Village Rampur, District Lucknow, Uttar Pradesh'
        },
        'bank_details': {
            'bank_name': 'State Bank of India',
            'account_number': '1234567890',
            'ifsc_code': 'SBIN0001234',
            'account_holder': 'Ravi Kumar'
        },
        'documents': [
            {'name': 'Aadhaar Card', 'format': 'pdf', 'size_mb': 1.5},
            {'name': 'Land Records', 'format': 'pdf', 'size_mb': 3.0},
            {'name': 'Bank Passbook', 'format': 'jpg', 'size_mb': 1.0}
        ],
        'declaration': True
    }
    
    result = tools.submit_application(
        user_id='user_12345',
        scheme_id='SCH_PM_KISAN',
        application_data=application_data
    )
    
    if result['success']:
        print("🎉 Application submitted successfully!")
        print(f"\nApplication ID: {result['application_id']}")
        print(f"Tracking Number: {result['tracking_number']}")
        print(f"Status: {result['status'].upper()}")
        
        receipt = result['receipt']
        print(f"\n📄 Receipt:")
        print(f"  Scheme: {receipt['scheme_name']}")
        print(f"  Submission Date: {receipt['submission_date']}")
        print(f"  Documents Submitted: {receipt['documents_submitted']}")
        print(f"  Message: {receipt['receipt_message']}")
        
        print("\n📝 Next Steps:")
        for i, step in enumerate(result['next_steps'], 1):
            print(f"  {i}. {step}")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_track_status():
    """Example: Track application status"""
    print_section("Example 4: Track Application Status")
    
    tools = SchemeApplicationTools(region='us-east-1')
    
    # Track application
    result = tools.track_application_status('APP_ABC123DEF456')
    
    if result['success']:
        print(f"Application ID: {result['application_id']}")
        print(f"Tracking Number: {result['tracking_number']}")
        print(f"Scheme: {result['scheme_name']}")
        print(f"\nCurrent Status: {result['current_status'].replace('_', ' ').title()}")
        print(f"Progress: {result['progress_percentage']}%")
        
        print(f"\nSubmission Date: {result['submission_date']}")
        print(f"Last Updated: {result['last_updated']}")
        print(f"Estimated Completion: {result['estimated_completion']}")
        
        print("\n📅 Status Timeline:")
        for entry in result['status_timeline']:
            print(f"  ✅ {entry['status'].replace('_', ' ').title()}")
            print(f"     Date: {entry['date']} at {entry['time']}")
            if entry['notes']:
                print(f"     Notes: {entry['notes']}")
        
        print(f"\n📌 Next Action: {result['next_action']}")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_send_notification():
    """Example: Send application notification"""
    print_section("Example 5: Send Application Notification")
    
    tools = SchemeApplicationTools(region='us-east-1')
    
    # Send notification
    result = tools.send_application_notification(
        user_id='user_12345',
        application_id='APP_ABC123DEF456',
        notification_type='submission_confirmation'
    )
    
    if result['success']:
        print("✅ Notification sent successfully!")
        print(f"\nNotification Type: {result['notification_type']}")
        print(f"Message: {result['message']}")
        print(f"Voice Audio URL: {result['voice_audio_url']}")
        print(f"Sent At: {result['sent_timestamp']}")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_complete_workflow():
    """Example: Complete application workflow"""
    print_section("Example 6: Complete Application Workflow")
    
    tools = SchemeApplicationTools(region='us-east-1')
    
    user_id = 'user_12345'
    scheme_id = 'SCH_PM_KISAN'
    
    print("Step 1: Generate Application Wizard")
    print("-" * 40)
    
    wizard_result = tools.generate_application_wizard(user_id, scheme_id, 'hi')
    
    if wizard_result['success']:
        print(f"✅ Wizard generated with {wizard_result['total_steps']} steps")
        print(f"   Estimated time: {wizard_result['estimated_time_minutes']} minutes")
    else:
        print(f"❌ Wizard generation failed")
        return
    
    print("\nStep 2: Validate Documents")
    print("-" * 40)
    
    documents = [
        {'name': 'Aadhaar Card', 'format': 'pdf', 'size_mb': 1.5},
        {'name': 'Land Records', 'format': 'pdf', 'size_mb': 3.0},
        {'name': 'Bank Passbook', 'format': 'jpg', 'size_mb': 1.0}
    ]
    
    validation_result = tools.validate_documents(documents, scheme_id)
    
    if validation_result['success'] and validation_result['all_valid']:
        print(f"✅ All {validation_result['total_documents']} documents validated")
    else:
        print(f"⚠️ Document validation issues found")
        return
    
    print("\nStep 3: Submit Application")
    print("-" * 40)
    
    application_data = {
        'personal_info': {'full_name': 'Ravi Kumar'},
        'contact_info': {'mobile': '+91 9876543210'},
        'bank_details': {'account_number': '1234567890'},
        'documents': documents,
        'declaration': True
    }
    
    submission_result = tools.submit_application(user_id, scheme_id, application_data)
    
    if submission_result['success']:
        print(f"✅ Application submitted successfully")
        print(f"   Application ID: {submission_result['application_id']}")
        print(f"   Tracking Number: {submission_result['tracking_number']}")
        
        application_id = submission_result['application_id']
    else:
        print(f"❌ Application submission failed")
        return
    
    print("\nStep 4: Track Application Status")
    print("-" * 40)
    
    status_result = tools.track_application_status(application_id)
    
    if status_result['success']:
        print(f"✅ Status: {status_result['current_status'].upper()}")
        print(f"   Progress: {status_result['progress_percentage']}%")
        print(f"   Next Action: {status_result['next_action']}")
    else:
        print(f"❌ Status tracking failed")
        return
    
    print("\nStep 5: Send Notification")
    print("-" * 40)
    
    notification_result = tools.send_application_notification(
        user_id, application_id, 'submission_confirmation'
    )
    
    if notification_result['success']:
        print(f"✅ Notification sent")
        print(f"   Type: {notification_result['notification_type']}")
    else:
        print(f"❌ Notification failed")
    
    print("\n" + "=" * 80)
    print("  ✅ Complete workflow executed successfully!")
    print("=" * 80)


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("  RISE Scheme Application Tools - Usage Examples")
    print("=" * 80)
    
    try:
        # Run individual examples
        example_generate_wizard()
        example_validate_documents()
        example_submit_application()
        example_track_status()
        example_send_notification()
        
        # Run complete workflow
        example_complete_workflow()
        
        print("\n" + "=" * 80)
        print("  All examples completed!")
        print("=" * 80 + "\n")
    
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
