# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DoResearch is a Chinese research paper management system that provides:
- Paper feed monitoring and RSS management
- **NEW: Template-based subscription management system**
- PDF downloading from IEEE and other sources
- Deep analysis using DeepSeek AI
- Reading status tracking and statistics
- SSE-based task queue system with distributed agents

## Architecture

### Core Components
- **Flask Web Server** (`app.py`) - Main application with modular route handlers
- **Agent System** (`agents/ieee_agent.py`) - Distributed workers for paper downloading
- **Task Management** (`services/task_*.py`) - Queue system with SSE communication
- **Paper Management** (`services/paper_manager.py`) - CRUD operations for papers and feeds
- **NEW: Subscription Management** (`services/subscription_service.py`) - Template-based subscription system
- **Database Layer** (`models/database.py`, `models/subscription_models.py`) - SQLite with papers, feeds, tasks, and subscription tables

### Data Flow
1. RSS feeds are monitored for new papers
2. Papers are stored in SQLite database with status tracking
3. Users can trigger analysis tasks via web interface
4. Tasks are queued and processed by agents via SSE
5. Results are stored and made available through API

## Development Commands

### Starting the Application
```bash
python app.py
```
Main server runs on `http://localhost:5000`

### Starting an IEEE Agent
```bash
python -c "
import sys, os
sys.path.append(os.path.dirname(__file__))
from agents.ieee_agent import IEEEAgent
agent = IEEEAgent(agent_id='ieee-agent-001', server_endpoint='http://localhost:5000', port=5001)
agent.run()
"
```

### Database Management
The application automatically creates required SQLite tables on startup. Manual database operations can be performed using the `Database` class from `models/database.py`.

## Configuration

### Required Environment
- DeepSeek API key must be set in `config.py`
- SQLite database (`papers.db`) is created automatically
- PDF storage directory (`data/pdfs/`) is created automatically

### Key Settings (`config.py`)
- `DEEPSEEK_API_KEY` - AI analysis service
- `DATABASE_PATH` - SQLite database location
- `PDF_DIR` - Downloaded PDF storage
- `TASK_CHECK_INTERVAL` - Task polling frequency
- `AGENT_HEARTBEAT_TIMEOUT` - Agent connection timeout

## API Structure

### Main Endpoints
- `/api/health` - System health check
- `/api/feeds` - Paper source management
- `/api/papers/<id>` - Paper CRUD operations
- `/api/tasks` - Task queue management
- `/api/statistics/*` - Reading analytics
- `/api/agent/*` - Agent registration and SSE
- `/api/download/*` - Paper download services

### SSE Communication
Agents connect via `/api/agent/<id>/events` for real-time task distribution. The system uses SQLite-backed task queues with automatic failover.

## File Structure Notes

- Route handlers are split across `app_*.py` files by functionality
- Services in `services/` are stateful and manage business logic
- Models in `models/` handle database schema and operations
- Static files and templates follow standard Flask conventions
- Agent code is isolated in `agents/` directory

## Testing

### New Subscription System Testing
Run the test script to verify the new subscription management system:
```bash
python test_subscription_system.py
```

### Manual Testing
Manual testing can be done through the web interface and API endpoints listed in the startup output. The new subscription management APIs are available under `/api/v2/` and `/api/admin/` prefixes.

## New Subscription Management System (v2)

### Overview
The new subscription management system provides a template-based approach where:
- **Administrators** maintain predefined subscription templates for different sources (IEEE, Elsevier, DBLP)
- **Users** create subscriptions by selecting templates and providing parameters
- **External microservice** handles the actual paper fetching with standardized APIs
- **Automatic synchronization** keeps subscriptions updated based on user-defined frequencies

### Architecture
```
DoResearch Backend ←→ External Paper Fetcher Service
     ↓
Template-based subscriptions → Standardized paper data → Existing papers table
```

### Key Components

#### Database Tables
- `subscription_templates` - Admin-maintained subscription types
- `user_subscriptions` - User-created subscriptions with parameters  
- `subscription_sync_history` - Sync execution logs and statistics
- `papers` - Extended with `subscription_id` field for new data source tracking

#### Services
- `SubscriptionTemplateManager` - Template CRUD operations
- `UserSubscriptionManager` - User subscription lifecycle management
- `SubscriptionSyncService` - Background synchronization with external service
- `ExternalServiceClient` - HTTP client for paper fetcher microservice
- `PaperProcessor` - Standardizes and stores fetched paper data

#### APIs
**User APIs (v2):**
- `GET /api/v2/subscription-templates` - Browse available subscription types
- `POST /api/v2/subscriptions` - Create subscription from template
- `GET /api/v2/subscriptions` - List user's subscriptions
- `POST /api/v2/subscriptions/{id}/sync` - Manual sync trigger
- `GET /api/v2/subscriptions/{id}/papers` - Get papers from subscription

**Admin APIs:**
- `GET /api/admin/subscription-templates` - Manage templates
- `POST /api/admin/subscription-templates` - Create new template
- `GET /api/admin/external-service/health` - Check microservice status

### Supported Source Types

#### IEEE Journals
- **Parameters:** `pnumber` (IEEE publication number)
- **Sync Strategy:** Latest N papers, daily/weekly
- **Example:** `{"pnumber": "5962382"}` for IEEE Computer Society

#### Elsevier Journals  
- **Parameters:** `pnumber` (ISSN or journal ID)
- **Sync Strategy:** Latest N papers, daily/weekly
- **Example:** `{"pnumber": "0164-1212"}` for Information and Software Technology

#### DBLP Conferences
- **Parameters:** `dblp_id` (conference ID), `year` (conference year) 
- **Sync Strategy:** All papers from specific year, less frequent updates
- **Example:** `{"dblp_id": "icse", "year": 2024}` for ICSE 2024

### External Microservice Interface

#### Required Endpoints
```
POST /api/v1/fetch
{
  "source": "ieee|elsevier|dblp", 
  "source_params": {...}
}
```

#### Expected Response Format
```json
{
  "success": true,
  "data": {
    "papers": [
      {
        "title": "...",
        "abstract": "...", 
        "authors": ["..."],
        "journal": "...",
        "published_date": "2024-01-01",
        "url": "...",
        "pdf_url": "...",
        "doi": "...",
        "keywords": ["..."],
        "citations": 10,
        "source_specific": {...},
        "metadata": {...}
      }
    ],
    "total_count": 100
  }
}
```

### Configuration
Environment variables for customization:
- `PAPER_FETCHER_SERVICE_URL` - External service URL (default: http://localhost:8000)
- `SYNC_CHECK_INTERVAL` - Sync check frequency in seconds (default: 60)
- `DEFAULT_SYNC_FREQ` - Default subscription sync frequency (default: 86400)
- `MAX_SUBSCRIPTIONS_PER_USER` - Per-user subscription limit (default: 50)

### Integration with Existing System
- New subscription data flows into existing `papers` table
- Existing feed-based subscriptions continue working unchanged
- Statistics and search APIs automatically include both data sources
- User interface can offer choice between legacy feeds and new template subscriptions

### Development Workflow
1. **Testing:** Run `python test_subscription_system.py` to verify system
2. **External Service:** Deploy paper fetcher microservice separately  
3. **Template Management:** Use admin APIs to define new subscription types
4. **User Migration:** Gradually migrate users from legacy feeds to templates
5. **Monitoring:** Check sync history and error logs via admin APIs