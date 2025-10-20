# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Shopify theme for Colvin y Cia (colvinycia.cl), a Chilean B2B/B2C e-commerce store. The theme is based on "Warehouse" theme v6.6.0 by Maestrooo, with the "Mesh" preset currently active. The store includes custom RMA (Return Merchandise Authorization) management functionality and B2B customer access controls.

## Theme Architecture

### Core Structure

This is a standard Shopify 2.0 theme with the following directory structure:

- **assets/** - JavaScript, CSS, images, and third-party libraries (Chart.js, Plotly, SweetAlert2, jQuery, etc.)
- **config/** - Theme settings schema and settings data
- **layout/** - Base template (theme.liquid)
- **locales/** - Multi-language translations (Spanish primary, with EN, FR, DE, IT, PT-BR, JA, NB, TR)
- **sections/** - Reusable theme sections (~55 sections)
- **snippets/** - Reusable template components (~45 snippets)
- **templates/** - Page templates (products, collections, pages, etc.)

### Key Technologies

- **Liquid** - Shopify's templating language
- **Vanilla JavaScript** - Custom functionality in assets/custom.js and theme.js
- **jQuery 3.5.1 & 3.6.0** - Loaded for compatibility (both versions present)
- **Chart.js** - Data visualization for RMA dashboards
- **Plotly.js** - Advanced charting (funnel charts)
- **SweetAlert2** - Modern alert/modal dialogs
- **Grid.js** - Data table rendering
- **SortableJS** - Drag-and-drop for Kanban boards
- **QRCode.js** - QR code generation

### Third-Party Apps Integration

**BSS B2B Lock/Login** - Customer access control system that locks content based on:
- Customer tags
- Login status
- Age verification
- IP addresses
- Custom passcodes

Look for snippets prefixed with `bss-lock-` and includes in templates like `{% include 'bss-lock' %}`.

**Request a Quote (SAR)** - Quote request functionality embedded in theme.

## Custom RMA System

The store has a sophisticated custom RMA management system with dedicated templates and snippets:

### RMA Templates
- `templates/page.todas-rma.liquid` - Admin-only view showing all RMAs (requires 'admin' customer tag)
- `templates/page.mis-rma.liquid` - Customer view of their own RMAs
- `templates/page.creacion-rma.liquid` - RMA creation form
- `templates/page.creacion-rma-para-cliente.liquid` - Admin-initiated RMA creation for customers

### RMA Components (snippets/)
- `css-todas-rma.liquid` - Styling for RMA admin interface
- `filtros-todas-rma.liquid` - Filter UI components
- `js-filtros-todas-rma.liquid` - Filter logic
- `graficos-todas-rma.liquid` - Chart containers
- `js-graficos-todas-rma.liquid` - Chart rendering and data visualization
- `js-kanban-todas-rma.liquid` - Kanban board for lab/workshop tracking

### RMA Features
- **Multi-tab interface**: List view, Kanban board, Dashboard with charts
- **Role-based access**: Admin-only sections protected by customer tag verification
- **Data visualization**: Charts for RMA status tracking, trends, and analytics
- **QR code generation**: For RMA tracking labels

## Development Guidelines

### Working with Liquid Templates

When editing templates, be aware of:

1. **BSS Lock integration** - Many templates include `{% include 'bss-lock' %}` at the top. Don't remove these unless explicitly requested.

2. **Custom JavaScript events** - The theme uses custom events for cart and variant changes:
   - `variant:changed` - Fired when product variant changes
   - `product:added` - Fired when product added to cart
   - `cart:refresh` - Fired to force cart UI refresh

3. **Global theme variables** - Exposed in theme.liquid (lines 56-96):
   - `window.theme` - Settings, cart count, money formats
   - `window.routes` - Shopify route URLs
   - `window.languages` - Translated strings for JS use

### Modifying Styles

The theme uses:
- `theme.css` - Main compiled stylesheet
- CSS variables defined in `snippets/css-variables.liquid`
- Inline styles in custom RMA components

Color scheme is controlled via `config/settings_schema.json` (Colors section) and can be customized in the Shopify theme editor.

### Adding or Modifying Sections

Sections follow Shopify 2.0 schema format. Each section includes:
- Liquid markup
- Schema definition with settings
- Optional presets

Common sections include: header, footer, announcement-bar, featured-product, collection-list, etc.

### Industry-Specific Templates

The store serves multiple industries with dedicated page templates:
- `page.mineria-info.json` - Mining
- `page.energia-info.json` - Energy
- `page.sectormaritimo-info.json` - Maritime
- `page.forestal.json` - Forestry
- `page.defensaseguridad-info.json` - Defense/Security
- `page.smartcities-info.json` - Smart Cities
- `page.automatizacion-industrial.json` - Industrial Automation
- `page.edificios-inteligentes.json` - Smart Buildings

### B2B Features

- `templates/search.bss.b2b.liquid` - B2B customer search
- `templates/search.bss.login.liquid` - Login-restricted search
- `templates/page.portal-b2b.json` - B2B customer portal
- Customer tag-based content restrictions throughout

## Version Control

Current git branch: `main`

Recent commits focus on:
- Tax handling updates
- Price rule configurations (0 price rule)
- Search and recently viewed item rules (>5M)
- Version updates

When committing, follow existing commit message style (lowercase, concise, action-oriented).

## Important Notes

- The theme loads both jQuery 3.5.1 and 3.6.0 (lines 152-155 in theme.liquid) - this is unusual but may be for compatibility with different apps
- Multi-language support is available but Spanish (`locales/es.json`) is the primary language
- The RMA system is custom-built and not part of any standard Shopify app
- Customer tags control access to many features - always verify tag requirements when working with restricted content
- The theme uses Shopify's section groups (header-group, footer-group, overlay-group) introduced in Shopify 2.0


{"idx":1,"id":400,"order_id":262,"shopify_line_item_id":"shipping-6808731812078","sku":"ENVIO","part_number":"ENVIO","quantity":1,"product_title":"Envío Chilexpress","variant_title":null,"created_at":"2025-10-13 17:02:01.845926+00","price":16807,"shopify_variant_id":null,"usd_price_at_order":null,"is_shipping_line":true}