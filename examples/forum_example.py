"""
RISE Multilingual Farmer Forums - Example Usage
Demonstrates forum functionality with translation and moderation
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.forum_tools import create_forum_tools
import json


def main():
    """Demonstrate forum tools functionality"""
    
    print("=" * 70)
    print("RISE Multilingual Farmer Forums - Example")
    print("=" * 70)
    
    # Initialize forum tools
    print("\n1. Initializing forum tools...")
    forum_tools = create_forum_tools(region='us-east-1')
    print("✓ Forum tools initialized")
    
    # Example 1: Create a post in Hindi
    print("\n2. Creating a post in Hindi...")
    post_result = forum_tools.create_post(
        user_id='farmer_ravi_001',
        title='गेहूं की खेती के लिए सर्वोत्तम प्रथाएं',
        content='''मैं उत्तर प्रदेश में 2 एकड़ जमीन पर गेहूं उगा रहा हूं। 
        क्या कोई मुझे बता सकता है कि:
        1. सबसे अच्छी किस्म कौन सी है?
        2. उर्वरक कब डालना चाहिए?
        3. सिंचाई कितनी बार करनी चाहिए?
        
        कृपया अपने अनुभव साझा करें।''',
        language='hi',
        category={
            'crop_type': 'wheat',
            'region': 'north_india',
            'method': 'traditional'
        },
        tags=['wheat', 'fertilizer', 'irrigation', 'advice']
    )
    
    if post_result['success']:
        print(f"✓ Post created successfully!")
        print(f"  Post ID: {post_result['post_id']}")
        print(f"  Sentiment Score: {post_result.get('sentiment_score', 0):.2f}")
        post_id = post_result['post_id']
    else:
        print(f"✗ Failed to create post: {post_result.get('error')}")
        return
    
    # Example 2: Get the post
    print("\n3. Retrieving the post...")
    get_result = forum_tools.get_post(post_id)
    
    if get_result['success']:
        post = get_result['post']
        print(f"✓ Post retrieved:")
        print(f"  Title: {post['title']}")
        print(f"  Language: {post['original_language']}")
        print(f"  Views: {post.get('views_count', 0)}")
    else:
        print(f"✗ Failed to get post: {get_result.get('error')}")
    
    # Example 3: Translate post to English
    print("\n4. Translating post to English...")
    translate_result = forum_tools.translate_post(post_id, 'en')
    
    if translate_result['success'] and translate_result.get('translated'):
        translated_post = translate_result['post']
        print(f"✓ Post translated:")
        print(f"  Original Title: {translated_post['original_title']}")
        print(f"  Translated Title: {translated_post['title']}")
        print(f"  From: {translate_result['source_language']} → To: {translate_result['target_language']}")
    elif translate_result['success']:
        print("ℹ Post already in target language")
    else:
        print(f"✗ Translation failed: {translate_result.get('error')}")
    
    # Example 4: Add a reply in English
    print("\n5. Adding a reply in English...")
    reply_result = forum_tools.add_reply(
        post_id=post_id,
        user_id='farmer_lakshmi_002',
        content='''Great question! I've been growing wheat for 10 years in Karnataka.
        
        Here are my recommendations:
        1. HD-2967 or PBW-343 varieties work well
        2. Apply fertilizer at sowing and 21 days after
        3. Irrigate 4-5 times during the season
        
        Feel free to ask if you need more details!''',
        language='en'
    )
    
    if reply_result['success']:
        print(f"✓ Reply added successfully!")
        print(f"  Reply ID: {reply_result['reply_id']}")
    else:
        print(f"✗ Failed to add reply: {reply_result.get('error')}")
    
    # Example 5: Like the post
    print("\n6. Liking the post...")
    like_result = forum_tools.like_post(post_id, 'farmer_arjun_003')
    
    if like_result['success']:
        print(f"✓ {like_result['message']}")
    else:
        print(f"✗ Failed to like post: {like_result.get('error')}")
    
    # Example 6: Search for posts
    print("\n7. Searching for wheat-related posts...")
    search_result = forum_tools.search_posts(
        query='wheat',
        category={'crop_type': 'wheat'},
        limit=10
    )
    
    if search_result['success']:
        print(f"✓ Found {search_result['count']} posts")
        for i, post in enumerate(search_result['posts'][:3], 1):
            print(f"  {i}. {post['title'][:50]}...")
    else:
        print(f"✗ Search failed: {search_result.get('error')}")
    
    # Example 7: Get user reputation
    print("\n8. Getting user reputation...")
    rep_result = forum_tools.get_user_reputation('farmer_ravi_001')
    
    if rep_result['success']:
        print(f"✓ User reputation:")
        print(f"  Score: {rep_result['reputation_score']}")
        print(f"  Badge: {rep_result['badge'].title()}")
        print(f"  Metrics:")
        for key, value in rep_result['metrics'].items():
            print(f"    - {key.replace('_', ' ').title()}: {value}")
    else:
        print(f"✗ Failed to get reputation: {rep_result.get('error')}")
    
    # Example 8: Get all posts
    print("\n9. Getting recent posts...")
    posts_result = forum_tools.get_posts(limit=5)
    
    if posts_result['success']:
        print(f"✓ Retrieved {posts_result['count']} posts")
        for i, post in enumerate(posts_result['posts'], 1):
            print(f"  {i}. [{post['original_language'].upper()}] {post['title'][:40]}...")
            print(f"     💬 {post.get('replies_count', 0)} replies • 👍 {post.get('likes_count', 0)} likes")
    else:
        print(f"✗ Failed to get posts: {posts_result.get('error')}")
    
    # Example 9: Test spam detection
    print("\n10. Testing spam detection...")
    spam_post = forum_tools.create_post(
        user_id='spammer_001',
        title='Buy cheap products now!!!',
        content='Click here to buy amazing products at lowest prices! Limited time offer!!!',
        language='en',
        category={'crop_type': 'other'},
        tags=['spam']
    )
    
    if not spam_post['success']:
        print(f"✓ Spam detected and blocked!")
        print(f"  Reason: {spam_post.get('reason', spam_post.get('error'))}")
    else:
        print(f"⚠ Spam post was not detected (may need tuning)")
    
    print("\n" + "=" * 70)
    print("✓ Forum example completed!")
    print("=" * 70)
    
    # Summary
    print("\n📊 Summary:")
    print("  - Created multilingual post (Hindi)")
    print("  - Translated post to English")
    print("  - Added reply with cross-language communication")
    print("  - Implemented AI-powered spam filtering")
    print("  - Calculated user reputation and badges")
    print("  - Enabled post categorization and search")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user")
    except Exception as e:
        print(f"\n✗ Error running example: {e}")
        import traceback
        traceback.print_exc()
