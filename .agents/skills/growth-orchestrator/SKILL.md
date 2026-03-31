---
name: growth-orchestrator
description: Multi-channel growth automation orchestrator. Analyzes SEO, product, paid, email, and data to generate unified growth strategy with prioritized action items.
---

# Growth Orchestrator Skill

This skill enables Claude to operate as a **senior growth engineer** coordinating multi-channel growth strategy for tablerodevuelta.cl.

## Primary Use Cases

- Generate nightly growth analysis cycles (SEO + Product + Data insights)
- Identify quick-win opportunities across channels
- Detect anomalies and risks in growth metrics
- Recommend prioritized actions (ranked by impact × effort)
- Generate compound entity scores (listings, keywords, landing pages)

## Input Format

Claude receives:
- Time period for analysis (e.g., "last 7 days", "this month")
- Channels to analyze: 'seo', 'paid', 'product', 'email', 'data'
- Optional trigger type: 'scheduled', 'webhook', 'manual'

## Output Format

Structured **GrowthBrief** containing:

```json
{
  "run_date": "2026-03-29",
  "channels_analyzed": ["seo", "product", "data"],
  "executive_summary": "Strong SEO momentum (↑18% clicks YoY) but product funnel has 12% conversion drop. Recommend: (1) fix listing quality issues, (2) target long-tail keywords.",
  "channel_summaries": [
    {
      "channel": "seo",
      "headline": "Strong SERP progress; opportunity in long-tail clusters",
      "top_win": "Programmatic landing pages for 'juegos [category] para [player_count]' cluster",
      "top_risk": "Ranking drops in competitive category pages (-3 avg position)",
      "metrics_snapshot": {
        "monthly_clicks": 3200,
        "monthly_impressions": 45000,
        "avg_position": 4.2,
        "ctr": 0.071
      }
    },
    {
      "channel": "product",
      "headline": "Conversion rate declining; inventory quality issues",
      "top_win": "Enforce minimum 3 photos per listing (reduce inquiry-to-contact dropoff)",
      "top_risk": "12% monthly decline in contacts-per-listing-view",
      "metrics_snapshot": {
        "dau": 850,
        "conversion_rate": 0.018,
        "avg_session_length": "2m34s"
      }
    }
  ],
  "action_items": [
    {
      "channel": "product",
      "action_type": "enforce_listing_quality",
      "priority": 1,
      "expected_impact": "high",
      "effort": "quick",
      "description": "Add validation: listings require minimum 3 photos and 100+ character description. Warn sellers before publish.",
      "payload": {
        "min_photos": 3,
        "min_description_chars": 100,
        "enforcement": "soft_warn"
      }
    },
    {
      "channel": "seo",
      "action_type": "new_programmatic_landing_pages",
      "priority": 2,
      "expected_impact": "high",
      "effort": "medium",
      "description": "Generate 24 landing pages for ['juegos cooperativos', 'juegos estrategia', ...] + [2, 3, 4, 5+] players. Target 500+ monthly searches.",
      "payload": {
        "template": "category_player_cluster",
        "keywords": [...],
        "estimated_pages": 24
      }
    }
  ],
  "compound_scores": {
    "listing:12345": 72.5,
    "keyword:juegos cooperativos": 81.0,
    "page:/categoria/cooperativos": 68.5
  }
}
```

## Data Sources

The orchestrator accesses:

| Source | Purpose | Credentials |
|---|---|---|
| Supabase | Listings, users, conversations | DATABASE_URL |
| GSC service account | Search clicks, impressions, rankings | GSC service account |
| Google Analytics 4 | Traffic, funnel, user behavior | GA4 property ID |
| SEO Engine Scripts | Shopify + GSC Priority Matrix | `.agents/skills/seo_engine/scripts/` |
| Orchestration Script | Core Priority Logic | `.agents/skills/growth-orchestrator/scripts/growth_orchestration_cycle.py` |

## Integration Points

**Subagents (Claude Agent SDK)**
- SEO Agent: Analyzes GSC data, identifies keyword opportunities, generates content recommendations
- Product Agent: Analyzes GA4 funnel, user engagement, retention metrics
- Data Agent: Aggregates cross-channel metrics, detects anomalies

