# Agentica

Agentica is an AI-powered multi-agent decision simulation platform.

Instead of giving one AI answer, Agentica creates multiple AI agents such as **Customer, Investor, Expert, Marketing, Critic, and Red Team Agent**. These agents debate, analyze, and simulate stakeholder behavior to predict outcomes in real-world scenarios.

## What it does

- Takes a user query, idea, or document as input
- Builds a **knowledge graph** using GraphRAG
- Spawns multiple AI agents with unique roles and biases
- Runs a simulation using social-style discussions
- Stores memory for context-aware reasoning
- Produces a structured prediction with:
  - Final decision
  - Confidence score
  - Key reasoning
  - Influential agents
  - Scenario comparisons

## Unique Features

- 🔴 **Red Team Agent** for adversarial risk analysis
- 🗺️ **Decision Tree Visualization** for explainable reasoning
- 📊 **Consensus Heatmap** to show agent agreement/disagreement
- 🧑💻 **Human-as-an-Agent** for interactive participation
- 🦋 **Butterfly Effect Mode** to test “what-if” changes

## Tech Stack

- **Frontend:** Next.js + Tailwind CSS
- **Backend:** FastAPI
- **Graph DB:** Neo4j
- **Memory:** MongoDB / Mem0
- **LLM:** OpenRouter API
- **Agent Architecture:** CAMEL-style multi-agent system

## Use Cases

- Business strategy simulation
- Product launch validation
- Market trend prediction
- Investment decision support
- Policy and planning analysis

## Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/your-username/agentica.git
cd agentica
```
