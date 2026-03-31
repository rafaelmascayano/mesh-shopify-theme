# Growth Orchestration System — Complete Technical Guide

**Version:** 1.0.0
**Last Updated:** March 29, 2026
**Status:** MVP (framework complete, awaiting data integration)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Data Flow](#data-flow)
4. [Database Schema](#database-schema)
5. [API & Integration](#api--integration)
6. [Configuration](#configuration)
7. [Deployment](#deployment)
8. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Architecture Overview

### System Design

```
┌─────────────────────────────────────────────┐
│   Growth Orchestrator (Opus 4.6)            │
│   Runs nightly or on-demand                 │
└──────────────────┬──────────────────────────┘
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
    SEO Agent  Product Agent  Data Agent
    (Haiku)    (Haiku)        (Haiku)
       │           │           │
       └───────────┼───────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
Tools Layer (MCP)    Database
├─ supabase_tools    (PostgreSQL)
├─ analytics_tools   ├─ growth_briefs
└─ content_tools     ├─ action_queue
                     ├─ channel_metrics
                     └─ entity_scores
```

### Key Design Principles

1. **Composable Channels**: Each growth channel (SEO, Product, Paid, Email, Data) is independent but coordinated
2. **Async-First**: All I/O is async; orchestrator can parallelize subagent calls
3. **Structured Output**: Pydantic schemas enforce output contracts; no string parsing
4. **Cost-Optimized**: Prompt caching for stable system prompts; Batch API for bulk operations; tier-appropriate models (Opus for orchestration, Haiku for subagents)
5. **Persistence-First**: Every run is logged; action queue is durably persisted; no in-memory-only state

---

## Core Components

### 1. Orchestrator (`growth/orchestrator.py`)

**Purpose**: Coordinates multi-channel analysis and synthesizes insights.

**Key Methods**:
- `run_growth_cycle(channels, trigger)` — Main entry point
- `analyze_single_channel(channel)` — Debug individual channels

**In Production**:
```python
from growth.orchestrator import create_orchestrator

orchestrator = create_orchestrator(model="claude-opus-4-6")
brief = await orchestrator.run_growth_cycle(channels=["seo", "product"], trigger="scheduled")
```

### 2. Subagents (`growth/agents/`)

Each channel has a specialized agent with:
- Scoped system prompt (frozen for caching)
- Restricted tool set (only relevant integrations)
- Typed output schema (Pydantic)

**SEO Agent** (`seo_agent.py`)
- Analyzes Google Search Console
- Identifies keyword opportunities
- Recommends content improvements
- Output: `SeoInsights`

**Product Agent** (`product_agent.py`)
- Analyzes GA4 funnel metrics
- Evaluates listing quality
- Detects retention issues
- Output: `ProductInsights`

**Data Agent** (future)
- Aggregates cross-channel metrics
- Detects anomalies
- Calculates compound scores

### 3. Tools (`growth/tools/`)

Atomic data access functions wrapped as `@beta_tool` (Claude Tool Runner).

**Supabase Tools** (`supabase_tools.py`)
- `query_listings()` — Fetch product inventory
- `write_action_item()` — Persist action to queue
- `get_metric_history()` — Time-series metrics

**Analytics Tools** (`analytics_tools.py`)
- `gsc_query()` — Google Search Console data
- `ga4_query()` — Google Analytics 4 data

### 4. Schemas (`growth/schemas/`)

**GrowthBrief** (`brief.py`)
- Root output type
- Contains: executive summary, per-channel insights, ranked actions, scores

**Channel Insights** (`insights.py`)
- `SeoInsights` — SEO analysis output
- `ProductInsights` — Product/UX analysis
- `PaidInsights` — Advertising performance
- `EmailInsights` — Email marketing metrics
- `DataInsights` — Cross-channel anomalies

**Scoring** (`scoring.py`)
- `EntityScore` — Composite score for a listing/keyword/page
- `CompoundScore` — Individual signal component

### 5. Persistence (`growth/store/`)

**Briefs** (`briefs.py`)
- `save_brief()` — Write GrowthBrief to `growth_briefs` table
- `get_latest_brief()` — Retrieve recent brief

**Actions** (`actions.py`)
- `write_action_queue()` — Populate `action_queue` table
- `get_pending_actions()` — Fetch actionable items

**Metrics** (`metrics.py`)
- `log_metric()` — Write time-series data to `channel_metrics`

### 6. Utilities (`growth/utils/`)

**Cache** (`cache.py`)
- `cached_tool_result()` — Memoize external API calls
- `hash_prompt()` — Track cacheable blocks for Prompt Caching API

**Cost Tracker** (`cost_tracker.py`)
- `track_usage()` — Log token consumption and estimate cost

**Retry** (`retry.py`)
- `retry_with_backoff()` — Exponential backoff for API failures

### 7. Scheduler (`growth/scheduler.py`)

Celery task definitions.

```python
from growth.scheduler import celery_app, run_growth_cycle_task

# Runs automatically at 23:00 UTC daily
celery_app.conf.beat_schedule = {
    "nightly-growth-cycle": {
        "task": "growth.scheduler.run_growth_cycle_task",
        "schedule": crontab(hour=23, minute=0),
    }
}
```

---

## Data Flow

### Nightly Execution (23:00 UTC)

```
1. Celery beat triggers run_growth_cycle_task()
   └─> Load 7-day windows from each data source
       ├─ GSC: clicks, impressions, ranking changes
       ├─ GA4: sessions, pageviews, conversions
       ├─ Supabase: new listings, contacts, transactions
       └─ Cache results locally (TTL 6h)

2. Orchestrator.run_growth_cycle()
   └─> Invoke 3 subagents in parallel (30s timeout each)
       ├─ SEO Agent
       │  ├─ Analyze GSC trends
       │  ├─ Identify keyword clusters
       │  └─> SeoInsights (JSON)
       ├─ Product Agent
       │  ├─ Analyze GA4 funnel
       │  ├─ Check listing quality metrics
       │  └─> ProductInsights (JSON)
       └─ Data Agent
          ├─ Merge all metrics
          ├─ Detect anomalies
          └─> DataInsights (JSON)

3. Merge insights
   └─> Create unified GrowthBrief
       ├─ Executive summary (2-3 sentences)
       ├─ Channel summaries (headline, wins, risks)
       ├─ Ranked action items (by priority × impact/effort)
       └─ Compound entity scores

4. Persist
   └─> Write to growth_briefs table
   └─> Populate action_queue (status=pending)
   └─> Update channel_metrics time-series
   └─> (Optional) Post to Slack webhook

5. Complete
   └─> Log cost (token usage)
   └─> Trigger notifications if anomalies detected
```

### Manual Execution (On-Demand)

```
User calls POST /api/growth/cycle (requires AUTH_TOKEN)
    │
    ├─ params: channels=["seo"], trigger="manual"
    │
    ├─> Run synchronous (no Celery) — blocks request
    │
    └─> Return GrowthBrief as JSON response (or long-poll if async)
```

---

## Database Schema

### Tables

#### `growth_briefs`
Stores each orchestrator run.

```sql
id              BIGINT PRIMARY KEY
run_date        DATE
channel         VARCHAR(50)           -- 'all', 'seo', 'product', etc.
model_used      VARCHAR(100)          -- 'claude-opus-4-6'
thinking_depth  VARCHAR(20)           -- 'shallow', 'standard', 'deep'
input_tokens    INT
output_tokens   INT
cache_read_tokens INT
brief_json      JSONB                 -- Serialized GrowthBrief
summary_text    TEXT
trigger         VARCHAR(50)           -- 'scheduled', 'manual', 'webhook'
created_at      TIMESTAMPTZ
```

**Indexes**:
- `(run_date DESC)` — Latest briefs first
- `(channel, run_date DESC)` — Per-channel historical view
- `(created_at DESC)` — Chronological audit trail

#### `action_queue`
Prioritized growth actions.

```sql
id              BIGINT PRIMARY KEY
brief_id        BIGINT FK            -- Which brief generated this
channel         VARCHAR(50)
action_type     VARCHAR(100)         -- 'new_landing_page', 'update_meta', etc.
priority        INT (1-5)            -- 1=highest
expected_impact VARCHAR(20)          -- 'high', 'medium', 'low'
effort          VARCHAR(20)          -- 'quick', 'medium', 'heavy'
description     TEXT
payload_json    JSONB                -- Structured automation params
status          VARCHAR(20)          -- 'pending', 'in_progress', 'done', 'skipped'
assigned_to     VARCHAR(255)
completed_at    TIMESTAMPTZ
created_at      TIMESTAMPTZ
```

**Indexes**:
- `(status, priority)` — Fetch top-priority pending items
- `(channel, status)` — Per-channel action views
- `(brief_id)` — Trace actions to their originating brief

#### `channel_metrics`
Time-series metrics snapshots.

```sql
id              BIGINT PRIMARY KEY
metric_date     DATE
channel         VARCHAR(50)          -- 'seo', 'ga4', 'product'
metric_name     VARCHAR(100)         -- 'clicks', 'impressions', 'ctr'
metric_value    NUMERIC(15, 4)
dimensions      JSONB                -- {"keyword": "...", "page": "..."}
source          VARCHAR(50)          -- 'gsc', 'ga4', 'supabase', 'calculated'
created_at      TIMESTAMPTZ
```

**Indexes**:
- `(metric_date DESC, channel)` — Latest metrics per channel
- `(source, metric_date DESC)` — Data source audit
- Unique constraint on `(metric_date, channel, metric_name, source, dimensions_hash)`

#### `entity_scores`
Composite scores for listings, keywords, landing pages.

```sql
id              BIGINT PRIMARY KEY
entity_type     VARCHAR(50)          -- 'listing', 'keyword', 'landing_page'
entity_id       VARCHAR(255)         -- Listing ID / keyword string / page path
score_date      DATE
composite_score NUMERIC(5, 2)        -- 0.00-100.00
signal_breakdown JSONB               -- {"seo_score": 72, "traffic_score": 45, ...}
recommendations JSONB                -- ["Fix meta", "Add FAQ", ...]
created_at      TIMESTAMPTZ
```

**Indexes**:
- `(entity_type, entity_id, score_date DESC)` — Trend per entity
- `(score_date DESC, composite_score DESC)` — Top scoring entities

---

## API & Integration

### Flask Routes (Future Implementation)

```python
@app.route("/api/growth/cycle", methods=["POST"])
def trigger_growth_cycle():
    """Trigger a growth analysis cycle."""
    channels = request.json.get("channels", ["seo", "product", "data"])
    trigger = request.json.get("trigger", "manual")

    orchestrator = create_orchestrator()
    brief = await orchestrator.run_growth_cycle(channels=channels, trigger=trigger)

    return jsonify(brief.model_dump()), 200

@app.route("/api/growth/briefs", methods=["GET"])
def list_briefs():
    """List recent growth briefs."""
    limit = request.args.get("limit", 10, type=int)
    channel = request.args.get("channel", "all")

    briefs = get_briefs(channel=channel, limit=limit)
    return jsonify([b.model_dump() for b in briefs]), 200

@app.route("/api/growth/actions", methods=["GET"])
def list_actions():
    """List pending action items."""
    status = request.args.get("status", "pending")
    priority = request.args.get("priority", None, type=int)

    actions = get_pending_actions(status=status, priority=priority)
    return jsonify([a.model_dump() for a in actions]), 200

@app.route("/api/growth/actions/<int:action_id>", methods=["PATCH"])
def update_action(action_id):
    """Update action status."""
    new_status = request.json.get("status")
    assigned_to = request.json.get("assigned_to")

    updated = update_action_status(action_id, new_status, assigned_to)
    return jsonify(updated.model_dump()), 200
```

### Claude Integration (Agent SDK)

```python
from claude_agent_sdk import AgentDefinition, query, ClaudeAgentOptions

SEO_AGENT_DEF = AgentDefinition(
    id="seo-channel",
    name="SEO Growth Agent",
    system_prompt=open("growth/prompts/seo_agent.txt").read(),
    model="claude-haiku-4-5",
    tools=["gsc_query", "ga4_query", "query_listings"],
)

async def orchestrate():
    brief = await query(
        prompt="Analyze SEO performance for last 7 days...",
        options=ClaudeAgentOptions(
            model="claude-opus-4-6",
            system_prompt=ORCHESTRATOR_PROMPT,
            agents={"seo": SEO_AGENT_DEF, ...},
            output_format=GrowthBrief.model_json_schema(),
        )
    )
```

### Slack Notifications (Future)

```python
import slack_sdk

def notify_slack_growth_brief(brief: GrowthBrief):
    client = slack_sdk.WebClient(token=SLACK_BOT_TOKEN)

    text = f"""
    📊 Growth Cycle: {brief.run_date}

    {brief.executive_summary}

    Top Actions:
    {[f"• [{a.priority}] {a.description}" for a in brief.action_items[:3]]}
    """

    client.chat_postMessage(channel="#growth", text=text)
```

---

## Configuration

### Environment Variables

```bash
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxxxx

# Google APIs
GOOGLE_SEARCH_CONSOLE_CREDENTIALS=/path/to/gsc-service-account.json
GOOGLE_ANALYTICS_PROPERTY_ID=123456789

# Celery + Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Claude API
ANTHROPIC_API_KEY=sk-xxxxx

# Slack (optional)
SLACK_BOT_TOKEN=xoxb-xxxxx
SLACK_CHANNEL=#growth
```

### Django/Flask Integration

```python
# In app/__init__.py
from growth.scheduler import celery_app

app.config["CELERY"] = celery_app

# In manage.py or main app startup
if __name__ == "__main__":
    from celery import Celery
    from growth.scheduler import celery_app as app_celery

    # Start Celery worker with beat scheduler
    app_celery.start()
```

---

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run test orchestrator cycle
python -m growth.orchestrator

# Start Celery worker + beat scheduler
celery -A growth.scheduler worker --beat --loglevel=info
```

### Production (Heroku/Fly.io)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Web dyno (Flask)
CMD gunicorn app:app

# Worker dyno (Celery)
CMD celery -A growth.scheduler worker --beat
```

### Database Migrations

```bash
# Apply growth tables
psql $DATABASE_URL < db/migrations/20260329_growth_tables.sql

# Verify
psql $DATABASE_URL -c "\dt growth_*"
```

---

## Monitoring & Maintenance

### Health Checks

```python
def check_growth_system_health():
    """Verify all integrations are accessible."""
    checks = {
        "supabase": can_query_listings(),
        "gsc": can_query_gsc(),
        "ga4": can_query_ga4(),
        "database": can_connect_postgres(),
        "redis": can_connect_redis(),
    }

    return {"healthy": all(checks.values()), "checks": checks}
```

### Metrics to Monitor

- **Orchestrator**
  - Cycle duration (should be < 5 min)
  - Token usage (input/output/cache)
  - Error rate (timeouts, API failures)

- **Database**
  - `growth_briefs` row count (1 per day + ~4 per week deep runs)
  - `action_queue` completion rate (% marked as done)
  - Query performance (use EXPLAIN ANALYZE)

- **Costs**
  - Claude API: `(input + output) × pricing`
  - External APIs: GSC/GA4 quota usage
  - Database: storage growth rate

### Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| "Agent timeout" | Subagent taking > 30s | Increase timeout, reduce data window |
| "Cache misses" | System prompt changed | Verify prompt hash, regenerate cache |
| "DB insert fails" | Unique constraint violation | Check `metric_date + source + dimensions` combo |
| "Celery tasks not running" | Redis down | Restart Redis, check broker URL |

---

## Future Enhancements

### Phase 2 (Q2 2026)
- [ ] Real-time anomaly detection (immediate Slack alerts)
- [ ] A/B testing framework (measure action impact)
- [ ] Automated action execution (e.g., update meta tags, publish landing pages)
- [ ] Cost optimization (route simple tasks to Haiku, use Batch API for bulk)

### Phase 3 (Q3 2026)
- [ ] Multi-site support (expand beyond tablerodevuelta.cl)
- [ ] Competitive intelligence (track competitor actions)
- [ ] Predictive modeling (forecast growth impact)
- [ ] Integration with product roadmap (align growth initiatives with features)

---

**Questions?** Reach out to the growth engineering team.
