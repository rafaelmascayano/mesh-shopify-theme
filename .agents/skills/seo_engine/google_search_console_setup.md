# Google Search Console Setup - Tablero de Vuelta

## Overview

Google Search Console (GSC) es herramienta CRÍTICA para monitorear y optimizar presencia en búsquedas.

**Time to complete:** 30-45 minutos
**Benefit:** Acceso a datos de búsqueda, indexación, y errores

---

## Step 1: Verificar Propiedad del Dominio

### Opción A: Verificación con DNS (Recomendada)

1. Ve a: https://search.google.com/search-console/
2. Selecciona **"Agregar propiedad"**
3. Ingresa: `https://tablerodevuelta.cl`
4. Selecciona **"Verificación de DNS"**
5. Google te dará un record DNS:
   ```
   TXT record name:  tablerodevuelta.cl
   TXT record value: google-site-verification=XXXXXXXXXXXXXX
   ```
6. Agrega este record en tu proveedor DNS (Namecheap, GoDaddy, etc.)
7. Espera 24-48 horas para que DNS se propague
8. Haz clic en "Verificar" en GSC

### Opción B: Verificación con archivo HTML

1. En GSC, selecciona "Archivo HTML"
2. Descarga el archivo HTML
3. Coloca en: `/static/` o raíz del servidor
4. Verifica en GSC

---

## Step 2: Enviar Sitemap

### Enviar sitemap.xml:

1. En GSC, ve a **Sitemaps**
2. Ingresa: `https://tablerodevuelta.cl/sitemap.xml`
3. Haz clic en "Enviar"

**Nota:** Asegúrate que `/sitemap.xml` esté accesible:

```python
# En main.py ya existe:
@main_bp.get("/sitemap.xml")
def sitemap_xml():
    # Genera sitemap dinámico
```

**Sitemap actual debe incluir:**
- ✓ Homepage
- ✓ Listings index
- ✓ Individual listings (24)
- ✓ Category pages (5)
- ✓ Player cluster pages (4)
- ✓ Guide pages (3)
- **Total: 40+ URLs**

---

## Step 3: Monitorear Errores de Crawl

En GSC, ve a **"Cobertura"** para ver:

- **Página indexada y sin errores:** Ideal
- **Excluida:** Si está bloqueada por robots.txt
- **Error:** Si Google no pudo acceder

**Acciones esperadas:**

✓ Todas las páginas de guías deben estar "Indexada"
✓ `/auth/*` debe estar "Excluida" (por robots.txt)
✓ `/admin/*` debe estar "Excluida"

---

## Step 4: Monitorear Posiciones en Búsqueda

En GSC, ve a **"Rendimiento"** para ver:

- **Consultas:** Keywords que generan clics
- **Páginas:** Qué URLs tienen más tráfico
- **Posición promedio:** Tu ranking en SERP

**Qué buscar después del launch TIER 2-3:**

```
Semana 1-2:
  • Esperado: Sin datos o datos mínimos
  • Normal: Google aún está crawleando

Semana 2-4:
  • Esperado: Primeras posiciones (30-100) para keywords largos
  • Buscar: "juegos de mesa", "juegos cooperativos", "estrategia"

Semana 4-8:
  • Esperado: Mejora de posiciones
  • Meta: Top 20 para keywords principales

Mes 3+:
  • Esperado: Crecimiento consistente
  • Objetivo: Top 10 para "juegos de mesa" + variaciones
```

---

## Step 5: Configurar Rastreo (Crawl)

### Presupuesto de Crawl

Google asigna un "presupuesto de crawl" (cuántas páginas visita por día).

**Para mejorar presupuesto:**

1. **Reducir errores 4xx/5xx**
   - Revisa logs de servidor
   - Soluciona enlaces rotos

2. **Usar robots.txt inteligente**
   ```
   # app/robots.txt ya configurado:
   User-agent: *
   Allow: /
   Disallow: /auth/
   Disallow: /admin/
   Disallow: /health/
   Sitemap: https://tablerodevuelta.cl/sitemap.xml
   ```

3. **Reducir redirects**
   - Evita cadenas de redirects
   - Usa redirects 301 permanentes

---

## Step 6: Enviar URLs Manualmente

Si necesitas indexación rápida de nuevas páginas:

1. En GSC, usa **"Inspección de URL"**
2. Ingresa URL: `https://tablerodevuelta.cl/guides/como-elegir-juego-de-mesa`
3. Haz clic en **"Solicitar indexación"**

