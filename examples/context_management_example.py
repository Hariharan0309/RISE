"""
RISE Context Management Integration Example
Demonstrates conversation context persistence and retrieval
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import get_orchestrator, create_farming_session, ask_farming_question
from tools.context_tools import ContextTools
import time


def example_basic_context_management():
    """Example 1: Basic context management with persistence"""
    print("=" * 70)
    print("Example 1: Basic Context Management with DynamoDB Persistence")
    print("=" * 70)
    
    try:
        # Initialize orchestrator
        print("\n1. Initializing RISE orchestrator...")
        orchestrator = get_orchestrator()
        print("✓ Orchestrator initialized")
        
        # Create a farming session
        print("\n2. Creating farming session...")
        session_id = create_farming_session(
            user_id="farmer_ravi_001",
            language="hi",
            location="Uttar Pradesh",
            crops=["wheat", "rice"]
        )
        print(f"✓ Session created: {session_id}")
        
        # First query
        print("\n3. First query: Asking about wheat cultivation...")
        response1 = ask_farming_question(
            session_id=session_id,
            question="What are the best practices for wheat cultivation in Uttar Pradesh?",
            context={"crop": "wheat", "season": "rabi"}
        )
        
        if response1['success']:
            print(f"✓ Response received ({response1['duration_ms']:.2f}ms)")
            print(f"  Context persisted: {response1.get('context_persisted', False)}")
            print(f"  Response preview: {response1['response'][:150]}...")
        else:
            print(f"✗ Error: {response1.get('error')}")
        
        # Wait a moment
        time.sleep(1)
        
        # Follow-up query (should use context)
        print("\n4. Follow-up query: Asking about fertilizer (context-aware)...")
        response2 = ask_farming_question(
            session_id=session_id,
            question="What fertilizer should I use for it?",  # "it" refers to wheat from context
            context={"follow_up": True}
        )
        
        if response2['success']:
            print(f"✓ Response received ({response2['duration_ms']:.2f}ms)")
            print(f"  Message count: {response2['message_count']}")
            print(f"  Response preview: {response2['response'][:150]}...")
        else:
            print(f"✗ Error: {response2.get('error')}")
        
        # Get session stats
        print("\n5. Session statistics...")
        stats = orchestrator.get_session_stats(session_id)
        if stats:
            print(f"✓ Session stats:")
            print(f"  - User ID: {stats['user_id']}")
            print(f"  - Language: {stats['language']}")
            print(f"  - Messages: {stats['message_count']}")
            print(f"  - Created: {stats['created_at']}")
            print(f"  - Last activity: {stats['last_activity']}")
        
        print("\n" + "=" * 70)
        print("✓ Example 1 completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


def example_context_retrieval():
    """Example 2: Direct context retrieval from DynamoDB"""
    print("\n" + "=" * 70)
    print("Example 2: Direct Context Retrieval from DynamoDB")
    print("=" * 70)
    
    try:
        # Initialize context tools
        print("\n1. Initializing context tools...")
        context_tools = ContextTools(region='us-east-1')
        print("✓ Context tools initialized")
        
        # Create test session
        print("\n2. Creating test session with messages...")
        session_id = "demo_session_001"
        user_id = "demo_farmer_001"
        
        # Save some test messages
        messages = [
            ("user", "मेरे गेहूं के पौधों में पीले धब्बे हैं। क्या करूं?"),
            ("assistant", "पीले धब्बे नाइट्रोजन की कमी या रोग का संकेत हो सकते हैं। कृपया पत्तियों की फोटो भेजें।"),
            ("user", "मैं फोटो भेज रहा हूं।"),
            ("assistant", "यह पीला रतुआ रोग है। तुरंत प्रोपिकोनाज़ोल स्प्रे करें।"),
            ("user", "कितनी मात्रा में?"),
            ("assistant", "प्रति एकड़ 200ml प्रोपिकोनाज़ोल को 200 लीटर पानी में मिलाएं।")
        ]
        
        for role, content in messages:
            context_tools.save_conversation_message(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                metadata={'language': 'hi', 'crop': 'wheat'}
            )
        
        print(f"✓ Saved {len(messages)} messages")
        
        # Retrieve conversation history
        print("\n3. Retrieving conversation history...")
        history = context_tools.get_conversation_history(session_id, limit=10)
        print(f"✓ Retrieved {len(history)} messages")
        
        print("\n4. Conversation history:")
        for i, msg in enumerate(history, 1):
            role = "किसान" if msg['role'] == 'user' else "सहायक"
            print(f"   {i}. {role}: {msg['content'][:60]}...")
        
        # Get formatted context window
        print("\n5. Getting formatted context window...")
        context_window = context_tools.get_context_window(session_id, window_size=3)
        print("✓ Context window:")
        print(context_window)
        
        print("\n" + "=" * 70)
        print("✓ Example 2 completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


def example_conversation_summarization():
    """Example 3: Conversation summarization for long sessions"""
    print("\n" + "=" * 70)
    print("Example 3: Conversation Summarization")
    print("=" * 70)
    
    try:
        # Initialize context tools
        print("\n1. Initializing context tools...")
        context_tools = ContextTools(region='us-east-1')
        print("✓ Context tools initialized")
        
        # Create a long conversation
        print("\n2. Creating long conversation...")
        session_id = "long_session_001"
        user_id = "farmer_lakshmi_001"
        
        conversation = [
            ("user", "I want to start organic farming. Where should I begin?"),
            ("assistant", "Great choice! Start with soil testing and composting. What crops do you grow?"),
            ("user", "I grow tomatoes and cucumbers."),
            ("assistant", "Perfect! For organic tomatoes, use vermicompost and neem oil for pests."),
            ("user", "How much vermicompost per plant?"),
            ("assistant", "Use 2-3 kg per plant at planting time, then 1 kg every month."),
            ("user", "What about pest control?"),
            ("assistant", "Use neem oil spray (5ml per liter) weekly. Also plant marigolds as companion plants."),
            ("user", "When should I harvest?"),
            ("assistant", "Harvest tomatoes when fully colored but still firm, usually 60-80 days after transplanting."),
            ("user", "How do I store them?"),
            ("assistant", "Store at room temperature away from sunlight. Don't refrigerate unless overripe."),
        ]
        
        for role, content in conversation:
            context_tools.save_conversation_message(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                metadata={'language': 'en', 'topic': 'organic_farming'}
            )
        
        print(f"✓ Created conversation with {len(conversation)} messages")
        
        # Summarize the conversation
        print("\n3. Generating conversation summary...")
        summary_result = context_tools.summarize_conversation(session_id)
        
        if summary_result['success']:
            print("✓ Summary generated:")
            print(f"\n{summary_result['summary']}")
            print(f"\nBased on {summary_result['message_count']} messages")
        else:
            print(f"✗ Summarization failed: {summary_result.get('error')}")
        
        print("\n" + "=" * 70)
        print("✓ Example 3 completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


def example_session_restoration():
    """Example 4: Session restoration from DynamoDB"""
    print("\n" + "=" * 70)
    print("Example 4: Session Restoration from DynamoDB")
    print("=" * 70)
    
    try:
        # Initialize orchestrator
        print("\n1. Initializing orchestrator...")
        orchestrator = get_orchestrator()
        print("✓ Orchestrator initialized")
        
        # Create and use a session
        print("\n2. Creating initial session...")
        session_id = create_farming_session(
            user_id="farmer_arjun_001",
            language="en",
            location="Punjab"
        )
        print(f"✓ Session created: {session_id}")
        
        # Add some messages
        print("\n3. Adding messages to session...")
        ask_farming_question(
            session_id=session_id,
            question="What is the best time to plant rice in Punjab?"
        )
        
        ask_farming_question(
            session_id=session_id,
            question="What variety should I choose?"
        )
        
        print("✓ Messages added")
        
        # Simulate session cleanup (remove from memory)
        print("\n4. Simulating session cleanup...")
        orchestrator.cleanup_session(session_id)
        print("✓ Session removed from memory")
        
        # Restore session from DynamoDB
        print("\n5. Restoring session from DynamoDB...")
        restored_session_id = orchestrator.load_session_from_history(
            session_id=session_id,
            user_id="farmer_arjun_001"
        )
        
        if restored_session_id:
            print(f"✓ Session restored: {restored_session_id}")
            
            # Get stats to verify restoration
            stats = orchestrator.get_session_stats(restored_session_id)
            if stats:
                print(f"  - Messages restored: {stats['message_count']}")
                print(f"  - Conversation length: {stats['conversation_length']}")
        else:
            print("✗ Session restoration failed")
        
        print("\n" + "=" * 70)
        print("✓ Example 4 completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


def example_session_timeout():
    """Example 5: Session timeout and cleanup"""
    print("\n" + "=" * 70)
    print("Example 5: Session Timeout and Cleanup")
    print("=" * 70)
    
    try:
        # Initialize orchestrator
        print("\n1. Initializing orchestrator...")
        orchestrator = get_orchestrator()
        print("✓ Orchestrator initialized")
        
        # Create multiple sessions
        print("\n2. Creating multiple test sessions...")
        sessions = []
        for i in range(3):
            session_id = create_farming_session(
                user_id=f"test_farmer_{i:03d}",
                language="hi"
            )
            sessions.append(session_id)
        
        print(f"✓ Created {len(sessions)} sessions")
        print(f"  Active sessions: {orchestrator.get_active_sessions_count()}")
        
        # Check timeout status
        print("\n3. Checking session timeout status...")
        for session_id in sessions:
            is_timed_out = orchestrator.check_session_timeout(session_id, timeout_hours=24)
            print(f"  - {session_id[:20]}...: {'Timed out' if is_timed_out else 'Active'}")
        
        # Cleanup expired sessions
        print("\n4. Running session cleanup...")
        cleaned_count = orchestrator.cleanup_expired_sessions(timeout_hours=24)
        print(f"✓ Cleaned up {cleaned_count} expired sessions")
        print(f"  Active sessions remaining: {orchestrator.get_active_sessions_count()}")
        
        print("\n" + "=" * 70)
        print("✓ Example 5 completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("RISE Context Management Integration Examples")
    print("=" * 70)
    print("\nThese examples demonstrate:")
    print("1. Basic context management with DynamoDB persistence")
    print("2. Direct context retrieval from DynamoDB")
    print("3. Conversation summarization for long sessions")
    print("4. Session restoration from DynamoDB")
    print("5. Session timeout and cleanup")
    print("\nNote: Examples require AWS credentials and DynamoDB table setup")
    print("=" * 70)
    
    try:
        # Run examples
        example_basic_context_management()
        example_context_retrieval()
        example_conversation_summarization()
        example_session_restoration()
        example_session_timeout()
        
        print("\n" + "=" * 70)
        print("✓ All examples completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
