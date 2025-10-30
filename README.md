# 🤖 STAN - Conversational AI Chatbot

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

> A Gen-Z personality chatbot with contextual memory, web search capabilities, and emotional intelligence built using FastAPI and multiple LLM providers.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Setup Instructions](#setup-instructions)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Testing](#testing)
- [Performance](#performance)
- [Contributing](#contributing)

---

## 🎯 Overview

**STAN** (Smart Talking AI Networker) is an intelligent conversational agent designed to provide human-like interactions with memory retention, contextual awareness, and emotional understanding. Built with modern Python frameworks, it supports multiple LLM providers and implements RAG (Retrieval-Augmented Generation) for enhanced conversational capabilities.

### Key Highlights

- **Multi-Provider LLM Support**: Gemini, Claude, Groq
- **Persistent Memory**: ChromaDB vector store for long-term conversation history
- **Web Search Integration**: Real-time information retrieval via Serper API
- **Emotional Intelligence**: Context-aware responses matching user sentiment
- **Rate Limiting**: Intelligent request management across providers
- **Gen-Z Personality**: Natural, relatable communication style

---

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
│  (Chat UI)  │
└──────┬──────┘
       │ HTTP/JSON
       ▼
┌─────────────────────────────────────────────┐
│           FastAPI Backend                   │
│  ┌─────────────────────────────────────┐   │
│  │      Chat Router (Endpoints)        │   │
│  └───────────────┬─────────────────────┘   │
│                  │                          │
│  ┌───────────────▼──────────────┐          │
│  │     Memory Manager            │          │
│  │  • Short-term buffer (8 msgs) │          │
│  │  • Long-term storage (Vector) │          │
│  └───────────────┬───────────────┘          │
│                  │                          │
│  ┌───────────────▼──────────────┐          │
│  │    Prompt Builder             │          │
│  │  • Context injection          │          │
│  │  • Memory formatting          │          │
│  └───────────────┬───────────────┘          │
│                  │                          │
│  ┌───────────────▼──────────────┐          │
│  │      LLM Client               │          │
│  │  • Provider selection         │          │
│  │  • Rate limiting              │          │
│  │  • Web search integration     │          │
│  └───────────────┬───────────────┘          │
└──────────────────┼──────────────────────────┘
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
┌──────────────┐      ┌──────────────┐
│  ChromaDB    │      │  LLM APIs    │
│ Vector Store │      │ (Multi-provider)│
└──────────────┘      └──────────────┘
```

### Data Flow

1. **User Input** → FastAPI endpoint receives message
2. **Memory Retrieval** → Fetch relevant past conversations (RAG)
3. **Context Building** → Combine recent chat + retrieved memories
4. **Prompt Generation** → Build structured prompt with personality
5. **LLM Call** → Send to configured provider (with rate limiting)
6. **Web Search** (if needed) → Augment response with real-time data
7. **Memory Storage** → Save interaction to vector store
8. **Response** → Return AI reply to client

---

##  Features

###  Contextual Memory System

- **Short-term Buffer**: Maintains last 8 messages for immediate context
- **Long-term Vector Storage**: Semantic search across conversation history
- **Intelligent Filtering**: Saves only meaningful information (names, preferences, facts)
- **Duplicate Prevention**: Avoids redundant memory entries

###  Web Search Integration

- **Automatic Detection**: Triggers search for queries like "tell me about X"
- **Serper API**: Fast, reliable Google search results
- **Context Injection**: Seamlessly integrates search results into responses
- **Smart Caching**: Avoids unnecessary searches for known topics

###  Personality & Tone

- **Gen-Z Voice**: Natural, casual language with appropriate slang
- **Emotional Matching**: Adjusts tone based on user sentiment
- **Varied Greetings**: Never repeats the same greeting twice
- **Interest-based**: Knows sports, anime, gaming, tech

###  Performance Optimization

- **Rate Limiting**: Per-provider request management
- **Usage Tracking**: Monitors daily/minute limits
- **Retry Logic**: Automatic recovery from transient failures
- **Timeout Handling**: Graceful degradation on slow responses

---

##  Tech Stack

### Backend Framework
- **FastAPI** - Modern, fast web framework for APIs
- **Uvicorn** - ASGI server for production deployment
- **Pydantic** - Data validation and settings management

### LLM Providers
- **Google Gemini 2.0 Flash** - Primary (15 req/min, 1.5M req/day)
- **Anthropic Claude 3.5 Haiku** - High-quality responses
- **Groq Llama 3.3 70B** - Fast inference
- **Cohere Command R** - Backup option

### Memory & Storage
- **ChromaDB** - Vector database for semantic search
- **Sentence Transformers** - Embedding model (all-MiniLM-L6-v2)
- **Persistent Storage** - Local file-based memory

### External Services
- **Serper API** - Web search functionality
- **HTTPX** - Async HTTP client for API calls

### Development Tools
- **Python 3.9+** - Core language
- **Colorama** - CLI color formatting
- **python-dotenv** - Environment management

---

##  Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip package manager
- API keys for at least one LLM provider

### Local Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/stan-chatbot.git
cd stan-chatbot
```

2. **Set up virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
cd backend
pip install fastapi uvicorn httpx python-dotenv chromadb sentence-transformers colorama pydantic
```

4. **Configure environment variables**

Create `backend/app/.env` file:
```env
# Choose one provider (gemini, claude, groq, cohere)
LLM_PROVIDER=gemini

# Add API keys (at least one required)
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_claude_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Optional: Web search (added for do you know questions)
SERPER_API_KEY=your_serper_api_key_here

# Optional: Model overrides
GEMINI_MODEL=gemini-2.0-flash-exp
CLAUDE_MODEL=claude-3-5-haiku-20241022
GROQ_MODEL=llama-3.3-70b-versatile
COHERE_MODEL=command-r-08-2024
```

5. **Run the server**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at `http://localhost:8000`

6. **Test the chatbot**

In a new terminal:
```bash
cd backend
python chat_test.py
```

---

## 📁 Project Structure

```
stan-chatbot/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── llm_client.py          # LLM provider interface
│   │   │   ├── memory_manager.py      # Memory operations
│   │   │   └── prompt_templates.py    # Prompt engineering
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── vector_store.py        # ChromaDB operations
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py             # Pydantic models
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── chat.py                # API endpoints
│   │   ├── __init__.py
│   │   ├── .env                        # Environment variables
│   │   └── .gitignore
│   ├── chroma_memory/                  # Vector DB storage
│   ├── main.py                         # FastAPI app entry
│   ├── chat_test.py                    # Interactive CLI client
│   └── quick_test.py                   # Performance tests
├── .gitignore
└── README.md
```

---

## 📡 API Documentation

### Endpoints

#### 1. Health Check
```http
GET /
```
**Response:**
```json
{
  "message": "STAN backend is running 🚀"
}
```

#### 2. Send Message
```http
POST /api/v1/message
```
**Request Body:**
```json
{
  "user_id": "john_doe",
  "message": "Hey! What's up?"
}
```

**Response:**
```json
{
  "reply": "hey! not much, just chilling. what about you?",
  "metadata": {
    "turn_id": 1
  }
}
```

#### 3. Reset Conversation
```http
POST /api/v1/reset?user_id=john_doe
```
**Response:**
```json
{
  "message": "Conversation reset for john_doe"
}
```

### Interactive API Docs

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## ⚙️ Configuration

### LLM Provider Selection

Edit `backend/app/.env`:
```env
LLM_PROVIDER=gemini  # Options: gemini, claude, groq, cohere
```

### Rate Limits (Default)

| Provider | Requests/Min | Requests/Day | Tokens/Min |
|----------|--------------|--------------|------------|
| Gemini   | 15           | 1,500        | 1,000,000  |
| Claude   | 50           | 100,000      | 40,000     |
| Groq     | 30           | 14,400       | 20,000     |


### Memory Settings

In `memory_manager.py`:
- `max_buffer_size`: Short-term buffer size (default: 8)
- `top_k`: Number of memories to retrieve (default: 4)

### Response Parameters

In `chat.py`:
- `max_tokens`: Maximum response length (default: 256)
- `temperature`: Creativity level (default: 0.7)
- `timeout_seconds`: API timeout (default: 30)

---

## 🧪 Testing

### Quick Performance Test
```bash
cd backend
python quick_test.py
```

**Tests:**
- Response time measurement
- Search trigger detection
- Memory recall accuracy
- Rate limiting behavior

### Interactive Chat Test
```bash
cd backend
python chat_test.py
```

**Features:**
- Real-time conversation
- Color-coded output
- Connection status monitoring
- Commands: `reset`, `clear`, `quit`

### Expected Performance

- **Regular queries**: < 2 seconds
- **Search queries**: 2-4 seconds
- **Memory recall**: < 1 second
- **Rate limit handling**: Automatic backoff

---

## 📊 Performance

### Optimization Strategies

1. **Rate Limiting**: Prevents API quota exhaustion
2. **Async Operations**: Non-blocking I/O for all API calls
3. **Memory Caching**: Recent context stored in-memory
4. **Smart Search**: Only triggers when necessary
5. **Retry Logic**: Automatic recovery from failures

### Scalability Considerations

- **Horizontal Scaling**: Stateless design allows multiple instances
- **Vector DB**: ChromaDB handles millions of embeddings
- **Provider Switching**: Automatic fallback if primary fails
- **Usage Tracking**: Monitors and warns before limits

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add docstrings to functions
- Write tests for new features
- Update documentation

---


## 🙏 Acknowledgments

- **Anthropic** - Claude API
- **Google** - Gemini API
- **ChromaDB** - Vector database
- **FastAPI** - Web framework
- **Hugging Face** - Sentence Transformers

---

Peace!!
