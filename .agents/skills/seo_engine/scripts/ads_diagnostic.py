# -*- coding: utf-8 -*-
"""
Google Ads Campaign Diagnostic Engine
======================================
Lee los CSVs exportados por ads.py y genera un reporte de diagnóstico completo
con recomendaciones accionables: keywords negativas, keywords a agregar,
mejoras de segmentación, redistribución de presupuesto, y análisis de copy.

Ejecución:
    python ads_diagnostic.py --input-dir ./exports --output ./diagnostic_report.md

Requiere:
    pip install pandas
"""

import argparse
import os
import sys
from datetime import datetime

import pandas as pd


# ─────────────────────────────────────────────────
# Configuración de umbrales
# ─────────────────────────────────────────────────
THRESHOLDS = {
    # Keywords negativas: gasto > X y 0 conversiones
    "negative_kw_min_cost": 5.0,
    "negative_kw_min_clicks": 3,
    # Keywords ganadoras: conv_rate > media y CPC razonable
    "winner_kw_min_conversions": 1,
    # Campañas con bajo CTR (posible problema de relevancia)
    "low_ctr_threshold": 0.02,  # 2%
    # Campañas con alto CPC vs. promedio (posible overbid)
    "high_cpc_multiplier": 1.5,  # 1.5x el promedio
    # Quality Score bajo
    "low_quality_score": 5,
    # PMax asset sin impresiones (candidato a eliminar)
    "pmax_asset_min_impr": 10,
    # Device/Geo: diferencia significativa en conv rate
    "segment_conv_rate_diff_pct": 50,  # 50% peor que el promedio
}


def parse_args():
    ap = argparse.ArgumentParser(
        description="Diagnóstico de campañas Google Ads a partir de CSVs exportados."
    )
    ap.add_argument(
        "--input-dir",
        type=str,
        default="./exports",
        help="Directorio con los CSVs exportados por ads.py",
    )
    ap.add_argument(
        "--output",
        type=str,
        default="./diagnostic_report.md",
        help="Archivo de salida del reporte (Markdown)",
    )
    return ap.parse_args()


def load_csv(input_dir: str, filename: str) -> pd.DataFrame | None:
    """Carga un CSV si existe, retorna None si no."""
    path = os.path.join(input_dir, filename)
    if not os.path.exists(path):
        print(f"[WARN] No encontrado: {path}")
        return None
    df = pd.read_csv(path)
    print(f"[OK] {filename}: {len(df)} filas")
    return df


# ─────────────────────────────────────────────────
# Módulos de análisis
# ─────────────────────────────────────────────────


