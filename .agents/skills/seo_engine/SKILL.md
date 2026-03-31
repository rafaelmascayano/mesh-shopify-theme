---
name: SEO Engine
description: Motor de GEO (Generative Engine Optimization) y SEO Técnico para E-commerce Industrial. Optimiza catálogos para citaciones en IA (Gemini, Perplexity).
---

# SEO Engine Skill (V2026.03: Elite GEO)

## Contexto General
Este skill transforma catálogos técnicos (ej. FLIR) en **Fuentes de Datos Autoritarias** para Motores de Respuesta IA. Se basa en la **Regla de los Primeros 200 palabras** y la **Inyección de Schema JSON-LD** de última generación.

## Herramientas del Skill (`.agents/skills/seo_engine/scripts/`)

### 🛠️ Núcleo de Optimización
- **`product_enricher_engine.py`**: El motor principal. Usa **Gemini 2.5 Flash** para generar descripciones GEO-Ready con especificaciones densas y Schema inyectado.
- **`seo_audit_colvinycia.py`**: Auditoría masiva de salud de catálogo (Métrica 2026: >1000 caracteres, E-E-A-T Snippet, JSON-LD Schema).

### 📈 Inteligencia de Performance
- **`growth_orchestration_cycle.py`** (en `growth-orchestrator`): Une GSC + Shopify para priorizar productos con alto tráfico pero contenido pobre.
- **`ads.py`**: Exportación de datos de Google Ads (campañas, search terms, device, geo, PMax, Quality Score, Ad Copy).
- **`ads_diagnostic.py`**: **Motor de diagnóstico de campañas.** Lee los CSVs exportados por `ads.py` y genera un reporte Markdown con:
  - 🚫 Candidatos a keywords negativas (gasto sin conversión)
  - 🏆 Keywords ganadoras a expandir
  - ⚔️ Detección de canibalización entre campañas
  - 📋 Análisis de Quality Score y acciones por keyword
  - 📱 Recomendaciones de bid por dispositivo y geografía
  - ✍️ Análisis de rendimiento de ad copy (RSA)
  - 🤖 Diagnóstico de assets de Performance Max

### 🔍 Diagnóstico y Conectividad
- **`test_shopify_graphql.py`**: Validación de Admin API.
- **`debug_gsc_sites.py`**: Verificación de permisos de Search Console por propiedad.
- **`list_gemini_models.py`**: Auditoría de modelos disponibles (2.0 vs 2.5).

## Workflow Maestro (The Elite Loop)

1. **Auditoría de Salud:** Ejecutar `seo_audit_colvinycia.py` para identificar productos "Thin Content" o sin Schema.
2. **Priorización:** Ejecutar `growth_orchestration_cycle.py` para cruzar con clics reales.
3. **Diagnóstico de Ads:** Ejecutar `ads.py` → `ads_diagnostic.py` para identificar mejoras en campañas pagadas.
4. **Enriquecimiento GEO:** Lanzar `product_enricher_engine.py` con las prioridades detectadas.
5. **Inyección de Confianza:** Validar que el trust snippet de "Distribuidor Oficial" esté presente en el HTML final.

## Estándares 2026 (Refactorizados)
- **Umbral de Citación:** Mínimo 1000 caracteres de contenido técnico útil.
- **E-E-A-T Local:** Obligatoriedad de citar el rol de distribuidor oficial.
- **Schema Velocity:** Cada producto debe contener su propio objeto `<script type="application/ld+json">`.

---
**Ultima Refactorización: 31 de marzo, 2026 (Post-Audit Gemini 2.5)**
