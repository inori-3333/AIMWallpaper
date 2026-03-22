# AIMWallpaper

AI-driven [Wallpaper Engine](https://www.wallpaperengine.io/) dynamic wallpaper creation tool. Describe wallpaper effects in natural language, and the system automatically generates Wallpaper Engine project files with AI-powered effects, animations, and interactive components.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                     TopNav                           │
│  [AIMWallpaper]  [Project Dropdown]  [+ New Project] │
└─────────────────────────────────────────────────────┘
┌──────────────┬──────────────────┬────────────────────┐
│  AssetPanel  │   PreviewPanel   │    ChatPanel       │
│              │                  │                    │
│  Upload      │  Preview Image   │  Message List      │
│  Layer Tree  │  Refresh Btn     │  Chat Input        │
│  File List   │  Status          │  Status Indicator  │
└──────────────┴──────────────────┴────────────────────┘
```

**Backend:** Python 3.11+ / FastAPI / SQLAlchemy + SQLite / LiteLLM / ChromaDB

**Frontend:** React 19 / TypeScript / Vite / TailwindCSS / Zustand / React Query

## Features

- **Natural Language Creation** — Describe desired wallpaper effects via AI chat, the system generates valid Wallpaper Engine projects
- **Multi-Provider AI** — Supports OpenAI, Anthropic (Claude), and Ollama (local models) via LiteLLM
- **Knowledge Base** — ChromaDB vector store with semantic pattern retrieval for effect matching
- **Example Analyzer** — Import and analyze existing WE projects to learn reusable effect patterns
- **Scene Builder** — Assembles valid `scene.json` from layers, effects, and AI-generated SceneScript
- **Live Preview** — Wallpaper Engine CLI integration for preview and screenshot capture
- **Asset Management** — Drag-and-drop upload with layer tree organization
- **WebSocket Chat** — Real-time multi-turn AI conversation with streaming responses

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Wallpaper Engine](https://store.steampowered.com/app/431960/Wallpaper_Engine/) (optional, for live preview)

### Configuration

Copy and edit `config.yaml` with your settings:

```yaml
wallpaper_engine:
  path: "C:\\Program Files\\Steam\\steamapps\\common\\wallpaper_engine"

ai:
  default_provider: "openai"  # openai | anthropic | ollama
  openai:
    api_key: "sk-..."
    model: "gpt-4o"
  anthropic:
    api_key: "sk-ant-..."
    model: "claude-sonnet-4-20250514"
  ollama:
    base_url: "http://localhost:11434"
    model: "llama3"

embedding:
  provider: "openai"
  openai:
    model: "text-embedding-3-small"
  local:
    model: "all-MiniLM-L6-v2"
```

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:3000` and proxies API requests to the backend.

### Running Tests

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npx vitest run
```

## Project Structure

```
AIMWallpaper/
├── backend/
│   ├── app/
│   │   ├── api/          # REST & WebSocket endpoints
│   │   ├── core/         # AI engine, scene builder, knowledge base
│   │   ├── db/           # SQLAlchemy models & database
│   │   └── models/       # Pydantic schemas
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── api/          # REST client, React Query hooks, WebSocket
│   │   ├── stores/       # Zustand state management
│   │   ├── components/   # React components (ChatPanel, AssetPanel, etc.)
│   │   └── types/        # Shared TypeScript types
│   └── __tests__/
└── config.yaml
```

## API

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/projects` | Create project |
| GET | `/api/projects` | List projects |
| GET | `/api/projects/{id}` | Get project details |
| POST | `/api/projects/{id}/preview` | Trigger WE preview |
| POST | `/api/projects/{id}/export` | Export to WE directory |
| POST | `/api/assets/upload` | Upload file (multipart) |
| GET | `/api/assets` | List assets |
| DELETE | `/api/assets/{id}` | Delete asset |
| GET | `/api/knowledge/patterns` | Query effect patterns |
| GET | `/api/health` | Health check |

### WebSocket

Connect to `ws://localhost:8000/ws/chat/{project_id}` for real-time AI conversation.

## License

[Apache License 2.0](LICENSE)
