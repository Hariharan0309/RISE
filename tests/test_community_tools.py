"""
Property-based tests for community forum tools.

Tests Properties 15 and 16 from the design document.
"""

import pytest
from hypothesis import given, strategies as st, assume
from tools.community_tools import (
    search_forum,
    summarize_discussions,
    store_experience,
    combine_advice,
    FORUM_STORAGE
)


# Helper strategies
@st.composite
def location_strategy(draw):
    """Generate valid location dictionaries."""
    districts = ["Bangalore", "Mysore", "Mandya", "Hassan", "Tumkur"]
    states = ["Karnataka", "Tamil Nadu", "Andhra Pradesh"]
    return {
        "district": draw(st.sampled_from(districts)),
        "state": draw(st.sampled_from(states))
    }


# Feature: missionai-farmer-agent, Property 15: Community Forum Round-Trip
@given(
    farmer_id=st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    topic=st.sampled_from(["disease", "weather", "market", "technique", "general"]),
    content=st.text(min_size=10, max_size=200, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))),
    language=st.sampled_from(["kannada", "english", "hindi"]),
    location=location_strategy()
)
@pytest.mark.property_test
def test_community_forum_round_trip(farmer_id, topic, content, language, location):
    """
    **Validates: Requirements 8.3**
    
    Property 15: Community Forum Round-Trip
    For any farmer experience stored in the community forum,
    retrieving posts by the same topic and location SHALL return
    the stored experience in the results.
    """
    # Clear storage before test
    FORUM_STORAGE.clear()
    
    # Store experience
    store_result = store_experience(
        farmer_id=farmer_id,
        topic=topic,
        content=content,
        language=language,
        location=location
    )
    
    assert store_result["status"] == "stored"
    post_id = store_result["post_id"]
    
    # Search for the stored experience by topic
    search_results = search_forum(
        query=topic,
        location=location,
        language=language
    )
    
    # Verify the stored experience is in search results
    found = False
    for result in search_results:
        if result["post_id"] == post_id:
            found = True
            assert result["topic"] == topic
            assert result["question"] == content
            assert result["language"] == language
            break
    
    assert found, f"Stored experience with post_id {post_id} should be found in search results"


# Feature: missionai-farmer-agent, Property 16: Combined Advice Composition
@given(
    ai_recommendation=st.text(min_size=20, max_size=200, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))),
    num_insights=st.integers(min_value=1, max_value=5)
)
@pytest.mark.property_test
def test_combined_advice_composition(ai_recommendation, num_insights):
    """
    **Validates: Requirements 8.4**
    
    Property 16: Combined Advice Composition
    For any advice response from the Community_Advisor_Agent,
    when both AI recommendations and community insights are available,
    the response SHALL include elements from both sources.
    """
    # Generate community insights
    community_insights = [
        f"Community insight {i}: Use local methods"
        for i in range(num_insights)
    ]
    
    # Combine advice
    result = combine_advice(ai_recommendation, community_insights)
    
    # Verify result is a string
    assert isinstance(result, str)
    assert len(result) > 0
    
    # Verify AI recommendation is included
    assert ai_recommendation in result or "AI Analysis" in result
    
    # Verify community insights are included
    assert "Community Experience" in result or "Community" in result
    
    # Verify at least some community insights are present
    insights_found = sum(1 for insight in community_insights if insight in result)
    assert insights_found > 0, "At least some community insights should be in combined advice"


# Additional unit tests
def test_search_forum_invalid_query():
    """Test forum search with invalid query."""
    with pytest.raises(ValueError) as exc_info:
        search_forum("")
    assert "query" in str(exc_info.value).lower()
    
    with pytest.raises(ValueError) as exc_info:
        search_forum("ab")  # Too short
    assert "query" in str(exc_info.value).lower()


def test_search_forum_with_filters():
    """Test forum search with location and language filters."""
    FORUM_STORAGE.clear()
    
    # Store posts with different attributes
    store_experience(
        "farmer1", "disease", "Tomato leaf curl problem",
        language="kannada",
        location={"district": "Mysore", "state": "Karnataka"}
    )
    post1_id = FORUM_STORAGE[-1]["post_id"]
    
    store_experience(
        "farmer2", "disease", "Tomato blight issue",
        language="english",
        location={"district": "Bangalore", "state": "Karnataka"}
    )
    post2_id = FORUM_STORAGE[-1]["post_id"]
    
    # Search with language filter
    results_kannada = search_forum("tomato", language="kannada")
    kannada_ids = [r["post_id"] for r in results_kannada]
    assert post1_id in kannada_ids, "Should find the Kannada post"
    
    # Search with location filter
    results_mysore = search_forum(
        "tomato",
        location={"district": "Mysore", "state": "Karnataka"}
    )
    mysore_ids = [r["post_id"] for r in results_mysore]
    assert post1_id in mysore_ids, "Should find the Mysore post"


def test_summarize_discussions_empty():
    """Test summarizing empty discussions list."""
    result = summarize_discussions([])
    assert "No community discussions" in result


