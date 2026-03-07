# RISE Agents – Multi-Agent, Single Architecture

## Design choice: one architecture for all agents

RISE uses a **multi-agent** design (orchestrator + specialists) but a **single architecture**: all agents are built with **AWS Strands Agents** and **Amazon Bedrock**. There are no mixed frameworks (e.g. no LangChain + Strands, no custom runners alongside Strands).

### Why one architecture?

| Benefit | Explanation |
|--------|-------------|
| **Consistency** | One SDK, one way to define tools, one invocation pattern. Easier to onboard and refactor. |
| **Unified observability** | Strands + OpenTelemetry give one trace model for all agents (orchestrator and specialists). |
| **Same runtime** | All agents run in the same process/container (e.g. ECS). No cross-service or cross-framework RPC. |
| **Tool reuse** | Tools are plain Python `@tool` functions; any agent can use the same tools without adapters. |
| **Simpler ops** | One stack to deploy, one set of env vars (e.g. `BEDROCK_MODEL_ID`), one place to tune model/prompts. |

### When you might use multiple architectures

- **Different runtimes**: e.g. one agent in Python (Strands), another in a separate service (Node/Go) with its own framework – only if you have a strong reason (team ownership, existing service).
- **Specialized needs**: e.g. a dedicated vision pipeline or a non-Strands workflow – you’d still usually call it as a **tool** from the Strands orchestrator, so the “agent layer” stays single-architecture.
- **Gradual migration**: temporarily running an old and a new framework; aim to converge to one.

For RISE, none of these requirements exist today, so a single architecture is the right default.

### Current vs target layout

- **Current**: One Strands agent (orchestrator) with `tools=[]`. No specialist agents yet; image/context/voice are used outside the agent (e.g. Streamlit → tools directly).
- **Target** (see `.kiro/specs/rise-farming-assistant/STRANDS_GUIDE.md`):  
  - **Orchestrator**: single Strands agent with a rich system prompt.  
  - **Specialists**: each domain (crop diagnosis, soil, weather, market, schemes, etc.) is a Strands agent with its own prompt and tools.  
  - **Integration**: specialists are exposed as **tools** to the orchestrator (e.g. `@tool def crop_diagnosis_assistant(query: str) -> str: return crop_expert(query)`).  
  - Optional: `agent_graph` for more complex flows (e.g. mesh or hierarchy).  
  All of this stays within Strands + Bedrock.

### Summary

Using **one architecture (Strands + Bedrock) for the whole multi-agent setup** is intentional and recommended: it keeps the system simple, observable, and easy to extend with more specialist agents and tools without introducing a second framework.
