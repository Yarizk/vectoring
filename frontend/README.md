# KSEI RAG Frontend

React 19 + TypeScript + Tailwind CSS frontend for KSEI RAG.

## Features

- 🎨 Bloomberg Terminal aesthetic (dark theme)
- 💬 Rich chat interface with markdown rendering
- 📊 Inline data tables for financial data
- 🔍 Source citations and context panel
- 📈 Pipeline monitoring dashboard
- 🏎️ Built with Vite for fast development

## Tech Stack

- React 19
- TypeScript
- Tailwind CSS v4
- Zustand (state management)
- React Router v7
- React Markdown + Remark GFM
- Lucide React (icons)

## Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Development Server

- Frontend: http://localhost:5173
- API Proxy: http://localhost:5173/api (proxies to localhost:8000)

## Project Structure

```
src/
├── components/       # React components
│   ├── layout/      # Header, Sidebar, Panels
│   ├── chat/        # Chat components
│   ├── pipeline/    # Pipeline monitor
│   ├── ticker/      # Ticker display
│   ├── sources/     # Source components
│   └── ui/          # Reusable UI
├── pages/           # Route pages
├── hooks/           # Custom hooks
├── stores/          # Zustand stores
├── types/           # TypeScript types
├── lib/             # Utils, API, constants
└── assets/          # Static assets
```

## Environment Variables

Create `.env.local` for local overrides:

```env
VITE_API_URL=http://localhost:8000
```

## Production Build

The production build outputs to `dist/` which is served by the FastAPI backend.

```bash
cd frontend
npm run build
```

After building, the FastAPI server will serve the React app at the root URL.
