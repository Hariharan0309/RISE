# RISE Multilingual Farmer Forums

## Overview

The Multilingual Farmer Forums enable farmers across India to connect, share experiences, and learn from each other regardless of language barriers. The system provides real-time translation, AI-powered spam filtering, and community reputation tracking.

## Features

### 🌐 Multilingual Support
- **9 Supported Languages**: Hindi, English, Tamil, Telugu, Kannada, Bengali, Gujarati, Marathi, Punjabi
- **Real-time Translation**: Automatic translation using Amazon Translate with agricultural terminology
- **Language Detection**: Auto-detect original language of posts
- **Cultural Adaptation**: Context-aware translations for regional farming practices

### 🛡️ AI-Powered Moderation
- **Spam Detection**: Amazon Comprehend sentiment analysis
- **Toxicity Filtering**: Amazon Bedrock-powered content moderation
- **Automatic Blocking**: Inappropriate content flagged before posting
- **Sentiment Scoring**: Track post quality and helpfulness

### 📊 Community Features
- **Post Categorization**: By crop type, region, and farming method
- **Tag System**: Flexible tagging for easy discovery
- **Search Functionality**: Keyword search across all posts
- **User Reputation**: Badge system based on contributions
- **Like & Reply**: Engage with community content

### 🏆 Reputation System
- **Badges**: Newcomer (🌱), Contributor (✨), Experienced (⭐), Expert (🌟)
- **Scoring**: Based on posts, likes, replies, and sentiment
- **Expert Highlighting**: Verified experts and experienced farmers stand out

## Architecture

### Components

1. **ForumTools** (`forum_tools.py`)
   - Core forum functionality
   - Translation and moderation
   - Reputation calculation

2. **Lambda Function** (`forum_lambda.py`)
   - API Gateway handler
   - Request routing
   - Error handling

3. **Streamlit UI** (`farmer_forum.py`)
   - User interface
   - Post creation and viewing
   - Search and filtering

### AWS Services Used

- **Amazon DynamoDB**: Forum posts and user data storage
- **Amazon Translate**: Real-time multilingual translation
- **Amazon Comprehend**: Sentiment analysis and spam detection
- **Amazon Bedrock**: Advanced toxicity checking
- **API Gateway**: RESTful API endpoints

## Data Model

### Forum Post Structure

```python
{
    'post_id': 'post_abc123',
    'timestamp': 1234567890000,
    'user_id': 'user_001',
    'title': 'Best practices for wheat cultivation',
    'content': 'Detailed post content...',
    'original_language': 'hi',
    'category': {
        'crop_type': 'wheat',
        'region': 'north_india',
        'method': 'traditional'
    },
    'tags': ['wheat', 'fertilizer', 'irrigation'],
    'sentiment_score': 0.75,
    'replies_count': 5,
    'likes_count': 10,
    'views_count': 50,
    'status': 'active',
    'created_at': '2024-01-15T10:30:00Z',
    'updated_at': '2024-01-15T12:45:00Z'
}
```

## API Reference

### Create Post

```python
result = forum_tools.create_post(
    user_id='user_001',
    title='Post title',
    content='Post content',
    language='hi',
    category={
        'crop_type': 'wheat',
        'region': 'north_india',
        'method': 'organic'
    },
    tags=['wheat', 'organic']
)
```

**Response:**
```python
{
    'success': True,
    'post_id': 'post_abc123',
    'timestamp': 1234567890000,
    'sentiment_score': 0.75
}
```

### Get Posts

```python
result = forum_tools.get_posts(
    category={'crop_type': 'wheat'},
    limit=20
)
```

**Response:**
```python
{
    'success': True,
    'posts': [...],
    'count': 15,
    'last_evaluated_key': {...}
}
```

### Translate Post

```python
result = forum_tools.translate_post(
    post_id='post_abc123',
    target_language='en'
)
```

**Response:**
```python
{
    'success': True,
    'post': {
        'title': 'Translated title',
        'content': 'Translated content',
        'translated_to': 'en',
        'original_title': 'Original title',
        'original_content': 'Original content'
    },
    'translated': True,
    'source_language': 'hi',
    'target_language': 'en'
}
```

### Add Reply

```python
result = forum_tools.add_reply(
    post_id='post_abc123',
    user_id='user_002',
    content='Reply content',
    language='en'
)
```

**Response:**
```python
{
    'success': True,
    'reply_id': 'reply_xyz789',
    'timestamp': 1234567890000
}
```

### Like Post

```python
result = forum_tools.like_post(
    post_id='post_abc123',
    user_id='user_002'
)
```

**Response:**
```python
{
    'success': True,
    'message': 'Post liked successfully'
}
```

