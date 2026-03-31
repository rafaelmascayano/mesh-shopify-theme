# Scripts Reorganization Guide

**Date:** March 30, 2026
**Status:** ✅ Complete
**Purpose:** Consolidate SEO Engine scripts into their logical home

---

## What Changed

### Before
```
scripts/
├── seo_description_generator.py
├── product_faq_generator.py
├── schema_generator.py
├── seo_opportunity_detector.py
├── serp_scraper.py
├── listings_seo_audit.py
├── seo_pipeline.py
├── (+ dbmate utilities, test files)
└── (MIXED: SEO + utilities)
```

### After
```
.claude/ecommerce-seo-engine/scripts/  ← NEW HOME for SEO engine
├── __init__.py                         (exports all functions)
├── seo_description_generator.py
├── product_faq_generator.py
├── schema_generator.py
├── seo_opportunity_detector.py
├── serp_scraper.py
├── listings_seo_audit.py
├── seo_pipeline.py
└── (CLEAN: SEO only)

scripts/
├── apply_seo_descriptions.py           (UPDATED: uses new imports)
├── dbmate-*.sh                         (unchanged: utilities)
├── test_access.py                      (unchanged: utilities)
└── (CLEAN: utilities only)

growth/tools/
└── content_tools.py                    (NEW: wrapper for Growth Orchestrator)
```

---

## Why This Organization?

### 1. **Skill-Based Separation**
- SEO Engine scripts live in `.claude/ecommerce-seo-engine/` (where the SKILL.md is)
- Growth Orchestrator tools live in `growth/tools/` (where the orchestrator is)
- Utilities stay in `scripts/` (shared infrastructure)

### 2. **Import Clarity**
Instead of:
```python
from scripts.seo_description_generator import generate_seo_description
```

Now Growth Orchestrator uses:
```python
from growth.tools.content_tools import generate_listing_description
```

Which internally imports:
```python
from .claude.ecommerce-seo-engine.scripts import generate_seo_description
```

### 3. **Reusability**
- SEO scripts can be imported directly by other tools/agents
- Growth Orchestrator wraps them as tools (adds error handling, logging)
- Clear separation of concerns

---

## File Inventory

### `.claude/ecommerce-seo-engine/scripts/`

| File | Purpose | Function(s) |
|---|---|---|
| `__init__.py` | Exports all SEO functions | All public functions available via package import |
| `seo_description_generator.py` | Generate product descriptions | `generate_seo_description()` |
| `product_faq_generator.py` | Generate FAQ schema | `generate_faq()`, `generate_faq_schema()` |
| `schema_generator.py` | Generate JSON-LD markup | `build_product_schema()`, `generate_schema()` |
| `seo_opportunity_detector.py` | Find keyword clusters | `detect_category_opportunities()`, `analyze_competitor_gap()` |
| `serp_scraper.py` | SERP analysis | `scrape_serp_for_keyword()` |
| `listings_seo_audit.py` | SEO quality audit | `audit_listing_seo()` |
| `seo_pipeline.py` | Full pipeline | `run_seo_pipeline_for_listing()` |

### `growth/tools/content_tools.py`

Wrapper functions (for Growth Orchestrator):

| Function | Purpose |
|---|---|
| `generate_listing_description()` | Wraps `generate_seo_description()` |
| `generate_product_faq()` | Wraps `generate_faq()` |
| `generate_product_schema()` | Wraps `build_product_schema()` |
| `audit_listing_seo_quality()` | Wraps `audit_listing_seo()` |
| `find_seo_opportunities()` | Wraps `detect_category_opportunities()` |
| `analyze_serp()` | Wraps `scrape_serp_for_keyword()` |
| `run_full_seo_pipeline()` | Wraps `run_seo_pipeline_for_listing()` |

### `scripts/apply_seo_descriptions.py`

**Updated** to use new import structure:
```python
from growth.tools.content_tools import generate_listing_description
```

---

## How to Use

