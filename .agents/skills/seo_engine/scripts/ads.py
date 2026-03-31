# Create a ready-to-use Python script and a YAML config template for Google Ads API exports.
import datetime
import os

# -*- coding: utf-8 -*-
"""
Google Ads → Exports semanales últimos 30 días (compatible con MCC o cuenta individual).
Requisitos:
  pip install google-ads==24.0.0 pandas==2.2.2

Config:
  - Crear/editar google-ads.yaml (usa el .template provisto)
  - Ubicarlo en el mismo directorio o exportar la variable:
      export GOOGLE_ADS_CONFIGURATION_FILE=/ruta/a/google-ads.yaml

Ejecución (ejemplos):
  - Cuenta individual:
      python google_ads_export.py --customer-id 6991880139
  - MCC (manager): (lee todas las cuentas hijas no administradoras)
      python google_ads_export.py --login-customer-id 6991880139

Parámetros útiles:
  --start-date YYYY-MM-DD (default: hoy-30)
  --end-date   YYYY-MM-DD (default: hoy)
  --customer-ids 1112223333,4445556666  (forzar lista específica)
  --output-dir ./exports

Salidas (CSV):
  campaigns_weekly.csv
  search_terms_weekly.csv
  device_weekly.csv
  geo_country_weekly.csv
  pmax_asset_groups_weekly.csv
  pmax_assets_weekly.csv
"""

import argparse
import sys
from datetime import datetime, timedelta

import pandas as pd
from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# Carga .env (busca en el directorio del script y ancestros)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
for _env_path in [
    os.path.join(_SCRIPT_DIR, ".env"),
    os.path.join(_SCRIPT_DIR, "../../../.env"),
    os.path.join(_SCRIPT_DIR, "../../../../.env"),
]:
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
        break


def parse_args():
    ap = argparse.ArgumentParser(description="Exportaciones Google Ads (últimos 30 días, segmentación semanal).")
    ap.add_argument("--customer-id", type=str, help="Customer ID sin guiones (cuenta individual).")
    ap.add_argument(
        "--login-customer-id",
        type=str,
        help="MCC / Manager ID sin guiones para operar como administrador.",
    )
    ap.add_argument(
        "--customer-ids",
        type=str,
        help="Lista de customer IDs separados por coma (prioritario vs. descubrimiento).",
    )
    ap.add_argument("--start-date", type=str, help="YYYY-MM-DD (default: hoy-30)")
    ap.add_argument("--end-date", type=str, help="YYYY-MM-DD (default: hoy)")
    ap.add_argument("--output-dir", type=str, default="./exports", help="Directorio de salida")
    return ap.parse_args()


def load_client(login_customer_id: str | None = None) -> GoogleAdsClient:
    # Intenta cargar desde el mismo directorio que el script si existe
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(script_dir, "google-ads.yaml")
    
    if os.path.exists(local_path):
        client = GoogleAdsClient.load_from_storage(local_path, version="v18")
        print(f"[INFO] Cargando config Google Ads de: {local_path}")
    else:
        # Fallback al comportamiento estándar (variable de entorno o ubicación default)
        client = GoogleAdsClient.load_from_storage(version="v18")
    
    if login_customer_id:
        client.login_customer_id = login_customer_id.replace("-", "")
    return client