def analyze_campaigns(df: pd.DataFrame) -> dict:
    """Análisis de rendimiento por campaña."""
    if df is None or df.empty:
        return {"section": "## 📊 Campañas", "content": "_Sin datos de campañas._\n"}

    # Agregar por campaña (sin segmentación semanal)
    agg = (
        df.groupby(["campaign_id", "campaign_name"])
        .agg(
            impr=("impr", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
            conv_value=("conv_value", "sum"),
            cost=("cost", "sum"),
        )
        .reset_index()
    )
    agg["ctr"] = (agg["clicks"] / agg["impr"].replace(0, 1)) * 100
    agg["cpc"] = agg["cost"] / agg["clicks"].replace(0, 1)
    agg["conv_rate"] = (agg["conversions"] / agg["clicks"].replace(0, 1)) * 100
    agg["roas"] = agg["conv_value"] / agg["cost"].replace(0, 1)

    avg_ctr = agg["ctr"].mean()
    avg_cpc = agg["cpc"].mean()
    avg_roas = agg["roas"].mean()
    total_cost = agg["cost"].sum()
    total_conv = agg["conversions"].sum()

    lines = []
    lines.append("## 📊 Rendimiento de Campañas\n")
    lines.append("### Resumen General\n")
    lines.append(f"| Métrica | Valor |")
    lines.append(f"|---|---|")
    lines.append(f"| Inversión total | ${total_cost:,.2f} |")
    lines.append(f"| Conversiones totales | {total_conv:,.0f} |")
    lines.append(f"| CTR promedio | {avg_ctr:.2f}% |")
    lines.append(f"| CPC promedio | ${avg_cpc:,.2f} |")
    lines.append(f"| ROAS promedio | {avg_roas:.2f}x |")
    lines.append("")

    # Tabla de campañas
    lines.append("### Detalle por Campaña\n")
    lines.append(
        "| Campaña | Impr | Clicks | CTR | CPC | Conv | ROAS | Costo | Señal |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")

    recommendations = []

    for _, row in agg.sort_values("cost", ascending=False).iterrows():
        signal = "✅"
        notes = []

        if row["ctr"] < THRESHOLDS["low_ctr_threshold"] * 100:
            signal = "⚠️"
            notes.append("CTR bajo → revisar relevancia de anuncios")

        if avg_cpc > 0 and row["cpc"] > avg_cpc * THRESHOLDS["high_cpc_multiplier"]:
            signal = "⚠️"
            notes.append(
                f"CPC ${row['cpc']:.2f} es {row['cpc']/avg_cpc:.1f}x el promedio"
            )

        if row["cost"] > 0 and row["conversions"] == 0:
            signal = "🔴"
            notes.append(f"${row['cost']:.2f} gastados sin conversiones")

        if avg_roas > 0 and row["roas"] > avg_roas * 1.5:
            signal = "🟢"
            notes.append("Alto ROAS → considerar aumentar presupuesto")

        lines.append(
            f"| {row['campaign_name'][:40]} | {row['impr']:,.0f} | {row['clicks']:,.0f} | "
            f"{row['ctr']:.1f}% | ${row['cpc']:.2f} | {row['conversions']:.0f} | "
            f"{row['roas']:.2f}x | ${row['cost']:.2f} | {signal} |"
        )

        if notes:
            for n in notes:
                recommendations.append(
                    f"- **{row['campaign_name'][:40]}**: {n}"
                )

    lines.append("")
    if recommendations:
        lines.append("### 🎯 Recomendaciones de Campañas\n")
        lines.extend(recommendations)
        lines.append("")

    # Tendencia semanal
    if "week" in df.columns:
        weekly = (
            df.groupby("week")
            .agg(cost=("cost", "sum"), clicks=("clicks", "sum"), conversions=("conversions", "sum"))
            .reset_index()
            .sort_values("week")
        )
        if len(weekly) > 1:
            lines.append("### 📈 Tendencia Semanal\n")
            lines.append("| Semana | Costo | Clicks | Conversiones |")
            lines.append("|---|---|---|---|")
            for _, w in weekly.iterrows():
                lines.append(
                    f"| {w['week']} | ${w['cost']:.2f} | {w['clicks']:.0f} | {w['conversions']:.0f} |"
                )
            lines.append("")

    return {"section": "campaigns", "content": "\n".join(lines)}


def analyze_search_terms(df: pd.DataFrame) -> dict:
    """Identifica keywords negativas, ganadoras, y nuevas oportunidades."""
    if df is None or df.empty:
        return {
            "section": "## 🔑 Search Terms",
            "content": "_Sin datos de search terms._\n",
        }

    # Agregar por search term
    agg = (
        df.groupby(["search_term", "campaign_name"])
        .agg(
            impr=("impr", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
            cost=("cost", "sum"),
        )
        .reset_index()
    )
    agg["conv_rate"] = (agg["conversions"] / agg["clicks"].replace(0, 1)) * 100
    agg["cpc"] = agg["cost"] / agg["clicks"].replace(0, 1)

    lines = []
    lines.append("## 🔑 Análisis de Search Terms\n")

    # --- NEGATIVAS: alto gasto, 0 conversiones ---
    negatives = agg[
        (agg["cost"] >= THRESHOLDS["negative_kw_min_cost"])
        & (agg["conversions"] == 0)
        & (agg["clicks"] >= THRESHOLDS["negative_kw_min_clicks"])
    ].sort_values("cost", ascending=False)

    lines.append(f"### 🚫 Candidatos a Keywords Negativas ({len(negatives)} encontradas)\n")
    lines.append(
        "> Search terms con gasto ≥ ${:.2f} y {} clicks sin ninguna conversión.\n".format(
            THRESHOLDS["negative_kw_min_cost"], THRESHOLDS["negative_kw_min_clicks"]
        )
    )

    if not negatives.empty:
        lines.append("| Search Term | Campaña | Clicks | Costo | Acción |")
        lines.append("|---|---|---|---|---|")
        wasted_total = 0
        for _, row in negatives.head(30).iterrows():
            wasted_total += row["cost"]
            lines.append(
                f"| `{row['search_term']}` | {row['campaign_name'][:30]} | "
                f"{row['clicks']:.0f} | ${row['cost']:.2f} | ❌ Agregar como negativa |"
            )
        lines.append(f"\n> **💰 Ahorro potencial si se agregan como negativas: ${wasted_total:,.2f}**\n")
    else:
        lines.append("_No se encontraron candidatos obvios a negativas._\n")

    # --- GANADORAS: buena conversión, candidatas a expandir ---
    winners = agg[
        (agg["conversions"] >= THRESHOLDS["winner_kw_min_conversions"])
    ].sort_values("conversions", ascending=False)

    lines.append(f"### 🏆 Keywords Ganadoras ({len(winners)} encontradas)\n")
    lines.append("> Search terms con al menos 1 conversión. Candidatas a agregar como keywords exactas o phrase.\n")

    if not winners.empty:
        lines.append("| Search Term | Campaña | Clicks | Conv | Conv Rate | CPC | Acción |")
        lines.append("|---|---|---|---|---|---|---|")
        for _, row in winners.head(20).iterrows():
            lines.append(
                f"| `{row['search_term']}` | {row['campaign_name'][:30]} | "
                f"{row['clicks']:.0f} | {row['conversions']:.0f} | {row['conv_rate']:.1f}% | "
                f"${row['cpc']:.2f} | ✅ Agregar keyword / subir bid |"
            )
        lines.append("")
    else:
        lines.append("_No se encontraron keywords ganadoras en el período._\n")

    # --- ALTO VOLUMEN SIN CONVERSION: investigar ---
    high_vol_no_conv = agg[
        (agg["clicks"] >= 10) & (agg["conversions"] == 0)
    ].sort_values("clicks", ascending=False)

    if not high_vol_no_conv.empty:
        lines.append(f"### 🔍 Alto Tráfico Sin Conversión ({len(high_vol_no_conv)} terms)\n")
        lines.append("> Terms con 10+ clicks y 0 conversiones. Investigar intención o landing page.\n")
        lines.append("| Search Term | Clicks | Impresiones | Costo |")
        lines.append("|---|---|---|---|")
        for _, row in high_vol_no_conv.head(15).iterrows():
            lines.append(
                f"| `{row['search_term']}` | {row['clicks']:.0f} | "
                f"{row['impr']:.0f} | ${row['cost']:.2f} |"
            )
        lines.append("")

    # --- CANIBALIZACIÓN: mismo search term en múltiples campañas ---
    term_counts = df.groupby("search_term")["campaign_name"].nunique()
    cannibalized = term_counts[term_counts > 1].sort_values(ascending=False)

    if not cannibalized.empty:
        lines.append(f"### ⚔️ Posible Canibalización ({len(cannibalized)} terms)\n")
        lines.append("> Mismo search term activando múltiples campañas. Puede subir el CPC.\n")
        lines.append("| Search Term | # Campañas | Campañas |")
        lines.append("|---|---|---|")
        for term, count in cannibalized.head(15).items():
            campaigns = df[df["search_term"] == term]["campaign_name"].unique()
            camp_list = ", ".join([c[:25] for c in campaigns])
            lines.append(f"| `{term}` | {count} | {camp_list} |")
        lines.append("")

    return {"section": "search_terms", "content": "\n".join(lines)}


def analyze_quality_score(df: pd.DataFrame) -> dict:
    """Análisis de Quality Score por keyword."""
    if df is None or df.empty:
        return {
            "section": "## 📋 Quality Score",
            "content": "_Sin datos de Quality Score. Ejecuta ads.py para exportar `quality_score_keywords.csv`._\n",
        }

    lines = []
    lines.append("## 📋 Análisis de Quality Score\n")

    # Distribución general
    qs_counts = df["quality_score"].value_counts().sort_index()
    avg_qs = df["quality_score"].mean()

    lines.append(f"### Distribución General (QS Promedio: {avg_qs:.1f})\n")
    lines.append("| Quality Score | # Keywords | % |")
    lines.append("|---|---|---|")
    total_kw = len(df)
    for qs, count in qs_counts.items():
        pct = (count / total_kw) * 100
        bar = "🟢" if qs >= 7 else ("🟡" if qs >= 5 else "🔴")
        lines.append(f"| {bar} {qs}/10 | {count} | {pct:.1f}% |")
    lines.append("")

    # Keywords con QS bajo
    low_qs = df[df["quality_score"] <= THRESHOLDS["low_quality_score"]].sort_values(
        "quality_score"
    )

    if not low_qs.empty:
        lines.append(f"### 🔴 Keywords con QS Bajo (≤{THRESHOLDS['low_quality_score']}) — {len(low_qs)} keywords\n")
        lines.append(
            "| Keyword | Match | QS | Creative | Landing | CTR Pred | Campaña | Acción |"
        )
        lines.append("|---|---|---|---|---|---|---|---|")
        for _, row in low_qs.head(20).iterrows():
            actions = []
            cq = str(row.get("creative_quality", ""))
            lq = str(row.get("landing_page_quality", ""))
            pc = str(row.get("predicted_ctr", ""))

            if "BELOW_AVERAGE" in cq:
                actions.append("Mejorar copy")
            if "BELOW_AVERAGE" in lq:
                actions.append("Mejorar landing page")
            if "BELOW_AVERAGE" in pc:
                actions.append("Mejorar relevancia")

            action_str = " + ".join(actions) if actions else "Revisar"

            lines.append(
                f"| `{row['keyword']}` | {row.get('match_type', '?')} | "
                f"{row['quality_score']}/10 | {cq} | {lq} | {pc} | "
                f"{row['campaign_name'][:25]} | {action_str} |"
            )
        lines.append("")

    # Impacto económico del QS bajo
    if not low_qs.empty and "cost" in low_qs.columns:
        cost_in_low_qs = low_qs["cost"].sum()
        lines.append(
            f"> **💡 Inversión en keywords con QS bajo: ${cost_in_low_qs:,.2f}** — "
            f"Mejorar el QS de estas keywords podría reducir significativamente el CPC.\n"
        )

    return {"section": "quality_score", "content": "\n".join(lines)}


def analyze_devices(df: pd.DataFrame) -> dict:
    """Análisis de rendimiento por dispositivo."""
    if df is None or df.empty:
        return {
            "section": "## 📱 Dispositivos",
            "content": "_Sin datos de dispositivos._\n",
        }

    agg = (
        df.groupby("device")
        .agg(
            impr=("impr", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
            cost=("cost", "sum"),
        )
        .reset_index()
    )
    agg["ctr"] = (agg["clicks"] / agg["impr"].replace(0, 1)) * 100
    agg["conv_rate"] = (agg["conversions"] / agg["clicks"].replace(0, 1)) * 100
    agg["cpc"] = agg["cost"] / agg["clicks"].replace(0, 1)
    agg["cost_per_conv"] = agg["cost"] / agg["conversions"].replace(0, 1)

    avg_conv_rate = agg["conv_rate"].mean()

    lines = []
    lines.append("## 📱 Rendimiento por Dispositivo\n")
    lines.append(
        "| Dispositivo | Impresiones | Clicks | CTR | Conv | Conv Rate | CPC | CPA | Señal |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")

    recommendations = []
    for _, row in agg.sort_values("cost", ascending=False).iterrows():
        signal = "✅"
        if avg_conv_rate > 0 and row["conv_rate"] < avg_conv_rate * (
            1 - THRESHOLDS["segment_conv_rate_diff_pct"] / 100
        ):
            signal = "⚠️"
            recommendations.append(
                f"- **{row['device']}**: Conv rate {row['conv_rate']:.1f}% es significativamente "
                f"menor al promedio ({avg_conv_rate:.1f}%). Considerar reducir bid modifier."
            )
        elif row["conversions"] > 0 and row["conv_rate"] > avg_conv_rate * 1.3:
            signal = "🟢"
            recommendations.append(
                f"- **{row['device']}**: Conv rate {row['conv_rate']:.1f}% es superior al promedio. "
                f"Considerar aumentar bid modifier."
            )

        cpa_str = f"${row['cost_per_conv']:.2f}" if row["conversions"] > 0 else "N/A"
        lines.append(
            f"| {row['device']} | {row['impr']:,.0f} | {row['clicks']:,.0f} | "
            f"{row['ctr']:.1f}% | {row['conversions']:.0f} | {row['conv_rate']:.1f}% | "
            f"${row['cpc']:.2f} | {cpa_str} | {signal} |"
        )

    lines.append("")
    if recommendations:
        lines.append("### 🎯 Recomendaciones de Dispositivo\n")
        lines.extend(recommendations)
        lines.append("")

    return {"section": "devices", "content": "\n".join(lines)}


def analyze_geo(df: pd.DataFrame) -> dict:
    """Análisis de rendimiento por geografía."""
    if df is None or df.empty:
        return {
            "section": "## 🌎 Geografía",
            "content": "_Sin datos geográficos._\n",
        }

    agg = (
        df.groupby("country")
        .agg(
            impr=("impr", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
            cost=("cost", "sum"),
        )
        .reset_index()
    )
    agg["conv_rate"] = (agg["conversions"] / agg["clicks"].replace(0, 1)) * 100
    agg["cpc"] = agg["cost"] / agg["clicks"].replace(0, 1)

    lines = []
    lines.append("## 🌎 Rendimiento por Geografía\n")
    lines.append("| País/Región | Impresiones | Clicks | Conv | Conv Rate | Costo | CPC | Señal |")
    lines.append("|---|---|---|---|---|---|---|---|")

    recommendations = []
    avg_conv_rate = agg["conv_rate"].mean() if not agg.empty else 0

    for _, row in agg.sort_values("cost", ascending=False).iterrows():
        signal = "✅"
        if row["cost"] > 5 and row["conversions"] == 0:
            signal = "🔴"
            recommendations.append(
                f"- **{row['country']}**: ${row['cost']:.2f} gastados sin conversiones. "
                f"Considerar excluir esta ubicación."
            )
        elif row["conversions"] > 0 and row["conv_rate"] > avg_conv_rate * 1.3:
            signal = "🟢"

        lines.append(
            f"| {row['country']} | {row['impr']:,.0f} | {row['clicks']:,.0f} | "
            f"{row['conversions']:.0f} | {row['conv_rate']:.1f}% | ${row['cost']:.2f} | "
            f"${row['cpc']:.2f} | {signal} |"
        )

    lines.append("")
    if recommendations:
        lines.append("### 🎯 Recomendaciones de Segmentación Geo\n")
        lines.extend(recommendations)
        lines.append("")

    return {"section": "geo", "content": "\n".join(lines)}


def analyze_ad_copy(df: pd.DataFrame) -> dict:
    """Análisis de rendimiento de ad copy (RSA headlines/descriptions)."""
    if df is None or df.empty:
        return {
            "section": "## ✍️ Ad Copy",
            "content": "_Sin datos de Ad Copy. Ejecuta ads.py para exportar `ad_copy_performance.csv`._\n",
        }

    lines = []
    lines.append("## ✍️ Análisis de Ad Copy\n")

    # Agregar por ad
    agg = (
        df.groupby(["ad_id", "campaign_name", "ad_group_name"])
        .agg(
            headlines=("headlines", "first"),
            descriptions=("descriptions", "first"),
            final_urls=("final_urls", "first"),
            impr=("impr", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
            cost=("cost", "sum"),
        )
        .reset_index()
    )
    agg["ctr"] = (agg["clicks"] / agg["impr"].replace(0, 1)) * 100
    agg["conv_rate"] = (agg["conversions"] / agg["clicks"].replace(0, 1)) * 100

    # Top performers
    top = agg[agg["clicks"] > 0].sort_values("ctr", ascending=False).head(10)
    if not top.empty:
        lines.append("### 🏆 Top 10 Anuncios por CTR\n")
        lines.append("| Campaña | Ad Group | CTR | Clicks | Conv | Headlines (muestra) |")
        lines.append("|---|---|---|---|---|---|")
        for _, row in top.iterrows():
            hl_preview = str(row["headlines"] or "")[:60] + "..."
            lines.append(
                f"| {row['campaign_name'][:25]} | {row['ad_group_name'][:20]} | "
                f"{row['ctr']:.1f}% | {row['clicks']:.0f} | {row['conversions']:.0f} | {hl_preview} |"
            )
        lines.append("")

    # Worst performers
    worst = agg[agg["impr"] > 100].sort_values("ctr").head(10)
    if not worst.empty:
        lines.append("### 🔻 10 Anuncios con Peor CTR (100+ impresiones)\n")
        lines.append("| Campaña | Ad Group | CTR | Impr | Clicks | Acción |")
        lines.append("|---|---|---|---|---|---|")
        for _, row in worst.iterrows():
            lines.append(
                f"| {row['campaign_name'][:25]} | {row['ad_group_name'][:20]} | "
                f"{row['ctr']:.1f}% | {row['impr']:.0f} | {row['clicks']:.0f} | "
                f"Reescribir headlines y descriptions |"
            )
        lines.append("")

    # Análisis de headlines únicos
    all_headlines = set()
    for hl_str in df["headlines"].dropna():
        for hl in str(hl_str).split("|||"):
            hl = hl.strip()
            if hl:
                all_headlines.add(hl)

    if all_headlines:
        lines.append(f"### 📝 Headlines Únicos en Uso ({len(all_headlines)} total)\n")
        lines.append("> Revisa si hay suficiente variedad y si cubren las intenciones de búsqueda.\n")
        for hl in sorted(all_headlines)[:30]:
            lines.append(f"- `{hl}`")
        if len(all_headlines) > 30:
            lines.append(f"- _...y {len(all_headlines) - 30} más_")
        lines.append("")

    return {"section": "ad_copy", "content": "\n".join(lines)}


def analyze_pmax(df_groups: pd.DataFrame, df_assets: pd.DataFrame) -> dict:
    """Análisis de Performance Max."""
    if (df_groups is None or df_groups.empty) and (
        df_assets is None or df_assets.empty
    ):
        return {
            "section": "## 🤖 Performance Max",
            "content": "_Sin datos de Performance Max._\n",
        }

    lines = []
    lines.append("## 🤖 Performance Max\n")

    # Asset groups
    if df_groups is not None and not df_groups.empty:
        agg = (
            df_groups.groupby(["campaign_name", "asset_group_name"])
            .agg(
                impr=("impr", "sum"),
                clicks=("clicks", "sum"),
                conversions=("conversions", "sum"),
                conv_value=("conv_value", "sum"),
                cost=("cost", "sum"),
            )
            .reset_index()
        )
        agg["ctr"] = (agg["clicks"] / agg["impr"].replace(0, 1)) * 100
        agg["roas"] = agg["conv_value"] / agg["cost"].replace(0, 1)

        lines.append("### Asset Groups\n")
        lines.append(
            "| Campaña | Asset Group | Impr | Clicks | CTR | Conv | ROAS | Costo | Señal |"
        )
        lines.append("|---|---|---|---|---|---|---|---|---|")

        for _, row in agg.sort_values("cost", ascending=False).iterrows():
            signal = "✅"
            if row["cost"] > 10 and row["conversions"] == 0:
                signal = "🔴"
            elif row["roas"] > 2:
                signal = "🟢"
            lines.append(
                f"| {row['campaign_name'][:25]} | {row['asset_group_name'][:25]} | "
                f"{row['impr']:,.0f} | {row['clicks']:,.0f} | {row['ctr']:.1f}% | "
                f"{row['conversions']:.0f} | {row['roas']:.2f}x | ${row['cost']:.2f} | {signal} |"
            )
        lines.append("")

    # Assets individuales
    if df_assets is not None and not df_assets.empty:
        agg_assets = (
            df_assets.groupby(["asset_name", "asset_type"])
            .agg(impr=("impr", "sum"), clicks=("clicks", "sum"))
            .reset_index()
        )
        agg_assets["ctr"] = (
            agg_assets["clicks"] / agg_assets["impr"].replace(0, 1)
        ) * 100

        # Assets sin impresiones
        dead_assets = agg_assets[agg_assets["impr"] < THRESHOLDS["pmax_asset_min_impr"]]
        if not dead_assets.empty:
            lines.append(
                f"### ⚠️ Assets con Bajo Rendimiento ({len(dead_assets)} assets con <{THRESHOLDS['pmax_asset_min_impr']} impresiones)\n"
            )
            lines.append("| Asset | Tipo | Impresiones | Acción |")
            lines.append("|---|---|---|---|")
            for _, row in dead_assets.head(15).iterrows():
                name = str(row["asset_name"])[:40] if row["asset_name"] else "Sin nombre"
                lines.append(
                    f"| {name} | {row['asset_type']} | {row['impr']:.0f} | "
                    f"Reemplazar o eliminar |"
                )
            lines.append("")

    return {"section": "pmax", "content": "\n".join(lines)}


def generate_executive_summary(sections: list[dict], total_cost: float) -> str:
    """Genera un resumen ejecutivo con las acciones más importantes."""
    lines = []
    lines.append("# 🏥 Diagnóstico de Campañas Google Ads\n")
    lines.append(f"**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append("---\n")
    lines.append("## 📋 Resumen Ejecutivo\n")
    lines.append(
        f"Inversión total analizada: **${total_cost:,.2f}**\n"
    )
    lines.append(
        "Este reporte analiza el rendimiento de tus campañas de Google Ads e identifica "
        "oportunidades de mejora en 6 dimensiones: rendimiento general, search terms (keywords), "
        "Quality Score, dispositivos, geografía, contenido de anuncios, y Performance Max.\n"
    )
    lines.append("### ⚡ Acciones Prioritarias\n")
    lines.append(
        "Las recomendaciones detalladas se encuentran en cada sección. "
        "Revisa especialmente:\n"
    )
    lines.append("1. **Keywords Negativas** — Ahorro inmediato eliminando gasto sin conversión")
    lines.append("2. **Keywords Ganadoras** — Amplificar lo que ya funciona")
    lines.append("3. **Quality Score Bajo** — Reducir CPC mejorando relevancia")
    lines.append("4. **Segmentación** — Ajustar bids por dispositivo y geografía")
    lines.append("5. **Ad Copy** — Reescribir anuncios con bajo CTR")
    lines.append("")
    lines.append("---\n")

    return "\n".join(lines)


# ─────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────


def main():
    args = parse_args()
    input_dir = args.input_dir
    output_path = args.output

    print(f"\n{'='*60}")
    print(f"  GOOGLE ADS CAMPAIGN DIAGNOSTIC")
    print(f"  Input:  {input_dir}")
    print(f"  Output: {output_path}")
    print(f"{'='*60}\n")

    # Cargar CSVs
    campaigns_df = load_csv(input_dir, "campaigns_weekly.csv")
    search_terms_df = load_csv(input_dir, "search_terms_weekly.csv")
    device_df = load_csv(input_dir, "device_weekly.csv")
    geo_df = load_csv(input_dir, "geo_country_weekly.csv")
    pmax_groups_df = load_csv(input_dir, "pmax_asset_groups_weekly.csv")
    pmax_assets_df = load_csv(input_dir, "pmax_assets_weekly.csv")
    quality_score_df = load_csv(input_dir, "quality_score_keywords.csv")
    ad_copy_df = load_csv(input_dir, "ad_copy_performance.csv")

    print(f"\n--- Ejecutando análisis ---\n")

    # Ejecutar módulos de análisis
    sections = []
    sections.append(analyze_campaigns(campaigns_df))
    sections.append(analyze_search_terms(search_terms_df))
    sections.append(analyze_quality_score(quality_score_df))
    sections.append(analyze_devices(device_df))
    sections.append(analyze_geo(geo_df))
    sections.append(analyze_ad_copy(ad_copy_df))
    sections.append(analyze_pmax(pmax_groups_df, pmax_assets_df))

    # Calcular inversión total
    total_cost = 0
    if campaigns_df is not None and not campaigns_df.empty:
        total_cost = campaigns_df["cost"].sum()

    # Generar reporte
    report_lines = [generate_executive_summary(sections, total_cost)]
    for section in sections:
        report_lines.append(section["content"])
        report_lines.append("\n---\n")

    report = "\n".join(report_lines)

    # Guardar
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n{'='*60}")
    print(f"  ✅ REPORTE GENERADO: {output_path}")
    print(f"  Secciones: {len(sections)}")
    print(f"  Inversión analizada: ${total_cost:,.2f}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
