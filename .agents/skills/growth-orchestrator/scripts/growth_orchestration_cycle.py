import pandas as pd
import requests
import os
import json
from datetime import date, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

# ---------------------------------------------------------
# CONFIGURACIÓN (Best Practice 2026)
# ---------------------------------------------------------
load_dotenv()

# Google Search Console
SITE_URL = os.getenv("GSC_SITE_URL", "sc-domain:colvinycia.cl") 
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

# Rutas dinámicas basadas en la ubicación del script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Google Search Console (Busca en el mismo directorio)
GSC_FILE = os.path.join(SCRIPT_DIR, "gsc-service-account.json")

# Shopify
SHOP = os.getenv("SHOPIFY_STORE", "colvinycia.myshopify.com")
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
COLLECTION_ID = os.getenv("COLLECTION_ID", "gid://shopify/Collection/434227314926")

def fetch_gsc_performance():
    """Obtiene rendimiento orgánico de los últimos 28 días."""
    print(f"📊 Extrayendo datos de GSC para: {SITE_URL}")
    
    # Intento de encontrar el archivo en la carpeta del skill o raíz de scripts
    search_paths = [
        GSC_FILE,
        os.path.join(SCRIPT_DIR, "../../../scripts/gsc-service-account.json"),
        os.path.join(SCRIPT_DIR, "../../seo_engine/scripts/gsc-service-account.json")
    ]
    
    final_gsc_path = None
    for p in search_paths:
        if os.path.exists(p):
            final_gsc_path = p
            break

    if not final_gsc_path:
        print(f"❌ Error: gsc-service-account.json no encontrado en {search_paths}")
        return pd.DataFrame()

    creds = service_account.Credentials.from_service_account_file(final_gsc_path, scopes=SCOPES)
    service = build("searchconsole", "v1", credentials=creds)
    
    end_date = date.today()
    start_date = end_date - timedelta(days=28)
    
    request = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["page"],
        "rowLimit": 5000,
    }
    
    try:
        response = service.searchanalytics().query(siteUrl=SITE_URL, body=request).execute()
        rows = response.get("rows", [])
        if not rows: return pd.DataFrame()
        
        data = [{
            "url": r["keys"][0],
            "clicks": r["clicks"],
            "impressions": r["impressions"],
            "ctr": r["ctr"],
            "avg_position": r["position"]
        } for r in rows]
        
        return pd.DataFrame(data)
    except Exception as e:
        print(f"❌ Error GSC: {e}")
        return pd.DataFrame()

def fetch_shopify_catalog():
    """Importa lógica de auditoría."""
    import sys
    # Añadimos las rutas de los otros scripts al path para permitir la importación
    sys.path.append(os.path.join(SCRIPT_DIR, "../../seo_engine/scripts"))
    sys.path.append(os.path.join(SCRIPT_DIR, "../../../scripts"))
    
    try:
        from seo_audit_colvinycia import get_products
        products = get_products(COLLECTION_ID)
        if not products: return pd.DataFrame()
        return pd.DataFrame(products)
    except ImportError as e:
        print(f"❌ Error al importar seo_audit_colvinycia: {e}")
        return pd.DataFrame()

def run_growth_cycle():
    print("🚀 Iniciando Ciclo de Orquestación de Crecimiento (V2026.02)")
    
    # 1. Obtener Rendimiento
    gsc_df = fetch_gsc_performance()
    
    # 2. Obtener Auditoría de Contenido
    shopify_df = fetch_shopify_catalog()
    
    if gsc_df.empty or shopify_df.empty:
        print("⚠️ Datos insuficientes para el cruce. Revisa credenciales.")
        return

    # 3. Cruzar Datos (Mapping URL -> Handle)
    # GSC URL suele ser https://colvinycia.cl/products/nombre-producto
    gsc_df['handle'] = gsc_df['url'].apply(lambda x: x.split('/')[-1] if '/products/' in x else None)
    
    # Merge
    merged = pd.merge(shopify_df, gsc_df, on='handle', how='left')
    
    # 4. Clasificación de "Oportunidad de Crecimiento"
    # FÓRMULA 2026: Low Hanging Fruit = (Posición 5-20) Y (Snippet Faltante O Contenido Pobre)
    merged['opportunity_score'] = 0.0
    
    # Aumentar score si impresiones > 100 y posición es mejorable
    merged.loc[(merged['avg_position'] > 5) & (merged['avg_position'] < 20), 'opportunity_score'] += 30
    
    # Aumentar score si falta el snippet de autoridad (E-E-A-T)
    merged.loc[merged['distributor_snippet'] == 0, 'opportunity_score'] += 40
    
    # Aumentar score si la descripción es corta (< 500 chars)
    merged.loc[merged['desc_len'] < 500, 'opportunity_score'] += 30

    # Ordenar por oportunidad y volumen de impresiones
    merged = merged.sort_values(by=['opportunity_score', 'impressions'], ascending=False)

    # 5. Guardar Reporte Maestro
    output_file = 'growth_priority_matrix.csv'
    merged.to_csv(output_file, index=False)
    
    print(f"\n✅ Matriz de Prioridad generada: {output_file}")
    print("\n📦 Top 5 Oportunidades Críticas (GEO-Ready):")
    for _, row in merged.head(5).iterrows():
        print(f" - {row['title']} | Score: {row['opportunity_score']} | Impr: {row['impressions'] or 0} | Snippet: {'❌' if not row['distributor_snippet'] else '✅'}")

if __name__ == "__main__":
    run_growth_cycle()
