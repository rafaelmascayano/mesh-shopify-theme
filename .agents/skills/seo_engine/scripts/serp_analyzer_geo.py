import os
import requests
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ---------------------------------------------------------
# CONFIGURACIÓN (V2026.03 - RECURSIVE SCAN)
# ---------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_env_recursive():
    curr = SCRIPT_DIR
    while curr != os.path.dirname(curr): # Till root /
        p = os.path.join(curr, ".env")
        if os.path.exists(p):
            load_dotenv(p)
            print(f"✅ .env cargado desde: {p}")
            return True
        curr = os.path.dirname(curr)
    return False

load_env_recursive()

# Gemini (V2.5 Flash - Estándar 2026)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------------------------------------
# GEO SERP ANALYZER
# ---------------------------------------------------------
SYSTEM_PROMPT = """
Eres un Analista de Mercado y Experto en GEO (Generative Engine Optimization).
Tu tarea es analizar los resultados de búsqueda (SERP) para detectar OPORTUNIDADES de Citación por IA.

Dada una lista de resultados de búsqueda para una keyword:
1. Identifica el INTENTO (Informacional, Transaccional, Comparativo).
2. Detecta la "Brecha Semántica" (¿Qué falta en los resultados actuales?).
3. Evalúa el potencial de "AI Snapshot" (¿Este término genera resúmenes de IA?).
4. Recomienda una estrategia de contenido (FAQ, Estructura, Entidades).
"""

def analyze_serp_geo(keyword, search_results_mock=None):
    # En un entorno real, aquí se consultaría SerpApi o similar.
    # Por ahora simulamos la recolección de los Top 3 para Colvin y Cía.
    
    context = f"Keyword: {keyword}\n\nTop 3 Resultados Simulados:\n1. Colvin y Cía - Distribuidor Oficial FLIR Chile\n2. FLIR Support - Soporte Oficial\n3. Amazon - Cámaras Térmicas Baratas\n"
    
    if search_results_mock:
        context = f"Keyword: {keyword}\n\nResultados Reales:\n{search_results_mock}"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=context,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
        )
        return response.text
    except Exception as e:
        print(f"❌ Error Gemini Intel: {e}")
        return None

def run_trend_scan():
    # Keywords de Alta Intención para Colvin y Cía
    KEYWORDS = [
        "cámaras termográficas FLIR Chile",
        "precio FLIR C5 Chile",
        "mejor cámara térmica para mantenimiento predictivo",
        "FLIR A-Series automatización"
    ]
    
    print(f"🚀 Escaneando Tendencias y SERP GEO 2026 para {len(KEYWORDS)} keywords...")
    
    report_file = os.path.join(SCRIPT_DIR, "../../../../keyword_market_intel.md")
    
    full_report = "# 📊 Reporte de Inteligencia de Mercado (Elite GEO 2026)\n\n"
    
    for kw in KEYWORDS:
        print(f"\n🔍 Analizando: {kw}")
        intel = analyze_serp_geo(kw)
        if intel:
            full_report += f"## Keyword: {kw}\n\n{intel}\n\n---\n"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(full_report)
        
    print(f"\n✅ Reporte de Inteligencia generado: {report_file}")

if __name__ == "__main__":
    run_trend_scan()