def discover_child_customers(client: GoogleAdsClient, manager_cid: str) -> list[str]:
    """Devuelve IDs de clientes 'no manager' bajo un MCC dado."""
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT
          customer_client.client_customer,
          customer_client.level,
          customer_client.hidden,
          customer_client.manager,
          customer_client.descriptive_name
        FROM customer_client
        WHERE customer_client.level >= 1
    """
    customer_ids = []
    stream = ga_service.search_stream(customer_id=manager_cid, query=query)
    for batch in stream:
        for row in batch.results:
            cc = row.customer_client
            if (not cc.hidden) and (not cc.manager) and cc.client_customer:
                # client_customer tiene formato "customers/1234567890"
                cid = cc.client_customer.split("/")[-1]
                customer_ids.append(cid)
    # Elimina duplicados
    return sorted(list(set(customer_ids)))


def run_query(client: GoogleAdsClient, customer_id: str, gaql: str) -> list[dict]:
    ga_service = client.get_service("GoogleAdsService")
    rows = []
    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=gaql)
        for batch in stream:
            for row in batch.results:
                rows.append(row)
    except GoogleAdsException as ex:
        print(f"[WARN] GAQL error for customer {customer_id}: {ex}", file=sys.stderr)
    return rows


def rows_to_dataframe(rows, field_map):
    """Convierte filas de la API a DataFrame usando un mapeo lambda por columna."""
    data = []
    for r in rows:
        item = {}
        for col, getter in field_map.items():
            try:
                item[col] = getter(r)
            except Exception:
                item[col] = None
        data.append(item)
    return pd.DataFrame(data)


def export_csv(df: pd.DataFrame, outdir: str, filename: str):
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, filename)
    df.to_csv(path, index=False)
    print(f"[OK] {filename}: {len(df)} filas")
    return path


def main():
    args = parse_args()
    outdir = args.output_dir

    # Rango de fechas
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date() if args.end_date else datetime.utcnow().date()
    start_date = (
        datetime.strptime(args.start_date, "%Y-%m-%d").date() if args.start_date else (end_date - timedelta(days=30))
    )

    # IDs — CLI args tienen prioridad, .env como fallback
    explicit_ids = []
    if args.customer_ids:
        explicit_ids = [x.strip().replace("-", "") for x in args.customer_ids.split(",") if x.strip()]

    customer_id = args.customer_id.replace("-", "") if args.customer_id else None
    if not customer_id:
        env_cid = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "").strip().replace("-", "")
        if env_cid:
            customer_id = env_cid
            print(f"[INFO] Customer ID desde .env: {customer_id}")

    login_cid = args.login_customer_id.replace("-", "") if args.login_customer_id else None
    if not login_cid:
        env_login = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").strip().replace("-", "")
        if env_login:
            login_cid = env_login
            print(f"[INFO] Login Customer ID (MCC) desde .env: {login_cid}")

    client = load_client(login_cid)

    target_customers = []
    if explicit_ids:
        target_customers = explicit_ids
    elif customer_id:
        target_customers = [customer_id]
    elif login_cid:
        target_customers = discover_child_customers(client, login_cid)
        if not target_customers:
            print(
                "[WARN] No se encontraron cuentas hijas bajo el MCC. Usa --customer-ids.",
                file=sys.stderr,
            )
    else:
        print(
            "ERROR: Debes indicar --customer-id, --customer-ids, --login-customer-id (MCC),\n"
            "       o definir GOOGLE_ADS_CUSTOMER_ID en tu .env",
            file=sys.stderr,
        )
        sys.exit(1)

    # GAQL commons
    date_filter = f"WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'"

    # 1) Campaign weekly performance
    campaign_gaql = f"""
        SELECT
          customer.id,
          customer.descriptive_name,
          campaign.id,
          campaign.name,
          campaign.advertising_channel_type,
          segments.week,
          metrics.impressions,
          metrics.clicks,
          metrics.ctr,
          metrics.average_cpc,
          metrics.conversions,
          metrics.conversions_value,
          metrics.cost_micros
        FROM campaign
        {date_filter}
    """
    # 2) Search terms (Search campaigns)
    search_terms_gaql = f"""
        SELECT
          customer.id,
          campaign.id,
          campaign.name,
          ad_group.id,
          ad_group.name,
          segments.week,
          search_term_view.search_term,
          metrics.impressions,
          metrics.clicks,
          metrics.conversions,
          metrics.cost_micros
        FROM search_term_view
        {date_filter}
    """
    # 3) Device performance
    device_gaql = f"""
        SELECT
          customer.id,
          campaign.id,
          campaign.name,
          segments.week,
          segments.device,
          metrics.impressions,
          metrics.clicks,
          metrics.conversions,
          metrics.conversions_value,
          metrics.cost_micros
        FROM campaign
        {date_filter}
    """
    # 4) Geo performance (country)
    geo_country_gaql = f"""
        SELECT
          customer.id,
          campaign.id,
          campaign.name,
          segments.week,
          segments.geo_target_country,
          metrics.impressions,
          metrics.clicks,
          metrics.conversions,
          metrics.cost_micros
        FROM campaign
        {date_filter}
    """
    # 5) Performance Max: asset group performance
    pmax_groups_gaql = f"""
        SELECT
          customer.id,
          campaign.id,
          campaign.name,
          asset_group.id,
          asset_group.name,
          segments.week,
          metrics.impressions,
          metrics.clicks,
          metrics.conversions,
          metrics.conversions_value,
          metrics.cost_micros
        FROM asset_group
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
          AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    """
    # 6) Performance Max: assets inside groups
    pmax_assets_gaql = f"""
        SELECT
          customer.id,
          campaign.id,
          asset_group.id,
          asset_group_asset.asset,
          asset.name,
          asset.type,
          segments.week,
          metrics.impressions,
          metrics.clicks
        FROM asset_group_asset
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
    """
    # 7) Quality Score por keyword
    quality_score_gaql = f"""
        SELECT
          customer.id,
          campaign.id,
          campaign.name,
          ad_group.id,
          ad_group.name,
          ad_group_criterion.keyword.text,
          ad_group_criterion.keyword.match_type,
          ad_group_criterion.quality_info.quality_score,
          ad_group_criterion.quality_info.creative_quality_score,
          ad_group_criterion.quality_info.post_click_quality_score,
          ad_group_criterion.quality_info.search_predicted_ctr,
          metrics.impressions,
          metrics.clicks,
          metrics.conversions,
          metrics.cost_micros
        FROM keyword_view
        {date_filter}
    """
    # 8) Ad Copy (Responsive Search Ads)
    ad_copy_gaql = f"""
        SELECT
          customer.id,
          campaign.id,
          campaign.name,
          ad_group.id,
          ad_group.name,
          ad_group_ad.ad.id,
          ad_group_ad.ad.responsive_search_ad.headlines,
          ad_group_ad.ad.responsive_search_ad.descriptions,
          ad_group_ad.ad.final_urls,
          ad_group_ad.ad.type,
          metrics.impressions,
          metrics.clicks,
          metrics.conversions,
          metrics.cost_micros
        FROM ad_group_ad
        {date_filter}
    """

    # Output aggregations
    all_campaigns, all_terms, all_device, all_geo_c, all_pmax_g, all_pmax_a = (
        [],
        [],
        [],
        [],
        [],
        [],
    )
    all_quality_score, all_ad_copy = [], []

    for cid in target_customers:
        print(f"\n=== Procesando customer {cid} ===")
        # campaigns
        rows = run_query(client, cid, campaign_gaql)
        df = rows_to_dataframe(
            rows,
            {
                "customer_id": lambda r: r.customer.id,
                "customer_name": lambda r: r.customer.descriptive_name,
                "campaign_id": lambda r: r.campaign.id,
                "campaign_name": lambda r: r.campaign.name,
                "channel": lambda r: r.campaign.advertising_channel_type.name,
                "week": lambda r: r.segments.week.value if r.segments.week else None,
                "impr": lambda r: r.metrics.impressions,
                "clicks": lambda r: r.metrics.clicks,
                "ctr": lambda r: r.metrics.ctr,
                "avg_cpc": lambda r: (
                    float(r.metrics.average_cpc.micros) / 1e6
                    if r.metrics.average_cpc and r.metrics.average_cpc.micros
                    else None
                ),
                "conversions": lambda r: r.metrics.conversions,
                "conv_value": lambda r: r.metrics.conversions_value,
                "cost": lambda r: float(r.metrics.cost_micros) / 1e6 if r.metrics.cost_micros else 0.0,
            },
        )
        df["customer_id"] = df["customer_id"].astype(str)
        all_campaigns.append(df)

        # search terms
        rows = run_query(client, cid, search_terms_gaql)
        df = rows_to_dataframe(
            rows,
            {
                "customer_id": lambda r: r.customer.id,
                "campaign_id": lambda r: r.campaign.id,
                "campaign_name": lambda r: r.campaign.name,
                "ad_group_id": lambda r: r.ad_group.id,
                "ad_group_name": lambda r: r.ad_group.name,
                "week": lambda r: r.segments.week.value if r.segments.week else None,
                "search_term": lambda r: r.search_term_view.search_term,
                "impr": lambda r: r.metrics.impressions,
                "clicks": lambda r: r.metrics.clicks,
                "conversions": lambda r: r.metrics.conversions,
                "cost": lambda r: float(r.metrics.cost_micros) / 1e6 if r.metrics.cost_micros else 0.0,
            },
        )
        all_terms.append(df)

        # device
        rows = run_query(client, cid, device_gaql)
        df = rows_to_dataframe(
            rows,
            {
                "customer_id": lambda r: r.customer.id,
                "campaign_id": lambda r: r.campaign.id,
                "campaign_name": lambda r: r.campaign.name,
                "week": lambda r: r.segments.week.value if r.segments.week else None,
                "device": lambda r: r.segments.device.name,
                "impr": lambda r: r.metrics.impressions,
                "clicks": lambda r: r.metrics.clicks,
                "conversions": lambda r: r.metrics.conversions,
                "conv_value": lambda r: r.metrics.conversions_value,
                "cost": lambda r: float(r.metrics.cost_micros) / 1e6 if r.metrics.cost_micros else 0.0,
            },
        )
        all_device.append(df)

        # geo country
        rows = run_query(client, cid, geo_country_gaql)
        df = rows_to_dataframe(
            rows,
            {
                "customer_id": lambda r: r.customer.id,
                "campaign_id": lambda r: r.campaign.id,
                "campaign_name": lambda r: r.campaign.name,
                "week": lambda r: r.segments.week.value if r.segments.week else None,
                "country": lambda r: r.segments.geo_target_country.name if r.segments.geo_target_country else None,
                "impr": lambda r: r.metrics.impressions,
                "clicks": lambda r: r.metrics.clicks,
                "conversions": lambda r: r.metrics.conversions,
                "cost": lambda r: float(r.metrics.cost_micros) / 1e6 if r.metrics.cost_micros else 0.0,
            },
        )
        all_geo_c.append(df)

        # pmax groups
        rows = run_query(client, cid, pmax_groups_gaql)
        df = rows_to_dataframe(
            rows,
            {
                "customer_id": lambda r: r.customer.id,
                "campaign_id": lambda r: r.campaign.id,
                "campaign_name": lambda r: r.campaign.name,
                "asset_group_id": lambda r: r.asset_group.id,
                "asset_group_name": lambda r: r.asset_group.name,
                "week": lambda r: r.segments.week.value if r.segments.week else None,
                "impr": lambda r: r.metrics.impressions,
                "clicks": lambda r: r.metrics.clicks,
                "conversions": lambda r: r.metrics.conversions,
                "conv_value": lambda r: r.metrics.conversions_value,
                "cost": lambda r: float(r.metrics.cost_micros) / 1e6 if r.metrics.cost_micros else 0.0,
            },
        )
        all_pmax_g.append(df)

        # pmax assets
        rows = run_query(client, cid, pmax_assets_gaql)
        df = rows_to_dataframe(
            rows,
            {
                "customer_id": lambda r: r.customer.id,
                "campaign_id": lambda r: r.campaign.id if hasattr(r, "campaign") else None,
                "asset_group_id": lambda r: r.asset_group.id if hasattr(r, "asset_group") else None,
                "asset_resource_name": lambda r: r.asset_group_asset.asset if hasattr(r, "asset_group_asset") else None,
                "asset_name": lambda r: r.asset.name if hasattr(r, "asset") else None,
                "asset_type": lambda r: r.asset.type.name if hasattr(r, "asset") and r.asset.type else None,
                "week": lambda r: r.segments.week.value if r.segments.week else None,
                "impr": lambda r: r.metrics.impressions,
                "clicks": lambda r: r.metrics.clicks,
            },
        )
        all_pmax_a.append(df)

        # quality score
        rows = run_query(client, cid, quality_score_gaql)
        df = rows_to_dataframe(
            rows,
            {
                "customer_id": lambda r: r.customer.id,
                "campaign_id": lambda r: r.campaign.id,
                "campaign_name": lambda r: r.campaign.name,
                "ad_group_id": lambda r: r.ad_group.id,
                "ad_group_name": lambda r: r.ad_group.name,
                "keyword": lambda r: r.ad_group_criterion.keyword.text,
                "match_type": lambda r: r.ad_group_criterion.keyword.match_type.name,
                "quality_score": lambda r: r.ad_group_criterion.quality_info.quality_score,
                "creative_quality": lambda r: r.ad_group_criterion.quality_info.creative_quality_score.name,
                "landing_page_quality": lambda r: r.ad_group_criterion.quality_info.post_click_quality_score.name,
                "predicted_ctr": lambda r: r.ad_group_criterion.quality_info.search_predicted_ctr.name,
                "impr": lambda r: r.metrics.impressions,
                "clicks": lambda r: r.metrics.clicks,
                "conversions": lambda r: r.metrics.conversions,
                "cost": lambda r: float(r.metrics.cost_micros) / 1e6 if r.metrics.cost_micros else 0.0,
            },
        )
        all_quality_score.append(df)

        # ad copy
        rows = run_query(client, cid, ad_copy_gaql)
        df = rows_to_dataframe(
            rows,
            {
                "customer_id": lambda r: r.customer.id,
                "campaign_id": lambda r: r.campaign.id,
                "campaign_name": lambda r: r.campaign.name,
                "ad_group_id": lambda r: r.ad_group.id,
                "ad_group_name": lambda r: r.ad_group.name,
                "ad_id": lambda r: r.ad_group_ad.ad.id,
                "ad_type": lambda r: r.ad_group_ad.ad.type_.name if r.ad_group_ad.ad.type_ else None,
                "headlines": lambda r: "|||".join(
                    [h.text for h in r.ad_group_ad.ad.responsive_search_ad.headlines]
                ) if r.ad_group_ad.ad.responsive_search_ad and r.ad_group_ad.ad.responsive_search_ad.headlines else None,
                "descriptions": lambda r: "|||".join(
                    [d.text for d in r.ad_group_ad.ad.responsive_search_ad.descriptions]
                ) if r.ad_group_ad.ad.responsive_search_ad and r.ad_group_ad.ad.responsive_search_ad.descriptions else None,
                "final_urls": lambda r: "|||".join(
                    list(r.ad_group_ad.ad.final_urls)
                ) if r.ad_group_ad.ad.final_urls else None,
                "impr": lambda r: r.metrics.impressions,
                "clicks": lambda r: r.metrics.clicks,
                "conversions": lambda r: r.metrics.conversions,
                "cost": lambda r: float(r.metrics.cost_micros) / 1e6 if r.metrics.cost_micros else 0.0,
            },
        )
        all_ad_copy.append(df)

    # Concatenate & export
    def concat_and_export(dfs, name):
        if not dfs:
            return None
        df = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
        return export_csv(df, outdir, name)

    paths = []
    paths.append(concat_and_export(all_campaigns, "campaigns_weekly.csv"))
    paths.append(concat_and_export(all_terms, "search_terms_weekly.csv"))
    paths.append(concat_and_export(all_device, "device_weekly.csv"))
    paths.append(concat_and_export(all_geo_c, "geo_country_weekly.csv"))
    paths.append(concat_and_export(all_pmax_g, "pmax_asset_groups_weekly.csv"))
    paths.append(concat_and_export(all_pmax_a, "pmax_assets_weekly.csv"))
    paths.append(concat_and_export(all_quality_score, "quality_score_keywords.csv"))
    paths.append(concat_and_export(all_ad_copy, "ad_copy_performance.csv"))

    print("\nListo. Archivos generados en:", outdir)
    for p in paths:
        if p:
            print(" -", p)


if __name__ == "__main__":
    main()
