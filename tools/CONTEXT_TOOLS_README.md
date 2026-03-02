# RISE Context Management Tools

## Overview

The Context Management Tools provide persistent conversation history, context retrieval, and intelligent summarization for the RISE farming assistant. This enables the system to maintain context across sessions and provide continuity in farmer interactions.

## Features

### 1. **DynamoDB Persistence**
- All conversation messages are stored in DynamoDB with automatic TTL-based cleanup
- Session-based and user-based indexing for efficient retrieval
- Encrypted at rest with AWS-managed keys
- Point-in-time recovery enabled

### 2. **Context Retrieval**
- Retrieve recent conversation history for context-aware responses
- Configurable context window size (default: 5 message pairs)
- Cross-session conversation history for personalized assistance
- Formatted context strings ready for agent consumption

### 3. **Conversation Summarization**
- Automatic summarization of long conversations using Amazon Bedrock
- Triggered automatically after 20+ messages
- Summaries stored as system messages for efficient context loading
- Focuses on key topics, recommendations, and follow-up actions

### 4. **Session Management**
- Automatic session timeout after 24 hours of inactivity
- TTL-based cleanup in DynamoDB (no manual intervention needed)
- Session restoration from DynamoDB history
- In-memory caching for active sessions

### 5. **Follow-up Question Handling**
- Context-aware query processing with conversation history
- Enhanced queries include previous conversation context
- Maintains continuity across multiple interactions
- Supports multilingual context preservation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Context Management Flow                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Query                                                 │
│      │                                                      │
│      ▼                                                      │
│  ┌──────────────────┐                                      │
│  │  Orchestrator    │                                      │
│  │  Agent           │                                      │
│  └────────┬─────────┘                                      │
│           │                                                 │
│           ├─────────────────┐                              │
│           │                 │                              │
│           ▼                 ▼                              │
│  ┌──────────────┐  ┌──────────────────┐                   │
│  │  In-Memory   │  │  Context Tools   │                   │
│  │  Session     │  │  (DynamoDB)      │                   │
│  │  Cache       │  └────────┬─────────┘                   │
│  └──────────────┘           │                              │
│                             ▼                              │
│                    ┌──────────────────┐                    │
│                    │  DynamoDB Table  │                    │
│                    │  Conversation    │                    │
│                    │  History         │                    │
│                    └────────┬─────────┘                    │
│                             │                              │
│                             ▼                              │
│                    ┌──────────────────┐                    │
│                    │  Amazon Bedrock  │                    │
│                    │  (Summarization) │                    │
│                    └──────────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## DynamoDB Table Schema

### Table: RISE-ConversationHistory

**Primary Key:**
- Partition Key: `session_id` (String)
- Sort Key: `timestamp` (Number - milliseconds)

**Attributes:**
- `session_id`: Session identifier
- `timestamp`: Message timestamp in milliseconds
- `user_id`: User identifier
- `role`: Message role (user/assistant/system)
- `content`: Message content
- `ttl`: Time-to-live for automatic cleanup (24 hours)
- `created_at`: ISO timestamp
- `metadata`: Optional metadata (JSON)

**Global Secondary Indexes:**
- `UserConversationIndex`: Partition key `user_id`, Sort key `timestamp`

**TTL Configuration:**
- Attribute: `ttl`
- Automatic deletion after 24 hours of inactivity

## Usage

### Basic Usage

```python
from tools.context_tools import ContextTools

# Initialize context tools
context_tools = ContextTools(region='us-east-1')

# Save a conversation message
context_tools.save_conversation_message(
    session_id='session_123',
    user_id='farmer_001',
    role='user',
    content='What fertilizer should I use for wheat?',
    metadata={'crop': 'wheat', 'language': 'hi'}
)

# Retrieve conversation history
messages = context_tools.get_conversation_history(
    session_id='session_123',
    limit=10
)

# Get formatted context window
context = context_tools.get_context_window(
    session_id='session_123',
    window_size=5
)

# Summarize long conversation
summary = context_tools.summarize_conversation(
    session_id='session_123'
)
```

### Integration with Orchestrator

The orchestrator automatically integrates context management:

```python
from agents.orchestrator import get_orchestrator

orchestrator = get_orchestrator()

# Create session
session_id = orchestrator.create_session(
    user_id='farmer_001',
    language='hi',
    metadata={'location': 'Uttar Pradesh', 'crops': ['wheat']}
)

# Process query with automatic context persistence
response = orchestrator.process_query(
    session_id=session_id,
    query='What is the best time to plant wheat?'
)

# Context is automatically:
# 1. Retrieved from DynamoDB
# 2. Included in agent prompt
# 3. Persisted back to DynamoDB
```