**Tools (@beta_tool pattern)**
- `gsc_query`: Search Console performance data
- `ga4_query`: Traffic and funnel metrics
- `query_listings`: Product inventory analysis
- `write_action_queue`: Persist action items to database

**Scheduling**
- Runs nightly at 23:00 UTC via Celery + Redis
- Ad-hoc runs via manual API call
- Persists GrowthBrief to `growth_briefs` table
- Populates `action_queue` for team execution

## Key Behaviors

### 1. Multi-Channel Orchestration
- Does NOT reinvent SEO analysis — leverages `.claude/ecommerce-seo-engine/` scripts
- Coordinates insights across SEO, Product, Paid, Email, Data into unified strategy
- Detects cross-channel patterns (SEO wins → product conversion uptick?)

### 2. Data-Driven Recommendations
- All insights backed by metrics (GSC clicks, GA4 sessions, listing count)
- Quantifies impact (e.g., "estimated 15% CTR improvement from meta refresh")
- Explicitly calls out confidence levels and data limitations

### 3. Prioritization Framework
- Priority = 1 (highest) to 5 (lowest)
- Expected Impact: high / medium / low
- Effort: quick (< 1 day) / medium (< 1 week) / heavy (> 1 week)
- Orders by: impact × (1 / effort)

### 4. Marketplace Context Always Included
- Understands board game market dynamics
- Recognizes seasonal patterns (holiday buying, gift season)
- Tailored for Chilean Spanish language and P2P marketplace mechanics

## Example Workflow

**Nightly Cycle (23:00 UTC)**
```
Celery beat triggers orchestrator.run_growth_cycle()
    ↓
Orchestrator loads 7-day snapshots from GSC, GA4, Supabase
    ↓
Spawns 3 subagents in parallel (SEO, Product, Data)
    ↓
Each subagent analyzes their channel, returns structured insights
    ↓
Root orchestrator merges insights into GrowthBrief
    ↓
Ranks 8-15 action items by priority
    ↓
Writes brief to growth_briefs table
    ↓
Populates action_queue table (status=pending)
    ↓
(Optional) Posts summary to Slack #growth channel
```

**Manual Execution (Debugging)**
```
curl -X POST https://api.tablerodevuelta.cl/growth/cycle \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -d '{"trigger": "manual", "channels": ["seo"]}'
    ↓
Returns GrowthBrief JSON immediately
```

## Configuration

Place environment variables in `.env`:
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx
GOOGLE_SEARCH_CONSOLE_CREDENTIALS=path/to/gsc-service-account.json
GOOGLE_ANALYTICS_PROPERTY_ID=123456789
CELERY_BROKER_URL=redis://localhost:6379/0
```

## Testing & Validation

Run a test cycle:
```bash
python -m growth.orchestrator
```

Expected output:
```
🚀 Starting growth cycle (trigger: test)
📊 Analyzing channels: seo, product, data
✅ Brief generated with 8 action items
💾 Brief saved: {id: 1, created_at: ...}
📋 Action queue written (8 items)

{
  "run_date": "2026-03-29",
  "channels_analyzed": ["seo", "product", "data"],
  ...
}
```

## Limitations & Future Work

**Current (MVP)**
- ✅ Framework and architecture (schemas, tools, agents)
- ✅ Pydantic structured output validation
- ✅ Database persistence (4 tables + indexes)
- ⏳ Subagent orchestration (requires Claude Agent SDK beta access)
- ⏳ Real data integration (GSC, GA4 API clients)
- ⏳ Celery scheduler (requires Redis)

**Next Phase**
- AI-powered entity scoring (composite signals)
- Real-time anomaly detection (Slack alerts)
- Cost optimization tracking (Opus 4.6 → Haiku for simple classification)
- A/B testing framework (measure impact of actions)

## Documentation Files

- `GROWTH_SYSTEM.md` — Full technical deep-dive
- `growth/orchestrator.py` — Main entry point
- `growth/schemas/` — Pydantic models (brief, insights, scores)
- `db/migrations/20260329_growth_tables.sql` — Database schema

