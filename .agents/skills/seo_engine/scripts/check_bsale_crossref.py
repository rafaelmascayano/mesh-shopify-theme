import requests
import os
import csv
from dotenv import load_dotenv

load_dotenv()

# BSale config from app/bsale_api.py logic or env
BSALE_TOKEN = os.getenv("BSALE_ACCESS_TOKEN")
BSALE_URL = "https://api.bsale.cl/v1/variants.json"
BSALE_HEADERS = {"access_token": BSALE_TOKEN, "Accept": "application/json"}

TARGET_SKUS = ["REP-001", "T199425ACC", "T197692", "T199369ACC"]

def cross_check():
    print(f"Buscando SKUs en BSale: {TARGET_SKUS}")
    results = []
    
    # We scan variants.json for these codes
    # Since we can't search by multiple SKUs directly in one call easily without knowing the variant list
    # we use the 'code' filter if supported? actually BSale allows ?code=XXX
    
    for sku in TARGET_SKUS:
        resp = requests.get(BSALE_URL, params={"code": sku}, headers=BSALE_HEADERS)
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            for item in items:
                # Get the product info to see description
                product_url = item.get("product", {}).get("href")
                desc = ""
                if product_url:
                    p_resp = requests.get(product_url, headers=BSALE_HEADERS)
                    if p_resp.status_code == 200:
                        desc = p_resp.json().get("description", "")
                
                results.append({
                    "sku": sku,
                    "bsale_name": item.get("name"),
                    "bsale_desc": desc,
                    "has_bsale_desc": 1 if desc else 0
                })
        else:
            print(f"Error buscando {sku}: {resp.status_code}")

    output_file = 'bsale_seo_crosscheck.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["sku", "bsale_name", "bsale_desc", "has_bsale_desc"])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Cruce con BSale finalizado. Resultado en: {output_file}")
    for r in results:
        print(f"  SKU: {r['sku']} | BSale Desc: {'✅' if r['has_bsale_desc'] else '❌'}")

if __name__ == "__main__":
    cross_check()