def test_summarize_discussions_with_posts():
    """Test summarizing discussions with posts."""
    discussions = [
        {
            "post_id": "1",
            "question": "How to treat tomato blight?",
            "topic": "disease",
            "answers": [
                {"content": "Use copper fungicide", "helpful_count": 5},
                {"content": "Remove affected leaves", "helpful_count": 3}
            ],
            "view_count": 100
        },
        {
            "post_id": "2",
            "question": "Best time to plant tomatoes?",
            "topic": "technique",
            "answers": [
                {"content": "Plant after monsoon", "helpful_count": 4}
            ],
            "view_count": 80
        }
    ]
    
    result = summarize_discussions(discussions)
    
    assert "2 relevant community discussions" in result
    assert "3 answers" in result
    assert "Key insights" in result or "community" in result.lower()


def test_store_experience_invalid_inputs():
    """Test storing experience with invalid inputs."""
    # Invalid farmer_id
    with pytest.raises(ValueError) as exc_info:
        store_experience("", "disease", "Some content")
    assert "farmer" in str(exc_info.value).lower()
    
    # Invalid topic
    with pytest.raises(ValueError) as exc_info:
        store_experience("farmer1", "invalid_topic", "Some content")
    assert "topic" in str(exc_info.value).lower()
    
    # Invalid content (too short)
    with pytest.raises(ValueError) as exc_info:
        store_experience("farmer1", "disease", "Short")
    assert "content" in str(exc_info.value).lower()
    
    # Invalid language
    with pytest.raises(ValueError) as exc_info:
        store_experience("farmer1", "disease", "Some content", language="invalid")
    assert "language" in str(exc_info.value).lower()


def test_store_experience_with_tags():
    """Test storing experience with tags."""
    FORUM_STORAGE.clear()
    
    result = store_experience(
        farmer_id="farmer1",
        topic="disease",
        content="Tomato plants showing yellow leaves",
        language="english",
        tags=["tomato", "yellowing", "nutrient"]
    )
    
    assert result["status"] == "stored"
    assert "post_id" in result
    
    # Verify stored in FORUM_STORAGE
    assert len(FORUM_STORAGE) == 1
    assert FORUM_STORAGE[0]["tags"] == ["tomato", "yellowing", "nutrient"]


def test_combine_advice_invalid_inputs():
    """Test combining advice with invalid inputs."""
    # Invalid AI recommendation
    with pytest.raises(ValueError) as exc_info:
        combine_advice("", ["insight1"])
    assert "recommendation" in str(exc_info.value).lower()
    
    # Invalid community insights
    with pytest.raises(ValueError) as exc_info:
        combine_advice("AI advice", "not a list")
    assert "insights" in str(exc_info.value).lower()


def test_combine_advice_no_community_insights():
    """Test combining advice with no community insights."""
    ai_rec = "Apply fungicide to affected plants"
    result = combine_advice(ai_rec, [])
    
    assert ai_rec in result or "AI Analysis" in result
    assert "No community insights available" in result


def test_combine_advice_with_insights():
    """Test combining advice with community insights."""
    ai_rec = "Apply fungicide to affected plants"
    insights = [
        "Local farmers recommend neem oil",
        "Spray early morning for best results",
        "Remove affected leaves first"
    ]
    
    result = combine_advice(ai_rec, insights)
    
    assert "AI Analysis" in result
    assert "Community Experience" in result
    assert any(insight in result for insight in insights)


def test_search_forum_by_tags():
    """Test searching forum by tags."""
    FORUM_STORAGE.clear()
    
    store_experience(
        "farmer1",
        "disease",
        "Tomato blight problem in my field",
        tags=["tomato", "blight", "fungal"]
    )
    post_id = FORUM_STORAGE[-1]["post_id"]
    
    # Search by tag
    results = search_forum("blight")
    result_ids = [r["post_id"] for r in results]
    assert post_id in result_ids, "Should find post by tag"
    
    # Find our specific post
    our_post = next((r for r in results if r["post_id"] == post_id), None)
    assert our_post is not None
    assert "blight" in our_post["tags"]


def test_search_forum_sorting():
    """Test that search results are sorted by relevance."""
    FORUM_STORAGE.clear()
    
    # Create posts with different view counts and answers
    store_experience("f1", "disease", "Question about xyz123 unique disease")
    FORUM_STORAGE[-1]["view_count"] = 50
    FORUM_STORAGE[-1]["answers"] = [{"content": "Answer 1", "helpful_count": 1}]
    post1_id = FORUM_STORAGE[-1]["post_id"]
    
    store_experience("f2", "disease", "Another xyz123 unique disease question")
    FORUM_STORAGE[-1]["view_count"] = 100
    FORUM_STORAGE[-1]["answers"] = [
        {"content": "Answer 1", "helpful_count": 2},
        {"content": "Answer 2", "helpful_count": 3}
    ]
    post2_id = FORUM_STORAGE[-1]["post_id"]
    
    results = search_forum("xyz123 unique")
    
    # Find our posts in results
    our_results = [r for r in results if r["post_id"] in [post1_id, post2_id]]
    assert len(our_results) == 2, "Should find both our posts"
    
    # Post with more answers should come first
    assert len(our_results[0]["answers"]) >= len(our_results[1]["answers"])
