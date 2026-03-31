import requests
import csv
import os
import time
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ---------------------------------------------------------
# CONFIGURACIÓN (V2026.03 - ELITE GEO)
# ---------------------------------------------------------
# Rutas dinámicas para ejecución desde Skill o Root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Cargar .env buscando en carpetas superiores si es necesario
search_paths = [
    os.path.join(SCRIPT_DIR, ".env"),
    os.path.join(SCRIPT_DIR, "../../.env"),
    os.path.join(SCRIPT_DIR, "../../../.env"),
    os.path.join(SCRIPT_DIR, "../../../scripts/.env")
]
for p in search_paths:
    if os.path.exists(p):
        load_dotenv(p)
        break

# Shopify
raw_shop = os.getenv("SHOPIFY_STORE", "colvinycia")
SHOP = f"{raw_shop.split('.')[0]}.myshopify.com" if "." in raw_shop else f"{raw_shop}.myshopify.com"
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
HEADERS = {"X-Shopify-Access-Token": ACCESS_TOKEN, "Content-Type": "application/json"}

# Gemini (Versión 2.5 Flash - Estándar Q1 2026)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------------------------------------
# PROMPT LOGIC (GEO & Schema Injection)
# ---------------------------------------------------------
SYSTEM_PROMPT = """
Eres el Consultor Senior de GEO (Generative Engine Optimization) para Colvin y Cía.
Tu misión es generar descripciones técnicas de productos FLIR que sean CITADAS por agentes de IA.

REGLAS DE ORO 2026:
1. REGLA DE LOS PRIMEROS 200: Los primeros 2 párrafos deben contener las entidades técnicas clave (resolución, precisión, rango, uso) de forma directa.
2. ENRIQUECIMIENTO DE ENTIDADES: No digas "es una gran cámara", di "Cámara termográfica de resolución 160x120 con sensibilidad térmica <70mK".
3. E-E-A-T (AUTORIDAD): Inserta el Trust Snippet: "Como distribuidores oficiales FLIR en Chile, garantizamos productos originales, calibración certificada y soporte técnico especializado."
4. SCHEMA JSON-LD: Al final del HTML, incluye un bloque <script type="application/ld+json"> con el esquema de Producto (Product Schema) dinámico basado en el título y marca.
5. FORMATO: HTML semántico (<p>, <strong>, <ul>, <li>). Sin emojis.
"""

def generate_geo_description(title, vendor="FLIR"):
    prompt = f"Producto: {title}\nMarca: {vendor}\n\nGenera una descripción técnica enriquecida para SEO de IA (GEO)."
    
    try:
        # Usamos el modelo 2.5 Flash - el más eficiente para volumen en 2026
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
        )
        return response.text
    except Exception as e:
        print(f"❌ Error Gemini: {e}")
        return None

def update_shopify_product(product_id, new_html):
    url = f"https://{SHOP}/admin/api/2025-01/graphql.json"
    mutation = """
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        product { id title }
        userErrors { field message }
      }
    }
    """
    variables = {"input": {"id": product_id, "descriptionHtml": new_html}}
    resp = requests.post(url, json={"query": mutation, "variables": variables}, headers=HEADERS)
    return resp.json()

def run_enrichment_cycle(limit=1):
    input_file = os.path.join(SCRIPT_DIR, '../../../../shopify_seo_audit.csv')
    if not os.path.exists(input_file):
        # Intento fallback
        input_file = 'shopify_seo_audit.csv'
    
    if not os.path.exists(input_file):
        print("❌ Error: No se encontró shopify_seo_audit.csv. Corre la auditoría primero.")
        return

    print(f"🚀 Iniciando Enriquecimiento GEO 2026 (Limite: {limit})...")
    
    count = 0
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if count >= limit: break
            
            # CRITERIO 2026: Si < 1000 chars o sin snippet
            if int(row.get('desc_len', 0)) < 1000 or row.get('distributor_snippet') == '0':
                print(f"\n🔄 ({count+1}/{limit}) Enriqueciendo: {row['title']}")
                
                new_html = generate_geo_description(row['title'], row.get('vendor', 'FLIR'))
                
                if new_html:
                    res = update_shopify_product(row['id'], new_html)
                    errs = res.get('data', {}).get('productUpdate', {}).get('userErrors')
                    if not errs:
                        print(f"✅ Actualizado éxito.")
                        count += 1
                    else:
                        print(f"❌ Error: {errs}")
                
                time.sleep(3) # Rate limit protection

if __name__ == "__main__":
    run_enrichment_cycle(limit=1)
