import requests
import os
from dotenv import load_dotenv

load_dotenv()

SHOP = os.getenv("SHOPIFY_STORE", "colvinycia")
if not SHOP.endswith("myshopify.com") and not "." in SHOP:
    SHOP = f"{SHOP}.myshopify.com"
elif "." in SHOP and not SHOP.endswith("myshopify.com"):
    # Si el usuario puso colvinycia.cl, tal vez necesite el .myshopify.com para la API
    print(f"DEBUG: SHOP is currently {SHOP}")

ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

HEADERS = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json",
}

QUERY = "{ shop { name primaryDomain { host } } }"

def test_connection():
    # Probar con .myshopify.com primero
    actual_shop = SHOP if "myshopify.com" in SHOP else f"{SHOP.split('.')[0]}.myshopify.com"
    url = f"https://{actual_shop}/admin/api/2025-01/graphql.json"
    
    print(f"Probando conexión a: {url}")
    try:
        resp = requests.post(url, json={"query": QUERY}, headers=HEADERS)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()
