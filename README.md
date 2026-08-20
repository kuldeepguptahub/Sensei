# Sensei

> An AI-powered learning engine that builds personalized paths to mastery for any subject.

## Installation

```bash
# Clone the repository
git clone https://github.com/kuldeepguptahub/sensei.git
cd sensei

# Install dependencies
uv sync
```

## Quick Start

```bash
# 1. Connect to an LLM provider
sensei connect

# 2. Start learning a topic
sensei start-new-course

# 3. Or launch the web dashboard
sensei ui
```

## Connecting to a Provider

Sensei is model-agnostic and works with any OpenAI-compatible API. Run `sensei connect` to set up a provider interactively.

### Supported Providers

| Provider | Free Tier | Notes |
|----------|-----------|-------|
| OpenRouter | Yes | Aggregator with access to many models |
| OpenAI | No | GPT-4, GPT-4o |
| Anthropic | No | Claude models |
| Google | No | Gemini models |
| Ollama | Yes | Local models (no API key needed) |
| Hugging Face | Yes | Inference API with free tier |

### Example: OpenRouter (recommended for free usage)

1. Get a free API key at [openrouter.ai](https://openrouter.ai)
2. Run `sensei connect`
3. Select "OpenRouter" from the provider list
4. Paste your API key
5. Select a model (free models are marked with `free` tag)

### Example: Ollama (local, no API key)

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Pull a model: `ollama pull llama3`
3. Run `sensei connect`
4. Select "Ollama" — it auto-detects your local models

### Check your configuration

```bash
sensei current    # Show current provider and model
sensei models     # List available models
```

## Commands Reference

### Provider Management

| Command | Description |
|---------|-------------|
| `sensei connect` | Connect to an LLM provider (interactive setup) |
| `sensei current` | Show current provider and model configuration |
| `sensei models` | List available models from connected provider |
| `sensei models --provider NAME` | List models from a specific provider |
| `sensei setup` | Legacy setup command (use `connect` instead) |
| `sensei reset` | Reset config to defaults (no provider, no model) |

### Course Management

| Command | Description |
|---------|-------------|
| `sensei start-new-course` | Start a new course (interactive interview) |
| `sensei resume COURSE` | Resume a previously started course |
| `sensei list` | List all your courses and their status |
| `sensei complete-course COURSE` | Mark a course as completed |
| `sensei delete-course COURSE` | Delete a course and its workspace |
| `sensei rename-course COURSE NEW_NAME` | Rename a course |

### Web Dashboard

| Command | Description |
|---------|-------------|
| `sensei ui` | Launch the Streamlit web dashboard |

## Web Dashboard

Sensei includes a web-based dashboard for a more visual learning experience.

```bash
# Launch the dashboard (default port: 8501)
sensei ui

# Launch on a custom port
sensei ui --port 8080
```

The dashboard provides:

- **Home page** — Browse and manage all your courses
- **Chat interface** — Streaming conversation with the agent
- **Progress tracking** — Visual progress bar and status in the sidebar
- **Course creation** — Create new courses directly from the UI

## How It Works

1. **Interview** — Sensei asks adaptive questions to understand your goals, experience, and learning style
2. **Plan** — Creates a personalized curriculum with modules, lessons, and milestones
3. **Teach** — Guides you through lessons with explanations, examples, and exercises
4. **Assess** — Tracks your competency and adapts difficulty based on your performance
5. **Resume** — Persists your progress so you can pick up where you left off

## Why Sensei?

This project started as a personal experiment.

Like many developers, I wanted to deeply understand new technologies—frameworks, SDKs, APIs, programming languages, and distributed systems—not just use them.

Official documentation is usually excellent as a reference, but it isn't always designed to teach. It often assumes prior knowledge, skips over the reasoning behind design decisions, and rarely provides a structured roadmap from beginner to confident practitioner.

Naturally, I turned to Large Language Models like ChatGPT, Claude, and Gemini.

They were incredibly helpful…

...until they weren't.

I found myself repeatedly running into the same problems:

- No clear learning roadmap
- Concepts introduced before their prerequisites
- Too much information at once
- Code examples without enough explanation
- Exercises that were either trivial or overwhelming
- Long conversations slowly losing context
- Re-explaining my progress every time I started a new chat

The first solution was a giant prompt.

It worked surprisingly well.

Over time, that prompt evolved through hundreds of iterations. As the courses became longer and more interactive, it became clear that the real problem wasn't writing a better prompt—it was building a better learning system.

That's how **Sensei** was born.

Sensei is not another AI wrapper.

It is a model-agnostic learning framework that transforms technical documentation into an adaptive, interactive learning experience.

Instead of measuring how much you've read, Sensei measures what you can actually do.

It guides you from understanding concepts to building real projects, reviewing your code, adapting to your pace, and helping you develop engineering intuition—not just API knowledge.

Whether you use OpenAI, Anthropic, Google, Ollama, or another compatible model, Sensei's goal remains the same:

> Help you master any technology, any subject, not just finish reading their documentation.

## What Makes Sensei Different?

Traditional AI chats → answer questions → conversation is the memory → eventually lose context → start over.

Sensei → builds a learning roadmap → guides implementation → tracks competency → maintains learning state → resume anytime → adaptive mentoring.

Sensei believes that learning is not measured by the number of pages you've read or prompts you've written.

Learning is measured by what you can explain, implement, debug, extend, and build independently.

That's the metric Sensei optimizes for.