import requests
import csv
import os
from dotenv import load_dotenv

# ---------------------------------------------------------
# CONFIGURACIÓN (V2026.03 - SEO AUDIT)
# ---------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Carga dinámica de .env
search_paths = [
    os.path.join(SCRIPT_DIR, ".env"),
    os.path.join(SCRIPT_DIR, "../../../.env"),
    os.path.join(SCRIPT_DIR, "../../../../.env"),
]
for p in search_paths:
    if os.path.exists(p):
        load_dotenv(p)
        break

raw_shop = os.getenv("SHOPIFY_STORE", "colvinycia")
SHOP = f"{raw_shop.split('.')[0]}.myshopify.com" if "." in raw_shop else f"{raw_shop}.myshopify.com"
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
COLLECTION_ID = os.getenv("COLLECTION_ID", "gid://shopify/Collection/434227314926")

HEADERS = {"X-Shopify-Access-Token": ACCESS_TOKEN, "Content-Type": "application/json"}

# Métrica 2026: Thin Content es < 1000 chars para ser citado por IA
GEO_MIN_CHARS = 1000 
TRUST_KEYWORDS = ["distribuidor oficial", "distribuidor autorizado", "distribución oficial"]

def get_products(collection_id, limit=50):
    url = f"https://{SHOP}/admin/api/2025-01/graphql.json"
    print(f"📡 Probando conexión a: {url}")
    
    query = """
    query getProductsByCollection($collectionId: ID!, $cursor: String) {
      collection(id: $collectionId) {
        title
        products(first: 50, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          edges {
            node {
              id
              title
              handle
              status
              vendor
              descriptionHtml
              tags
            }
          }
        }
      }
    }
    """
    
    all_products = []
    cursor = None
    
    while True:
        variables = {"collectionId": collection_id, "cursor": cursor}

            edges = collection["products"]["edges"]
            page_info = collection["products"]["pageInfo"]

            for edge in edges:
                node = edge["node"]
                
                # FILTRO: Solo productos activos
                if node["status"] != "ACTIVE":
                    continue

                # Auditoría SEO sobre el contenido
                body = node.get("bodyHtml") or ""
                has_snippet = "distribuidores oficiales FLIR en Chile" in body
                
                # Procesar variantes
                for v in node["variants"]["edges"]:
                    variant = v["node"]
                    products.append({
                        "collection": collection["title"],
                        "product_id": node["id"],
                        "title": node["title"],
                        "handle": node["handle"],
                        "status": node["status"],
                        "sku": variant["sku"],
                        "price": variant["price"],
                        "inventory": variant["inventoryQuantity"],
                        "vendor": node.get("vendor"),
                        "desc_len": len(body),
                        "has_tags": 1 if node.get("tags") else 0,
                        "distributor_snippet": 1 if has_snippet else 0
                    })

            if page_info["hasNextPage"]:
                cursor = page_info["endCursor"]
                print(f"Cargando siguiente página... ({len(products)} variantes acumuladas)")
            else:
                break
                
        except Exception as e:
            print(f"Error de conexión: {e}")
            break

    return products

def audit_and_save():
    products = get_products(COLLECTION_ID)
    
    if not products:
        print("No se encontraron productos activos en esta colección.")
        return

    output_file = 'shopify_seo_audit.csv'
    
    print(f"\nColección: {products[0]['collection']} — {len(products)} variantes encontradas\n")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'collection', 'product_id', 'title', 'handle', 'status', 'sku', 
            'price', 'inventory', 'vendor', 'desc_len', 'has_tags', 'distributor_snippet'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)

    print(f"Auditoría completada. Resultados guardados en: {output_file}")
    
    # Preview en consola
    for p in products[:10]:
        print(f"  {p['title']} | SKU: {p['sku']} | Desc Len: {p['desc_len']} | Snippet: {'✅' if p['distributor_snippet'] else '❌'}")

if __name__ == "__main__":
    audit_and_save()
