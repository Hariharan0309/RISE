# AWS Strands Agents - Quick Reference for RISE

## What is AWS Strands Agents?

AWS Strands Agents is an open-source Python framework for building autonomous AI agents with a model-first approach. Instead of hardcoding workflows, you let the LLM (Large Language Model) decide how to solve problems using tools you provide.

## Key Concepts

### 1. Agent
The core class that represents an AI agent. It has:
- A **model** (e.g., Claude 3 Sonnet on Amazon Bedrock)
- A **system prompt** (defines the agent's role and behavior)
- A list of **tools** (functions the agent can call)

```python
from strands import Agent

agent = Agent(
    system_prompt="You are a helpful farming assistant.",
    tools=[weather_tool, crop_diagnosis_tool]
)

response = agent("What crops should I plant this season?")
```

### 2. Tools (@tool decorator)
Tools are Python functions that agents can call. Use the `@tool` decorator:

```python
from strands import tool

@tool
def get_weather(location: str) -> str:
    """Get current weather for a location."""
    # Your implementation
    return f"Weather in {location}: Sunny, 25°C"
```

The docstring is important - the agent uses it to understand when to use the tool.

### 3. Supervisor-Agent Pattern
Create specialist agents and wrap them as tools for an orchestrator:

```python
from strands import Agent, tool

# Create specialist agent
crop_expert = Agent(
    system_prompt="You are a crop disease expert.",
    tools=[image_analysis_tool, treatment_database_tool]
)

# Wrap specialist as a tool
@tool
def crop_diagnosis_assistant(query: str) -> str:
    """Diagnose crop diseases and recommend treatments."""
    return crop_expert(query)

# Orchestrator uses specialist as a tool
orchestrator = Agent(
    tools=[crop_diagnosis_assistant, weather_assistant, market_assistant]
)
```

### 4. Multi-Agent Networks
For complex scenarios, create networks of agents that communicate:

```python
from strands import agent_graph

# Define agent network
graph = agent_graph(
    agents={
        "research": research_agent,
        "analysis": analysis_agent,
        "synthesis": synthesis_agent
    },
    topology="mesh"  # or "star", "hierarchy"
)
```

### 5. Observability (OTEL)
Strands has built-in OpenTelemetry support for tracing:

```python
# Traces automatically capture:
# - Model calls (prompt, response, tokens)
# - Tool invocations (input, output, duration)
# - Agent reasoning steps

# Send traces to AWS X-Ray and CloudWatch
```

## RISE Architecture with Strands

```
┌─────────────────────────────────────────────────────────┐
│                  RISE Orchestrator Agent                │
│  (Main agent that handles user queries)                 │
│                                                          │
│  System Prompt: "You are RISE, a multilingual farming   │
│  assistant for Indian farmers..."                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Uses specialist agents as tools
                     │
        ┌────────────┼────────────┬──────────────┐
        │            │            │              │
        ▼            ▼            ▼              ▼
┌──────────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐
│ Crop         │ │ Soil     │ │ Weather │ │ Market   │
│ Diagnosis    │ │ Analysis │ │ Agent   │ │ Agent    │
│ Agent        │ │ Agent    │ │         │ │          │
└──────────────┘ └──────────┘ └─────────┘ └──────────┘
       │                │            │           │
       │                │            │           │
       ▼                ▼            ▼           ▼
   [Tools]          [Tools]      [Tools]     [Tools]
```

## Installation

```bash
# Install Strands Agents SDK
pip install strands-agents strands-agents-tools

# Install AWS SDK for Bedrock
pip install boto3
```

## Basic Example for RISE

```python
from strands import Agent, tool
import boto3

# Configure Amazon Bedrock
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# Define a simple tool
@tool
def get_crop_price(crop: str, location: str) -> str:
    """Get current market price for a crop in a location."""
    # Your implementation here
    return f"Price of {crop} in {location}: ₹2500/quintal"

# Create the agent
agent = Agent(
    model_provider="bedrock",  # Use Amazon Bedrock
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    system_prompt="""You are RISE, an AI farming assistant for Indian farmers.
    You help with crop advice, market prices, weather, and more.
    Always respond in a helpful, clear manner.""",
    tools=[get_crop_price]
)

# Use the agent
response = agent("What is the price of wheat in Punjab?")
print(response)
```

## Integration with Amazon Bedrock

```python
from strands import Agent

# Use Claude 3 Sonnet on Bedrock
agent = Agent(
    model_provider="bedrock",
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region="us-east-1",
    system_prompt="Your prompt here",
    tools=[tool1, tool2]
)

# Use Amazon Nova Pro
agent = Agent(
    model_provider="bedrock",
    model_id="amazon.nova-pro-v1:0",
    region="us-east-1",
    system_prompt="Your prompt here",
    tools=[tool1, tool2]
)
```

## Multimodal Support (Images)

```python
from strands import Agent

agent = Agent(
    model_provider="bedrock",
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    system_prompt="You are a crop disease expert."
)

# Send image with query
response = agent(
    "What disease does this crop have?",
    images=["path/to/crop_image.jpg"]
)
```

## Session Management

```python
from strands import Agent

agent = Agent(
    system_prompt="You are a farming assistant.",
    tools=[weather_tool]
)

# Maintain conversation context
session_id = "user_123"

response1 = agent("What's the weather in Punjab?", session_id=session_id)
response2 = agent("Should I plant wheat there?", session_id=session_id)
# Agent remembers the location from previous query
```

## Error Handling

```python
from strands import Agent

agent = Agent(
    system_prompt="You are a farming assistant.",
    tools=[weather_tool],
    max_iterations=10,  # Prevent infinite loops
    timeout=30  # Timeout in seconds
)

try:
    response = agent("Your query here")
except Exception as e:
    print(f"Agent error: {e}")
```

## Deployment Options

### 1. AWS Lambda (Serverless)
```python
import json
from strands import Agent

agent = Agent(...)

def lambda_handler(event, context):
    query = event['query']
    response = agent(query)
    return {
        'statusCode': 200,
        'body': json.dumps({'response': response})
    }
```

### 2. Amazon Bedrock AgentCore (Recommended for Production)
```python
from strands import Agent
from strands.bedrock import BedrockAgentCoreApp

agent = Agent(...)

# Wrap agent for AgentCore deployment
app = BedrockAgentCoreApp(agent)

# Deploy using AWS CLI or CDK
```

### 3. Container (ECS/Fargate)
```python
from flask import Flask, request
from strands import Agent

app = Flask(__name__)
agent = Agent(...)

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    response = agent(data['query'])
    return {'response': response}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

## Observability Setup

```python
from strands import Agent
import os

# Enable OTEL tracing
os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4317'
os.environ['OTEL_SERVICE_NAME'] = 'rise-agent'

agent = Agent(
    system_prompt="You are a farming assistant.",
    tools=[tool1, tool2],
    enable_tracing=True  # Enable OTEL traces
)

# Traces will be sent to AWS X-Ray via OTEL collector
```

## Best Practices for RISE

1. **Clear System Prompts**: Define the agent's role, expertise, and behavior clearly
2. **Descriptive Tool Docstrings**: Help the agent understand when to use each tool
3. **Tool Granularity**: Create focused tools that do one thing well
4. **Error Handling**: Implement robust error handling in tools
5. **Caching**: Cache expensive operations (API calls, database queries)
6. **Monitoring**: Use OTEL traces to understand agent behavior
7. **Testing**: Test agents with various inputs and edge cases
8. **Security**: Validate inputs, sanitize outputs, use Bedrock Guardrails

## Common Patterns for RISE

### Pattern 1: Voice Query Processing
```python
@tool
def transcribe_voice(audio_file: str) -> str:
    """Convert voice audio to text."""
    # Use Amazon Transcribe
    return transcribed_text

@tool
def synthesize_speech(text: str, language: str) -> str:
    """Convert text to speech."""
    # Use Amazon Polly
    return audio_url

agent = Agent(
    tools=[transcribe_voice, synthesize_speech, ...]
)
```

### Pattern 2: Image Analysis
```python
@tool
def analyze_crop_image(image_path: str) -> dict:
    """Analyze crop image for diseases."""
    # Use Bedrock multimodal
    return {
        'disease': 'Leaf Blight',
        'severity': 'Moderate',
        'treatment': '...'
    }

agent = Agent(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    tools=[analyze_crop_image]
)
```

### Pattern 3: Multi-Step Workflow
```python
# Agent automatically chains tools
agent = Agent(
    system_prompt="You help farmers with complete solutions.",
    tools=[
        get_soil_analysis,
        recommend_crops,
        calculate_profitability,
        find_suppliers
    ]
)

# Agent will use multiple tools as needed
response = agent("I have sandy soil in Punjab. What should I plant?")
# Agent might: analyze soil → recommend crops → calculate profit → find suppliers
```

## Resources

- [Strands Agents GitHub](https://github.com/awslabs/strands-agents)
- [Strands Documentation](https://strands-agents.readthedocs.io/)
- [AWS Blog Post](https://aws.amazon.com/blogs/machine-learning/strands-agents-sdk-a-technical-deep-dive-into-agent-architectures-and-observability/)
- [Amazon Bedrock](https://aws.amazon.com/bedrock/)
- [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/)

## Next Steps for RISE

1. Start with Task 1: Install Strands Agents SDK
2. Create a simple orchestrator agent (Task 3)
3. Build your first tool (e.g., weather tool - Task 15)
4. Create your first specialist agent (e.g., crop diagnosis - Task 8)
5. Test agent-to-agent communication (Task 36)
6. Deploy to Amazon Bedrock AgentCore (Task 52-54)

Good luck building RISE with AWS Strands Agents! 🚜🌾