### Strands Tool Integration

Context tools are available as Strands @tool decorators:

```python
from tools.context_tools import (
    retrieve_conversation_context,
    summarize_long_conversation,
    get_user_conversation_history
)

# These tools can be added to Strands agents
# for automatic context management
```

## Session Lifecycle

### 1. Session Creation
```python
session_id = orchestrator.create_session(
    user_id='farmer_001',
    language='hi'
)
```

### 2. Message Processing
- User message saved to DynamoDB
- Context retrieved from DynamoDB
- Agent processes with context
- Response saved to DynamoDB

### 3. Session Restoration
```python
# Load existing session from DynamoDB
session_id = orchestrator.load_session_from_history(
    session_id='existing_session_123',
    user_id='farmer_001'
)
```

### 4. Session Timeout
- Automatic cleanup after 24 hours of inactivity
- TTL-based deletion in DynamoDB
- Manual cleanup available:
```python
orchestrator.cleanup_expired_sessions(timeout_hours=24)
```

## Conversation Summarization

### Automatic Summarization
- Triggered after 20 messages
- Runs every 10 messages thereafter
- Summary stored as system message

### Manual Summarization
```python
summary_result = context_tools.summarize_conversation(
    session_id='session_123'
)

if summary_result['success']:
    print(f"Summary: {summary_result['summary']}")
    print(f"Based on {summary_result['message_count']} messages")
```

### Summary Format
Summaries focus on:
1. Main topics discussed (crops, diseases, weather, etc.)
2. Key recommendations provided
3. Important context about farmer's situation
4. Follow-up actions needed

## Performance Considerations

### Caching Strategy
- Active sessions cached in memory
- DynamoDB queries only for context retrieval
- Context window limited to recent messages (default: 5 pairs)

### Cost Optimization
- TTL-based automatic cleanup (no Lambda costs)
- On-demand billing for DynamoDB
- Efficient indexing for fast queries
- Summarization uses cost-effective Haiku model

### Scalability
- DynamoDB auto-scales with demand
- No connection pooling needed (serverless)
- Supports 100K+ concurrent sessions
- Global secondary indexes for efficient queries

## Testing

### Unit Tests
```bash
cd RISE
python -m pytest tests/test_context_tools.py -v
```

### Integration Tests
Requires AWS credentials and DynamoDB table:
```bash
python tools/context_tools.py
```

## Configuration

### Environment Variables
```bash
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=RISE-ConversationHistory
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
```

### CDK Deployment
The DynamoDB table is automatically created via CDK:
```bash
cd infrastructure
cdk deploy
```

## Monitoring

### CloudWatch Metrics
- DynamoDB read/write capacity
- Query latency
- TTL deletion count
- Error rates

### Custom Metrics
- Messages per session
- Average conversation length
- Summarization frequency
- Context retrieval latency

## Security

### Data Protection
- Encryption at rest (AWS-managed KMS)
- Encryption in transit (TLS 1.2+)
- IAM-based access control
- Point-in-time recovery enabled

### Privacy
- TTL-based automatic deletion (24 hours)
- User data isolation via partition keys
- No cross-user data leakage
- GDPR-compliant data retention

## Troubleshooting

### Common Issues

**Issue: Context not persisting**
- Check AWS credentials
- Verify DynamoDB table exists
- Check IAM permissions

**Issue: Slow context retrieval**
- Reduce context window size
- Check DynamoDB capacity
- Verify GSI configuration

**Issue: Summarization failing**
- Check Bedrock model access
- Verify IAM permissions
- Check conversation length

## Future Enhancements

1. **Semantic Search**: Vector embeddings for context retrieval
2. **Multi-turn Planning**: Long-term conversation goals
3. **Context Compression**: Intelligent context pruning
4. **Cross-session Learning**: User preference learning
5. **Real-time Sync**: WebSocket-based context updates

## References

- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Strands Agents SDK](https://github.com/awslabs/strands-agents)
- [RISE Requirements](../RISE/.kiro/specs/rise-farming-assistant/requirements.md)
- [RISE Design](../RISE/.kiro/specs/rise-farming-assistant/design.md)

## Support

For issues or questions:
1. Check this README
2. Review test cases in `tests/test_context_tools.py`
3. Check CloudWatch logs
4. Review DynamoDB table configuration

---

**Version:** 1.0.0  
**Last Updated:** 2024  
**Status:** ✅ Implemented (Task 7 - Phase 2)