### Search Posts

```python
result = forum_tools.search_posts(
    query='wheat cultivation',
    category={'crop_type': 'wheat'},
    limit=20
)
```

**Response:**
```python
{
    'success': True,
    'posts': [...],
    'count': 8,
    'query': 'wheat cultivation'
}
```

### Get User Reputation

```python
result = forum_tools.get_user_reputation(
    user_id='user_001'
)
```

**Response:**
```python
{
    'success': True,
    'user_id': 'user_001',
    'reputation_score': 245,
    'badge': 'experienced',
    'metrics': {
        'total_posts': 12,
        'total_likes': 45,
        'total_replies': 23,
        'avg_sentiment': 0.72
    }
}
```

## Usage Examples

### Example 1: Create Multilingual Post

```python
from tools.forum_tools import create_forum_tools

# Initialize
forum_tools = create_forum_tools()

# Create post in Hindi
result = forum_tools.create_post(
    user_id='farmer_ravi',
    title='गेहूं की खेती के लिए सर्वोत्तम प्रथाएं',
    content='मैं अपने खेत में गेहूं उगा रहा हूं...',
    language='hi',
    category={
        'crop_type': 'wheat',
        'region': 'north_india',
        'method': 'traditional'
    },
    tags=['wheat', 'advice']
)

print(f"Post created: {result['post_id']}")
```

### Example 2: Translate and Reply

```python
# Get post
post_result = forum_tools.get_post('post_abc123')

# Translate to English
translated = forum_tools.translate_post('post_abc123', 'en')

# Add reply in English
reply = forum_tools.add_reply(
    post_id='post_abc123',
    user_id='farmer_lakshmi',
    content='Great question! Here are my suggestions...',
    language='en'
)
```

### Example 3: Search and Filter

```python
# Search for wheat posts in North India
results = forum_tools.search_posts(
    query='wheat fertilizer',
    category={
        'crop_type': 'wheat',
        'region': 'north_india'
    },
    limit=10
)

for post in results['posts']:
    print(f"{post['title']} - {post['likes_count']} likes")
```

## Spam Detection

The system uses multi-layered spam detection:

1. **Sentiment Analysis** (Amazon Comprehend)
   - Detects highly negative content (>80% negative)
   - Flags suspicious patterns

2. **Toxicity Check** (Amazon Bedrock)
   - Identifies offensive language
   - Detects spam patterns
   - Provides toxicity scores

3. **Content Validation**
   - Checks for excessive promotional content
   - Validates agricultural relevance

## Reputation System

### Scoring Formula

```
reputation_score = (
    total_posts × 10 +
    total_likes × 5 +
    total_replies × 3 +
    avg_sentiment × 50
)
```

### Badge Levels

| Badge | Score Range | Emoji |
|-------|-------------|-------|
| Newcomer | 0-50 | 🌱 |
| Contributor | 51-200 | ✨ |
| Experienced | 201-500 | ⭐ |
| Expert | 500+ | 🌟 |

## Testing

Run unit tests:

```bash
pytest tests/test_forum.py -v
```

Run example:

```bash
python examples/forum_example.py
```

## Configuration

### Environment Variables

```bash
AWS_REGION=us-east-1
DYNAMODB_TABLE_POSTS=RISE-ForumPosts
DYNAMODB_TABLE_USERS=RISE-UserProfiles
```

### DynamoDB Table Setup

```python
# Create ForumPosts table
aws dynamodb create-table \
    --table-name RISE-ForumPosts \
    --attribute-definitions \
        AttributeName=post_id,AttributeType=S \
        AttributeName=timestamp,AttributeType=N \
    --key-schema \
        AttributeName=post_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST
```

## Performance Considerations

- **Caching**: Translation results cached for 24 hours
- **Pagination**: Use `last_evaluated_key` for large result sets
- **Indexing**: GSI on user_id and category for fast queries
- **TTL**: Automatic cleanup of old posts (optional)

## Security

- **Input Validation**: All user input sanitized
- **Content Moderation**: AI-powered spam and toxicity filtering
- **Rate Limiting**: Prevent abuse (implement in API Gateway)
- **Authentication**: User verification required for posting

## Future Enhancements

- [ ] Image attachments in posts
- [ ] Video content support
- [ ] Real-time notifications
- [ ] Advanced search with filters
- [ ] Trending topics
- [ ] Expert verification system
- [ ] Mobile push notifications
- [ ] Offline post drafts

## Support

For issues or questions:
- Check the example file: `examples/forum_example.py`
- Run tests: `pytest tests/test_forum.py`
- Review API documentation above

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project.
