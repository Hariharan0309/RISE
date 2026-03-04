# RISE Expert Recognition System

## Overview

The Expert Recognition System is a comprehensive reputation and expertise tracking system for the RISE farmer community forum. It identifies, verifies, and highlights agricultural experts based on their contributions, engagement, and community impact.

## Features

### 1. User Reputation Tracking

The system tracks multiple metrics to calculate a comprehensive reputation score:

- **Total Posts**: Number of discussions started
- **Helpful Answers**: Posts with high engagement and positive sentiment
- **Total Likes**: Community appreciation
- **Total Replies**: Engagement generated
- **Verified Solutions**: Posts marked as verified solutions
- **Community Endorsements**: Highly engaged posts (10+ likes or 5+ replies)
- **Sentiment Score**: Average positive sentiment across posts
- **Consistency Score**: Regular participation over time
- **Expertise Breadth**: Number of different crop types/areas

### 2. Expertise Scoring Algorithm

The reputation score is calculated using a weighted formula:

```python
reputation_score = (
    total_posts * 10 +                    # Base contribution
    helpful_answers * 25 +                # Quality answers
    total_likes * 5 +                     # Community appreciation
    total_replies * 3 +                   # Engagement generation
    verified_solutions * 50 +             # Verified expertise
    community_endorsements * 15 +         # High-impact contributions
    avg_sentiment * 50 +                  # Positive sentiment
    consistency_score * 20 +              # Regular participation
    len(expertise_areas) * 30             # Breadth of knowledge
)
```

### 3. Verified Expert Badges

The system awards badges based on reputation and contribution quality:

#### 🏆 Master Farmer
- **Requirements**: 2000+ reputation, 50+ helpful answers, 20+ verified solutions
- **Status**: Verified Expert
- **Description**: Top agricultural expert

#### 🌟 Expert
- **Requirements**: 1000+ reputation, 25+ helpful answers, 10+ verified solutions
- **Status**: Verified Expert
- **Description**: Verified agricultural specialist

#### ⭐ Experienced Farmer
- **Requirements**: 500+ reputation, 10+ helpful answers
- **Status**: Trusted Contributor
- **Description**: Trusted contributor

#### ✨ Contributor
- **Requirements**: 200+ reputation, 3+ helpful answers
- **Status**: Active Member
- **Description**: Active community member

#### 🌱 Beginner
- **Requirements**: New users
- **Status**: New Member
- **Description**: New to the community

### 4. Expert Highlighting in Forum

Expert posts are visually distinguished in the forum:

- **Verified Expert Badge**: Prominently displayed on posts
- **Badge Emoji**: Visual indicator of expertise level
- **Badge Description**: Explains the user's status
- **Expertise Areas**: Shows user's areas of specialization

### 5. Expert Directory

A comprehensive directory showcasing community experts:

- **All Experts View**: Lists all experts by reputation
- **Verified Only View**: Shows only verified experts
- **By Expertise Area**: Filter experts by crop type or specialty
- **Expert Cards**: Detailed profile cards with metrics
- **Search and Filter**: Find experts by area of expertise

### 6. User Profile Dashboard

Detailed profile showing:

- **Reputation Score**: Overall reputation points
- **Expertise Level**: 0-100% expertise rating
- **Contribution Metrics**: Detailed breakdown of contributions
- **Expertise Areas**: User's specializations with engagement metrics
- **Achievements**: Unlocked achievements and milestones
- **Progress Tracker**: Progress to next badge level

## API Endpoints

### Get User Reputation

```python
GET /api/v1/community/get_reputation
{
    "action": "get_reputation",
    "user_id": "user_123"
}
```

**Response:**
```json
{
    "success": true,
    "user_id": "user_123",
    "reputation_score": 1250,
    "expertise_level": 62,
    "badge": "expert",
    "badge_emoji": "🌟",
    "badge_description": "Expert - Verified agricultural specialist",
    "is_verified_expert": true,
    "expertise_areas": [
        {
            "area": "wheat",
            "posts_count": 15,
            "engagement": 120,
            "score": 390
        }
    ],
    "metrics": {
        "total_posts": 45,
        "helpful_answers": 28,
        "total_likes": 156,
        "verified_solutions": 12,
        "community_endorsements": 18
    },
    "achievements": [
        {
            "title": "Problem Solver",
            "description": "25+ helpful answers"
        }
    ]
}
```

### Get Top Experts

```python
GET /api/v1/community/get_top_experts
{
    "action": "get_top_experts",
    "limit": 10,
    "expertise_area": "wheat"  # Optional
}
```

