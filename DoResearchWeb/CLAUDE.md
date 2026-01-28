# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

- **Development server**: `npm run dev` - Starts Vite dev server on host 0.0.0.0 (accessible externally)
- **Build**: `npm run build` - Creates production build using Vite
- **Lint**: `npm run lint` - Runs ESLint on all files
- **Preview**: `npm run preview` - Serves production build locally

## Architecture Overview

This is a React-based research paper management application built with Vite. The app provides a comprehensive interface for managing academic papers, reading lists, and research tasks.

### Key Technologies
- **Frontend**: React 19.1 with Material-UI (MUI) for components
- **Build Tool**: Vite 7.0 with React plugin
- **Routing**: React Router DOM with nested routes
- **HTTP Client**: Axios with custom interceptors
- **Charts**: Multiple charting libraries (Chart.js, Recharts, MUI X-Charts)
- **Environment**: Supports both Vite and Create React App environment variables

### Application Structure

The app follows a context-based state management pattern with three main contexts:

1. **PaperContext** (`src/contexts/PaperContext.jsx`) - Manages paper selection and current paper state
2. **DataContext** (`src/contexts/DataContext.jsx`) - Handles read-later functionality and statistics
3. **TaskContext** (`src/contexts/TaskContext.jsx`) - Manages research tasks

### Core Components

- **App.jsx** - Main application with responsive layout, MUI theme, and global error handling
- **Sidebar.jsx** - Navigation sidebar with feed-based paper organization
- **Views** (`src/components/views/`) - Main content areas:
  - `StatsView` - Dashboard with reading statistics and charts
  - `PapersView` - Feed-based paper listing with detail view
  - `ReadLaterView` - Read-later queue management
  - `TasksView` - Research task management
  - `EnhancedSearchView` - Advanced paper search functionality

### API Integration

The application uses a centralized API client (`src/services/apiClient.jsx`) with:

- Environment-aware base URL configuration
- Request/response interceptors for logging and error handling
- Comprehensive error handling with user-friendly messages
- Support for both development (`http://localhost:5000`) and production environments
- Timeout handling (30 seconds)

### Routing Structure

- `/` - Redirects to `/stats`
- `/stats` - Statistics dashboard
- `/readlater` - Read-later list
- `/tasks` - Task management
- `/search` - Paper search
- `/feed/:filter/:feedId` - Feed papers view
- `/feed/:filter/:feedId/paper/:paperId` - Paper detail view

### UI Features

- Responsive design with mobile-first approach
- Material-UI theme customization
- Mobile drawer navigation
- Global notification system using Snackbar
- Heatmap calendar for reading tracking
- Multiple chart types for data visualization

### Backend API Integration

The frontend integrates with a DoResearch Python backend API (Flask-based) running on `http://localhost:5000`. 

**Key API Categories:**
- **System**: Health checks (`/api/health`)
- **Feed Management**: CRUD operations for RSS feeds (`/api/feeds`)
- **Paper Operations**: Paper details, status updates, translation (`/api/papers`)
- **Search**: Full-text search with filters (`/api/search`, `/api/search/advanced`)
- **Read Later**: Queue management with priority/notes (`/api/read-later`)
- **Statistics**: Dashboard metrics and analytics (`/api/statistics/*`, `/api/stats`)
- **Task Management**: Async task processing (`/api/tasks`)
- **Agent System**: Distributed download agents with SSE (`/api/agent/*`)
- **Downloads**: PDF download services (`/api/download/*`)

**API Response Format:**
```json
{
  "success": true,
  "data": { /* response data */ }
}
```

**Key Backend Features:**
- SQLite database with paper metadata
- DeepSeek API integration for Chinese translation
- SSE (Server-Sent Events) for real-time agent communication
- Distributed PDF download system
- RSS feed parsing and updating
- Full-text search with relevance scoring
- Reading statistics and calendar tracking

**Environment Variables:**
- `DEEPSEEK_API_KEY`: Required for translation features
- Database: SQLite file-based storage
- PDF Storage: Local filesystem with configurable directory

### Error Handling

- Global error boundaries in App.jsx
- API error interceptors with status-specific messages
- Fallback data structures to prevent UI crashes
- User notification system for all operations

### Environment Configuration

The app supports both Vite and CRA environment variables:
- `VITE_API_BASE_URL` or `REACT_APP_API_BASE_URL` for API endpoint
- Development default: `http://localhost:5000`
- Production default: relative paths

### Code Conventions

- Chinese comments and UI text (this is a Chinese language application)
- Material-UI component patterns
- Context-based state management
- Functional components with hooks
- ESLint configuration with React hooks and refresh plugins