### As an SEO Engineer (Direct Use)
```python
from .claude.ecommerce_seo_engine.scripts import (
    generate_seo_description,
    detect_category_opportunities,
)

listing = {"title": "Catan", "players_min": 3, "players_max": 4}
description = generate_seo_description(listing)
```

### As Growth Orchestrator (Tool Use)
```python
from growth.tools.content_tools import generate_listing_description

result = generate_listing_description(listing)
# Returns: {status, listing_id, description, char_count}
```

### From Command Line
```bash
# Old way (deprecated)
# python scripts/apply_seo_descriptions.py

# New way (updated)
python scripts/apply_seo_descriptions.py
# (Now uses growth.tools.content_tools internally)
```

---

## Migration Checklist

- [x] Copy scripts to `.claude/ecommerce-seo-engine/scripts/`
- [x] Create `__init__.py` with exports
- [x] Create `growth/tools/content_tools.py` wrapper
- [x] Update `scripts/apply_seo_descriptions.py` imports
- [x] Add error handling in wrapper
- [x] Update logging/documentation
- [ ] Test end-to-end (content_tools → SEO engine)
- [ ] Remove old scripts from `scripts/` (keep backup in git history)
- [ ] Update any other imports (if any)

---

## Testing

### Verify SEO Engine Still Works
```bash
cd /Users/rafaelmascayano/git/tablerodevuelta

# Test direct import
python -c "from .claude.ecommerce_seo_engine.scripts import generate_seo_description; print('✓ Direct import works')"

# Test wrapper import
python -c "from growth.tools.content_tools import generate_listing_description; print('✓ Wrapper import works')"

# Test full script
python scripts/apply_seo_descriptions.py
```

### Verify Growth Orchestrator Can Call SEO Tools
```python
from growth.tools.content_tools import generate_listing_description

listing = {
    "id": 1,
    "title": "Pandemic",
    "players_min": 2,
    "players_max": 4,
}

result = generate_listing_description(listing)
print(result)
# Expected: {status: "success", description: "...", char_count: ...}
```

---

## Benefits of This Organization

✅ **Clarity:** Each skill has its own directory under `.claude/`
✅ **Reusability:** SEO scripts can be called by any tool/agent
✅ **Maintainability:** Changes to SEO scripts don't affect utilities
✅ **Scalability:** Easy to add more skills (paid-agent-tools, email-agent-tools, etc.)
✅ **Auditability:** Git history shows why scripts moved
✅ **Documentation:** SKILL.md + REORGANIZATION.md explain everything

---

## Future: Additional Skills

When adding Paid/Email/Analytics tools:

```
.claude/
├── ecommerce-seo-engine/        ✅ Exists
│   └── scripts/
├── growth-orchestrator/         ✅ Exists
├── paid-agent-tools/            ⏳ Future
│   └── scripts/
├── email-agent-tools/           ⏳ Future
│   └── scripts/
└── README.md                    ✅ Exists (unified reference)

growth/tools/
├── content_tools.py             ✅ Exists (SEO wrapper)
├── paid_tools.py                ⏳ Future (Paid wrapper)
├── email_tools.py               ⏳ Future (Email wrapper)
└── analytics_tools.py           ✅ Exists (GSC, GA4)
```

---

## Questions?

- **Why not just keep scripts in `scripts/`?** Because SEO is one of potentially 5 growth channels. Consolidating by skill (not by purpose) makes it clearer which tools belong to which agent.

- **Can I import from `.claude/` directly?** Yes! Both direct import and wrapper import work. Use wrapper if you want error handling + logging.

- **Will this break existing integrations?** No. `scripts/apply_seo_descriptions.py` still works, just uses the new import path internally.

- **How do I add more functions to the SEO engine?** Add them to `.claude/ecommerce-seo-engine/scripts/`, then export from `__init__.py`, then wrap in `content_tools.py` if needed.

---

**Updated:** March 30, 2026
**Maintained by:** Growth Engineering Team