**Google indexará en 24-48 horas (generalmente más rápido).**

---

## Step 7: Monitorear Experiencia de Página

En GSC, ve a **"Experiencia de página"** para ver:

- **LCP (Largest Contentful Paint):** Velocidad de carga
- **FID (First Input Delay):** Responsividad
- **CLS (Cumulative Layout Shift):** Estabilidad visual

**Objetivos:**
- LCP: < 2.5s
- FID: < 100ms
- CLS: < 0.1

**Si hay problemas, revisa:**
- Imágenes sin optimizar
- Scripts third-party (GA4)
- CSS/JS no minificados

---

## Step 8: Security & Manual Actions

En GSC, ve a **"Seguridad y acciones manuales"** para:

- ✓ Asegurar no hay malware detectado
- ✓ Confirmar sin acciones manuales por spam
- ✓ Verificar SSL certificado válido

**Esperado:** "No hay problemas de seguridad"

---

## Post-Launch Checklist

### Inmediatamente después de deploy:

- [ ] Verificar propiedad en GSC
- [ ] Enviar sitemap.xml
- [ ] Inspeccionar homepage
- [ ] Solicitar indexación de guías (3 URLs)
- [ ] Revisar robots.txt
- [ ] Verificar SSL certificado

### Después de 1 semana:

- [ ] Revisar "Cobertura" (erroresy exclusiones)
- [ ] Monitorear "Rendimiento" para primeros datos
- [ ] Revisar "Experiencia de página"
- [ ] Solucionar errores 4xx si los hay

### Después de 4 semanas:

- [ ] Analizar top keywords en "Rendimiento"
- [ ] Optimizar meta descriptions si CTR baja
- [ ] Identificar paginas sin tráfico para mejorar
- [ ] Planificar TIER 4

---

## Integración con GA4

Conecta GSC con Google Analytics:

1. En GSC, ve a **"Ajustes"**
2. En **"Propiedad vinculada"**, selecciona tu GA4
3. En GA4, ve a **"Fuentes de tráfico"** para ver búsqueda orgánica

Esto te permite trackear:
- Desde qué keywords vienes
- A qué página te diriges
- Qué haces después (conversiones)

---

## Keywords para Monitorear

**Tier 1 (Principales):**
- juegos de mesa
- juegos de mesa chile
- comprar juegos de mesa

**Tier 2 (Categoría):**
- juegos cooperativos
- juegos estrategia
- juegos familiares
- juegos party
- juegos cartas

**Tier 3 (Long-tail):**
- como elegir juego de mesa
- mejores juegos cooperativos
- juegos para parejas
- juegos para 2 jugadores
- pandemia juego comprar

**Tier 4 (Branded):**
- tablero de vuelta
- tablerodevuelta.cl

---

## Timeline Esperado

```
Semana 0:     Deploy + GSC verificación
Semana 1-2:   Google crawlea nuevas páginas
Semana 2-4:   Primeros rankings para long-tail keywords
Semana 4-8:   Mejora a posiciones 20-50 para Tier 2
Semana 8-12:  Posiciones 10-30 para keywords principales
Mes 3+:       Crecimiento continuo y estabilización
```

---

## Common Issues & Fixes

### "Página descubierta actualmente sin indexación"

**Causa:** Google la vio pero aún no indexada
**Solución:** Espera 1-2 semanas o solicita indexación

### "Excluida por robots.txt"

**Esperado para:** `/auth/*`, `/admin/*`, `/profile/edit`
**Inesperado para:** Páginas de guías, categorías, clusters
**Solución:** Revisa robots.txt y corrige

### "Error: 404 Not Found"

**Significa:** URL devuelve 404
**Solución:** Verifica enlace, corrige redirección, o espera a que se crawlee de nuevo

### "Bajo CTR en Rendimiento"

**Significa:** Muchas impresiones pero pocos clics
**Solución:** Mejora meta descriptions para ser más atractivas

---

## Useful Links

- [GSC Help Center](https://support.google.com/webmasters)
- [Search Console Academy](https://www.youtube.com/playlist?list=PLKoqnSL3XzuuVyMM7fG1XL-VhMFaVVLbA)
- [Mobile Friendly Test](https://search.google.com/test/mobile-friendly)
- [PageSpeed Insights](https://pagespeed.web.dev/)

---

**Next:** Implementar TIER 4 - City-based landing pages + Advanced filtering + Email marketing setup