**Response:**
```json
{
    "success": true,
    "experts": [
        {
            "user_id": "user_123",
            "reputation_score": 1250,
            "expertise_level": 62,
            "badge": "expert",
            "is_verified_expert": true,
            "expertise_areas": [...]
        }
    ],
    "count": 10
}
```

### Mark Post as Solution

```python
POST /api/v1/community/mark_solution
{
    "action": "mark_solution",
    "post_id": "post_abc123",
    "marked_by_user_id": "user_456"
}
```

### Get Expert Directory

```python
GET /api/v1/community/get_expert_directory
{
    "action": "get_expert_directory"
}
```

**Response:**
```json
{
    "success": true,
    "directory": {
        "verified_experts": [...],
        "by_expertise": {
            "wheat": [...],
            "rice": [...]
        },
        "total_experts": 45,
        "total_verified": 12
    }
}
```

## Usage Examples

### Python SDK

```python
from forum_tools import ForumTools

# Initialize
forum_tools = ForumTools(region='us-east-1')

# Get user reputation
reputation = forum_tools.get_user_reputation('user_123')
print(f"Reputation: {reputation['reputation_score']}")
print(f"Badge: {reputation['badge_emoji']} {reputation['badge']}")

# Get top experts
experts = forum_tools.get_top_experts(limit=10)
for expert in experts['experts']:
    print(f"{expert['badge_emoji']} {expert['user_id']}: {expert['reputation_score']}")

# Mark post as solution
result = forum_tools.mark_post_as_solution('post_abc123', 'user_456')

# Get expert directory
directory = forum_tools.get_expert_directory()
print(f"Total experts: {directory['directory']['total_experts']}")
```

### Streamlit UI

```python
from ui.farmer_forum import render_farmer_forum

# Render forum with expert recognition
render_farmer_forum(
    forum_tools=forum_tools,
    user_id='user_123',
    user_language='en'
)
```

## Achievements System

Users can unlock achievements based on their contributions:

### Posting Milestones
- **Active Member**: 10+ posts
- **Prolific Contributor**: 50+ posts
- **Century Club**: 100+ posts

### Helpful Answers
- **Helpful Hand**: 10+ helpful answers
- **Problem Solver**: 25+ helpful answers
- **Community Hero**: 50+ helpful answers

### Verified Solutions
- **Solution Provider**: 10+ verified solutions
- **Solution Master**: 20+ verified solutions

### Community Impact
- **Community Favorite**: 20+ highly engaged posts

### Expertise Breadth
- **Diverse Knowledge**: Expertise in 3+ crop types
- **Multi-Crop Expert**: Expertise in 5+ crop types

## Expertise Areas

The system automatically identifies expertise areas based on:

1. **Post Categories**: Crop types, regions, farming methods
2. **Engagement Metrics**: Likes and replies on posts
3. **Minimum Threshold**: At least 3 posts in an area
4. **Scoring**: Posts count × 10 + engagement × 2

Top 5 expertise areas are displayed for each user.

## Consistency Scoring

Measures regular participation:

- **Ideal**: 1-7 days between posts (10 points)
- **Good**: 8-14 days between posts (8 points)
- **Moderate**: 15-30 days between posts (5 points)
- **Low**: 30+ days between posts (2 points)

## Integration with Forum

The expert recognition system is fully integrated with the forum:

1. **Post Creation**: Sentiment analysis for quality scoring
2. **Post Display**: Expert badges shown prominently
3. **Post Actions**: Mark as solution feature
4. **User Profiles**: Comprehensive reputation dashboard
5. **Expert Directory**: Searchable expert database

## AWS Services Used

- **Amazon DynamoDB**: Store posts and reputation data
- **Amazon Comprehend**: Sentiment analysis for quality scoring
- **Amazon Bedrock**: Toxicity detection and content moderation
- **AWS Lambda**: Serverless API endpoints

## Future Enhancements

1. **Peer Endorsements**: Allow users to endorse experts
2. **Expert Verification**: Manual verification by moderators
3. **Expertise Certifications**: Link to agricultural certifications
4. **Expert Matching**: Match farmers with relevant experts
5. **Expert Rewards**: Incentives for top contributors
6. **Analytics Dashboard**: Track community expertise growth

## Testing

Run tests for the expert recognition system:

```bash
pytest tests/test_forum.py::test_get_user_reputation
pytest tests/test_forum.py::test_get_top_experts
pytest tests/test_forum.py::test_mark_solution
pytest tests/test_forum.py::test_expert_directory
```

## Contributing

To enhance the expert recognition system:

1. Update scoring algorithm in `forum_tools.py`
2. Add new badge levels in `_determine_badge()`
3. Create new achievements in `_get_achievements()`
4. Update UI components in `farmer_forum.py`
5. Add tests for new features

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project.
