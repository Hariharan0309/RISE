"""
Community forum tools for MissionAI Farmer Agent.

This module provides tools for searching forum posts, storing experiences,
and combining AI with community wisdom.
"""

from typing import Dict, List, Optional
import json
import uuid
from datetime import datetime
from data_models import CommunityPost, Answer


# Load forum posts from JSON
def load_forum_posts() -> List[Dict]:
    """Load community forum posts from data file."""
    try:
        with open("data/forum_posts.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


# In-memory storage for new posts (would be database in production)
FORUM_STORAGE = []


def search_forum(
    query: str,
    location: Optional[Dict[str, str]] = None,
    language: Optional[str] = None
) -> List[Dict]:
    """
    Search community forum for relevant discussions.
    
    Args:
        query: Search query text
        location: Optional location filter (district, state)
        language: Optional language filter (kannada, english, hindi)
    
    Returns:
        List of matching forum posts
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")
    if len(query) < 3:
        raise ValueError("Query must be at least 3 characters long")
    
    query_lower = query.lower()
    
    # Load existing posts
    all_posts = load_forum_posts() + FORUM_STORAGE
    
    results = []
    
    for post in all_posts:
        # Check if query matches question, tags, or topic
        question_lower = post["question"].lower()
        tags_lower = [t.lower() for t in post.get("tags", [])]
        topic_lower = post.get("topic", "").lower()
        
        query_match = (
            query_lower in question_lower or
            query_lower in topic_lower or
            topic_lower in query_lower or
            any(query_lower in tag for tag in tags_lower) or
            any(tag in query_lower for tag in tags_lower)
        )
        
        if not query_match:
            continue
        
        # Apply location filter
        if location:
            post_location = post.get("location", {})
            if "state" in location:
                if post_location.get("state", "").lower() != location["state"].lower():
                    continue
            if "district" in location:
                if post_location.get("district", "").lower() != location["district"].lower():
                    continue
        
        # Apply language filter
        if language:
            if post.get("language", "").lower() != language.lower():
                continue
        
        # Add to results
        results.append({
            "post_id": post["post_id"],
            "farmer_id": post["farmer_id"],
            "location": post.get("location", {}),
            "language": post.get("language", "english"),
            "topic": post.get("topic", "general"),
            "question": post["question"],
            "answers": post.get("answers", []),
            "tags": post.get("tags", []),
            "created_at": post.get("created_at", ""),
            "view_count": post.get("view_count", 0)
        })
    
    # Sort by relevance (view count and answer count)
    results.sort(
        key=lambda x: (len(x["answers"]), x["view_count"]),
        reverse=True
    )
    
    return results


def summarize_discussions(discussions: List[Dict]) -> str:
    """
    Summarize key insights from community discussions.
    
    Args:
        discussions: List of forum post dictionaries
    
    Returns:
        Summary string with key insights
    
    Raises:
        ValueError: If discussions is invalid
    """
    # Input validation
    if not isinstance(discussions, list):
        raise ValueError("Discussions must be a list")
    
    if len(discussions) == 0:
        return "No community discussions found on this topic."
    
    # Extract key information
    total_posts = len(discussions)
    total_answers = sum(len(d.get("answers", [])) for d in discussions)
    
    # Get most common topics
    topics = [d.get("topic", "general") for d in discussions]
    topic_counts = {}
    for topic in topics:
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    # Get most helpful answers
    helpful_answers = []
    for discussion in discussions:
        for answer in discussion.get("answers", []):
            if answer.get("helpful_count", 0) > 2:
                helpful_answers.append({
                    "content": answer["content"],
                    "helpful_count": answer["helpful_count"]
                })
    
    helpful_answers.sort(key=lambda x: x["helpful_count"], reverse=True)
    
    # Build summary
    summary_parts = [
        f"Found {total_posts} relevant community discussions with {total_answers} answers."
    ]
    
    if topic_counts:
        most_common_topic = max(topic_counts.items(), key=lambda x: x[1])
        summary_parts.append(f"Most discussed topic: {most_common_topic[0]}")
    
    if helpful_answers:
        summary_parts.append("\nKey insights from community:")
        for i, answer in enumerate(helpful_answers[:3], 1):
            summary_parts.append(f"{i}. {answer['content'][:150]}...")
    
    return "\n".join(summary_parts)


def store_experience(
    farmer_id: str,
    topic: str,
    content: str,
    language: str = "english",
    location: Optional[Dict[str, str]] = None,
    tags: Optional[List[str]] = None
) -> Dict:
    """
    Store farmer experience in community forum.
    
    Args:
        farmer_id: Farmer identifier
        topic: Topic category (disease, weather, market, technique)
        content: Experience content/question
        language: Language of content
        location: Optional location information
        tags: Optional tags for categorization
    
    Returns:
        Dictionary with stored post information
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not farmer_id or not isinstance(farmer_id, str):
        raise ValueError("Farmer ID must be a non-empty string")
    if not topic or not isinstance(topic, str):
        raise ValueError("Topic must be a non-empty string")
    if not content or not isinstance(content, str):
        raise ValueError("Content must be a non-empty string")
    if len(content) < 10:
        raise ValueError("Content must be at least 10 characters long")
    
    valid_topics = ["disease", "weather", "market", "technique", "general"]
    if topic.lower() not in valid_topics:
        raise ValueError(f"Topic must be one of: {', '.join(valid_topics)}")
    
    valid_languages = ["kannada", "english", "hindi"]
    if language.lower() not in valid_languages:
        raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
    
    # Create post
    post = {
        "post_id": str(uuid.uuid4()),
        "farmer_id": farmer_id,
        "location": location or {"district": "Unknown", "state": "Unknown"},
        "language": language.lower(),
        "topic": topic.lower(),
        "question": content,
        "answers": [],
        "tags": tags or [],
        "created_at": datetime.now().isoformat(),
        "view_count": 0
    }
    
    # Store post
    FORUM_STORAGE.append(post)
    
    return {
        "post_id": post["post_id"],
        "status": "stored",
        "message": "Experience successfully shared with community",
        "topic": post["topic"],
        "language": post["language"]
    }


def combine_advice(
    ai_recommendation: str,
    community_insights: List[str]
) -> str:
    """
    Combine AI recommendations with community insights.
    
    Args:
        ai_recommendation: AI-generated recommendation
        community_insights: List of community insights/advice
    
    Returns:
        Combined advice string
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not ai_recommendation or not isinstance(ai_recommendation, str):
        raise ValueError("AI recommendation must be a non-empty string")
    if not isinstance(community_insights, list):
        raise ValueError("Community insights must be a list")
    
    # Build combined advice
    combined = []
    
    # Add AI recommendation
    combined.append("AI Analysis:")
    combined.append(ai_recommendation)
    combined.append("")
    
    # Add community insights if available
    if community_insights and len(community_insights) > 0:
        combined.append("Community Experience:")
        for i, insight in enumerate(community_insights, 1):
            if insight and isinstance(insight, str):
                combined.append(f"{i}. {insight}")
        combined.append("")
        combined.append("Recommendation: Consider both AI analysis and local community experience for best results.")
    else:
        combined.append("Note: No community insights available for this specific query.")
    
    return "\n".join(combined)
