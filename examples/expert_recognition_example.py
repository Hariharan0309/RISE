"""
RISE Expert Recognition System Example
Demonstrates the expert recognition and reputation tracking features
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.forum_tools import create_forum_tools
import json


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def example_get_user_reputation():
    """Example: Get comprehensive user reputation"""
    print_section("Example 1: Get User Reputation")
    
    # Initialize forum tools
    forum_tools = create_forum_tools(region='us-east-1')
    
    # Get reputation for a user
    user_id = 'farmer_ravi_001'
    
    print(f"Getting reputation for user: {user_id}\n")
    
    result = forum_tools.get_user_reputation(user_id)
    
    if result['success']:
        print(f"✓ Success!")
        print(f"\nUser ID: {result['user_id']}")
        print(f"Reputation Score: {result['reputation_score']}")
        print(f"Expertise Level: {result['expertise_level']}%")
        print(f"Badge: {result['badge_emoji']} {result['badge']}")
        print(f"Description: {result['badge_description']}")
        print(f"Verified Expert: {'Yes' if result['is_verified_expert'] else 'No'}")
        
        print("\n--- Contribution Metrics ---")
        metrics = result['metrics']
        print(f"Total Posts: {metrics['total_posts']}")
        print(f"Helpful Answers: {metrics['helpful_answers']}")
        print(f"Verified Solutions: {metrics['verified_solutions']}")
        print(f"Total Likes: {metrics['total_likes']}")
        print(f"Total Replies: {metrics['total_replies']}")
        print(f"Community Endorsements: {metrics['community_endorsements']}")
        print(f"Engagement Rate: {metrics['engagement_rate']}")
        print(f"Consistency Score: {metrics['consistency_score']}")
        
        print("\n--- Expertise Areas ---")
        for area in result['expertise_areas']:
            print(f"  • {area['area'].replace('_', ' ').title()}")
            print(f"    Posts: {area['posts_count']}, Engagement: {area['engagement']}, Score: {area['score']}")
        
        print("\n--- Achievements ---")
        for achievement in result['achievements']:
            print(f"  🏅 {achievement['title']}: {achievement['description']}")
    else:
        print(f"✗ Error: {result.get('error')}")


def example_get_top_experts():
    """Example: Get top experts in the community"""
    print_section("Example 2: Get Top Experts")
    
    forum_tools = create_forum_tools(region='us-east-1')
    
    print("Getting top 10 experts in the community...\n")
    
    result = forum_tools.get_top_experts(limit=10)
    
    if result['success']:
        print(f"✓ Found {result['count']} experts\n")
        
        for idx, expert in enumerate(result['experts'], 1):
            print(f"{idx}. {expert['badge_emoji']} {expert['user_id']}")
            print(f"   Reputation: {expert['reputation_score']}")
            print(f"   Expertise Level: {expert['expertise_level']}%")
            print(f"   Badge: {expert['badge'].replace('_', ' ').title()}")
            
            if expert['expertise_areas']:
                areas = ', '.join([a['area'] for a in expert['expertise_areas'][:3]])
                print(f"   Expertise: {areas}")
            
            print()
    else:
        print(f"✗ Error: {result.get('error')}")


def example_get_experts_by_area():
    """Example: Get experts filtered by expertise area"""
    print_section("Example 3: Get Experts by Expertise Area")
    
    forum_tools = create_forum_tools(region='us-east-1')
    
    expertise_area = 'wheat'
    print(f"Getting experts in {expertise_area} cultivation...\n")
    
    result = forum_tools.get_top_experts(limit=5, expertise_area=expertise_area)
    
    if result['success']:
        print(f"✓ Found {result['count']} experts in {expertise_area}\n")
        
        for idx, expert in enumerate(result['experts'], 1):
            print(f"{idx}. {expert['badge_emoji']} {expert['user_id']}")
            print(f"   Reputation: {expert['reputation_score']}")
            
            # Find wheat expertise
            wheat_expertise = next(
                (a for a in expert['expertise_areas'] if a['area'] == expertise_area),
                None
            )
            
            if wheat_expertise:
                print(f"   {expertise_area.title()} Posts: {wheat_expertise['posts_count']}")
                print(f"   {expertise_area.title()} Engagement: {wheat_expertise['engagement']}")
            
            print()
    else:
        print(f"✗ Error: {result.get('error')}")


def example_mark_solution():
    """Example: Mark a post as verified solution"""
    print_section("Example 4: Mark Post as Verified Solution")
    
    forum_tools = create_forum_tools(region='us-east-1')
    
    post_id = 'post_abc123'
    marked_by = 'moderator_001'
    
    print(f"Marking post {post_id} as verified solution...\n")
    
    result = forum_tools.mark_post_as_solution(post_id, marked_by)
    
    if result['success']:
        print(f"✓ {result['message']}")
        print(f"\nThis will increase the post author's reputation:")
        print(f"  • +50 points for verified solution")
        print(f"  • Contributes to expert badge qualification")
    else:
        print(f"✗ Error: {result.get('error')}")


def example_expert_directory():
    """Example: Get comprehensive expert directory"""
    print_section("Example 5: Expert Directory")
    
    forum_tools = create_forum_tools(region='us-east-1')
    
    print("Loading expert directory...\n")
    
    result = forum_tools.get_expert_directory()
    
    if result['success']:
        directory = result['directory']
        
        print(f"✓ Expert Directory Loaded\n")
        print(f"Total Experts: {directory['total_experts']}")
        print(f"Verified Experts: {directory['total_verified']}")
        print(f"Expertise Areas: {len(directory['by_expertise'])}")
        
        print("\n--- Verified Experts ---")
        for expert in directory['verified_experts'][:5]:
            print(f"  {expert['badge_emoji']} {expert['user_id']}")
            print(f"     Reputation: {expert['reputation_score']}")
        
        print("\n--- Experts by Area ---")
        for area, experts in list(directory['by_expertise'].items())[:3]:
            print(f"\n  {area.replace('_', ' ').title()}:")
            for expert in experts[:3]:
                print(f"    • {expert['badge_emoji']} {expert['user_id']} (Score: {expert['expertise_score']})")
    else:
        print(f"✗ Error: {result.get('error')}")


def example_badge_progression():
    """Example: Show badge progression system"""
    print_section("Example 6: Badge Progression System")
    
    print("Badge Levels and Requirements:\n")
    
    badges = [
        {
            'emoji': '🌱',
            'name': 'Beginner',
            'requirements': 'New to the community',
            'reputation': '0-199 points'
        },
        {
            'emoji': '✨',
            'name': 'Contributor',
            'requirements': '200+ reputation, 3+ helpful answers',
            'reputation': '200-499 points'
        },
        {
            'emoji': '⭐',
            'name': 'Experienced Farmer',
            'requirements': '500+ reputation, 10+ helpful answers',
            'reputation': '500-999 points'
        },
        {
            'emoji': '🌟',
            'name': 'Expert',
            'requirements': '1000+ reputation, 25+ helpful answers, 10+ verified solutions',
            'reputation': '1000-1999 points',
            'verified': True
        },
        {
            'emoji': '🏆',
            'name': 'Master Farmer',
            'requirements': '2000+ reputation, 50+ helpful answers, 20+ verified solutions',
            'reputation': '2000+ points',
            'verified': True
        }
    ]
    
    for badge in badges:
        print(f"{badge['emoji']} {badge['name']}")
        print(f"   Reputation: {badge['reputation']}")
        print(f"   Requirements: {badge['requirements']}")
        if badge.get('verified'):
            print(f"   Status: ✓ VERIFIED EXPERT")
        print()


def example_reputation_calculation():
    """Example: Show how reputation is calculated"""
    print_section("Example 7: Reputation Calculation Formula")
    
    print("Reputation Score Formula:\n")
    print("reputation_score = (")
    print("    total_posts × 10 +                    # Base contribution")
    print("    helpful_answers × 25 +                # Quality answers")
    print("    total_likes × 5 +                     # Community appreciation")
    print("    total_replies × 3 +                   # Engagement generation")
    print("    verified_solutions × 50 +             # Verified expertise")
    print("    community_endorsements × 15 +         # High-impact contributions")
    print("    avg_sentiment × 50 +                  # Positive sentiment")
    print("    consistency_score × 20 +              # Regular participation")
    print("    len(expertise_areas) × 30             # Breadth of knowledge")
    print(")")
    
    print("\n--- Example Calculation ---")
    print("\nUser with:")
    print("  • 20 posts")
    print("  • 12 helpful answers")
    print("  • 85 likes")
    print("  • 45 replies")
    print("  • 5 verified solutions")
    print("  • 8 community endorsements")
    print("  • 0.6 avg sentiment")
    print("  • 8.0 consistency score")
    print("  • 3 expertise areas")
    
    score = (
        20 * 10 +
        12 * 25 +
        85 * 5 +
        45 * 3 +
        5 * 50 +
        8 * 15 +
        0.6 * 50 +
        8.0 * 20 +
        3 * 30
    )
    
    print(f"\nCalculated Reputation: {int(score)} points")
    print(f"Badge Level: Experienced Farmer ⭐")


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("  RISE Expert Recognition System - Examples")
    print("=" * 80)
    
    print("\nNote: These examples use mock data for demonstration.")
    print("In production, they would connect to DynamoDB and AWS services.")
    
    try:
        example_get_user_reputation()
        example_get_top_experts()
        example_get_experts_by_area()
        example_mark_solution()
        example_expert_directory()
        example_badge_progression()
        example_reputation_calculation()
        
        print_section("Examples Complete")
        print("✓ All examples executed successfully!")
        print("\nFor more information, see:")
        print("  • tools/EXPERT_RECOGNITION_README.md")
        print("  • tests/test_forum.py (TestExpertRecognitionSystem)")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
