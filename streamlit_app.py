"""
Retail Lakehouse — Analytics Dashboard
======================================
An interactive analytics dashboard that visualizes the Gold-layer output of the
Retail Lakehouse Pipeline (PySpark + Delta Lake + dbt + Airflow).

For this live demo the data is generated deterministically in-memory so the app
is fully self-contained. In production this dashboard reads from the Gold Delta
tables / warehouse marts produced by the pipeline.

Author: Aditya Yadav
"""

from __future__ import annotations
import datetime as dt

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# Page config + theme
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Retail Lakehouse — Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .main { background-color: #0e1117; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    /* KPI cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1b2030, #161a26);
        border: 1px solid #2a3142;
        border-radius: 14px;
        padding: 18px 18px 10px 18px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.35);
    }
    div[data-testid="stMetricLabel"] p { color: #9aa4b8 !important; font-weight: 600; }
    div[data-testid="stMetricValue"] { color: #ffffff; font-size: 1.9rem; }
    h1, h2, h3 { color: #e8ecf4; }
    .pill {
        display:inline-block; padding:3px 12px; border-radius:999px;
        font-size:0.78rem; font-weight:700; letter-spacing:.3px;
    }
    .ok   { background:#10381f; color:#46d17a; border:1px solid #1d6b3a; }
    .warn { background:#3a2f12; color:#e8b339; border:1px solid #6b541d; }
    .fail { background:#3a1620; color:#ff6b81; border:1px solid #6b1d2e; }
    .layer-card {
        background:linear-gradient(145deg,#1b2030,#161a26);
        border:1px solid #2a3142; border-radius:14px; padding:16px 18px; margin-bottom:8px;
    }
    .muted { color:#8b94a7; font-size:0.85rem; }
    footer {visibility:hidden;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

REGIONS = ["North", "South", "East", "West"]
CATEGORIES = ["Apparel", "Footwear", "Accessories", "Equipment"]
PRODUCTS = [
    "Ultraboost Runner", "Classic Tee", "Pro Trackpants", "Trail Jacket",
    "Court Sneaker", "Gym Duffel", "Flex Shorts", "Aero Cap",
    "Power Hoodie", "Speed Socks", "Climacool Polo", "Stadium Backpack",
]


# ----------------------------------------------------------------------------
# Data generation (deterministic) — mimics the Gold layer marts
# ----------------------------------------------------------------------------
@st.cache_data
def load_data(days: int = 180, seed: int = 42):
    rng = np.random.default_rng(seed)
    end = dt.date.today()
    dates = pd.date_range(end - dt.timedelta(days=days - 1), end, freq="D")

    rows = []
    for d in dates:
        # seasonality + weekend lift + slow upward trend
        base = 1.0 + 0.25 * np.sin(2 * np.pi * d.dayofyear / 365)
        weekend = 1.25 if d.weekday() >= 5 else 1.0
        trend = 1.0 + (d - dates[0]).days / (days * 4)
        for region in REGIONS:
            region_factor = {"North": 1.2, "South": 0.9, "East": 1.05, "West": 1.0}[region]
            orders = int(rng.normal(120, 18) * base * weekend * trend * region_factor)
            orders = max(orders, 5)
            aov = float(rng.normal(82, 9))
            revenue = round(orders * aov, 2)
            rows.append({
                "order_date": d.date(),
                "region": region,
                "total_orders": orders,
                "total_revenue": revenue,
                "avg_order_value": round(aov, 2),
                "unique_customers": int(orders * rng.uniform(0.7, 0.92)),
            })
    daily = pd.DataFrame(rows)

    # product/category breakdown
    prod_rows = []
    for p in PRODUCTS:
        cat = rng.choice(CATEGORIES)
        units = int(rng.normal(8000, 2500))
        rev = round(units * rng.uniform(40, 180), 2)
        prod_rows.append({"product_name": p, "category": cat, "units_sold": max(units, 500), "revenue": rev})
    products = pd.DataFrame(prod_rows).sort_values("revenue", ascending=False)

    # customer LTV
    n_cust = 1000
    ltv = rng.gamma(shape=2.0, scale=900, size=n_cust).round(2)
    cust = pd.DataFrame({
        "customer_id": range(1, n_cust + 1),
        "region": rng.choice(REGIONS, n_cust),
        "lifetime_value": ltv,
        "total_orders": rng.integers(1, 40, n_cust),
    })
    def tier(v):
        if v >= 5000: return "Platinum"
        if v >= 2000: return "Gold"
        if v >= 500:  return "Silver"
        return "Bronze"
    cust["ltv_tier"] = cust["lifetime_value"].apply(tier)

    # weekday x hour heatmap
    heat = rng.normal(100, 20, size=(7, 24)).clip(10)
    heat[:, 9:21] *= 1.6           # daytime lift
    heat[5:, :] *= 1.2             # weekend lift
    return daily, products, cust, heat


daily, products, customers, heat = load_data()


# ----------------------------------------------------------------------------
# Sidebar — branding + filters
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🛒 Retail Lakehouse")
    st.caption("Analytics Dashboard · Gold Layer")
    st.markdown('<span class="pill ok">● PIPELINE HEALTHY</span>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("#### Filters")
    min_d, max_d = daily["order_date"].min(), daily["order_date"].max()
    date_range = st.date_input("Date range", (min_d, max_d), min_value=min_d, max_value=max_d)
    regions_sel = st.multiselect("Region", REGIONS, default=REGIONS)
    st.markdown("---")
    st.caption("Built by **Aditya Yadav**")
    st.caption("Data Engineer · Spark · AWS · Databricks")
    st.markdown("[GitHub](https://github.com/adityayadav97) · [LinkedIn](https://www.linkedin.com/in/theadityayadav/)")

# apply filters
if isinstance(date_range, tuple) and len(date_range) == 2:
    d0, d1 = date_range
else:
    d0, d1 = min_d, max_d
mask = (daily["order_date"] >= d0) & (daily["order_date"] <= d1) & (daily["region"].isin(regions_sel))
df = daily[mask].copy()
if df.empty:
    st.warning("No data for the selected filters.")
    st.stop()


# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.title("Retail Lakehouse — Analytics Dashboard")
st.markdown(
    '<span class="muted">Live demo visualizing the Gold-layer marts produced by the '
    "PySpark + Delta Lake + dbt + Airflow pipeline.</span>",
    unsafe_allow_html=True,
)

# KPI row
tot_rev = df["total_revenue"].sum()
tot_ord = int(df["total_orders"].sum())
aov = tot_rev / max(tot_ord, 1)
cust_cnt = int(df["unique_customers"].sum())

# previous period delta
span = (d1 - d0).days + 1
prev_mask = (daily["order_date"] >= d0 - dt.timedelta(days=span)) & (daily["order_date"] < d0) & (daily["region"].isin(regions_sel))
prev = daily[prev_mask]
def delta_pct(cur, prv):
    return f"{((cur - prv) / prv * 100):+.1f}%" if prv else "—"

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", f"${tot_rev/1e6:.2f}M", delta_pct(tot_rev, prev["total_revenue"].sum()))
c2.metric("Total Orders", f"{tot_ord:,}", delta_pct(tot_ord, prev["total_orders"].sum()))
c3.metric("Avg Order Value", f"${aov:.2f}")
c4.metric("Unique Customers", f"{cust_cnt:,}", delta_pct(cust_cnt, prev["unique_customers"].sum()))

st.markdown("")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview", "🛍️ Sales", "👥 Customers", "✅ Data Quality", "🏗️ Pipeline Health"]
)

# ---- TAB 1: Overview --------------------------------------------------------
with tab1:
    ts = df.groupby("order_date", as_index=False)["total_revenue"].sum()
    ts["ma7"] = ts["total_revenue"].rolling(7, min_periods=1).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts["order_date"], y=ts["total_revenue"], name="Daily Revenue",
                             line=dict(color="#4c8bf5", width=1.5)))
    fig.add_trace(go.Scatter(x=ts["order_date"], y=ts["ma7"], name="7-Day Moving Avg",
                             line=dict(color="#f5a623", width=3)))
    fig.update_layout(template="plotly_dark", height=380, title="Revenue Trend",
                      legend=dict(orientation="h", y=1.1), margin=dict(t=60, l=10, r=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    cc1, cc2 = st.columns(2)
    by_region = df.groupby("region", as_index=False)["total_revenue"].sum()
    f2 = px.bar(by_region, x="region", y="total_revenue", color="region",
                template="plotly_dark", title="Revenue by Region", text_auto=".2s")
    f2.update_layout(height=330, showlegend=False, margin=dict(t=50, l=10, r=10, b=10))
    cc1.plotly_chart(f2, use_container_width=True)

    by_cat = products.groupby("category", as_index=False)["revenue"].sum()
    f3 = px.pie(by_cat, names="category", values="revenue", hole=0.55,
                template="plotly_dark", title="Revenue by Category")
    f3.update_layout(height=330, margin=dict(t=50, l=10, r=10, b=10))
    cc2.plotly_chart(f3, use_container_width=True)

# ---- TAB 2: Sales -----------------------------------------------------------
with tab2:
    cc1, cc2 = st.columns([3, 2])
    top = products.head(10).sort_values("revenue")
    f = px.bar(top, x="revenue", y="product_name", orientation="h",
               template="plotly_dark", title="Top Products by Revenue", text_auto=".2s",
               color="revenue", color_continuous_scale="Blues")
    f.update_layout(height=430, coloraxis_showscale=False, margin=dict(t=50, l=10, r=10, b=10))
    cc1.plotly_chart(f, use_container_width=True)

    days_lbl = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    fh = px.imshow(heat, labels=dict(x="Hour", y="Day", color="Orders"),
                   y=days_lbl, template="plotly_dark", title="Order Heatmap (Day × Hour)",
                   color_continuous_scale="Viridis", aspect="auto")
    fh.update_layout(height=430, margin=dict(t=50, l=10, r=10, b=10))
    cc2.plotly_chart(fh, use_container_width=True)

    st.markdown("#### Product Detail")
    st.dataframe(products, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download product data (CSV)", products.to_csv(index=False),
                       "product_revenue.csv", "text/csv")

# ---- TAB 3: Customers -------------------------------------------------------
with tab3:
    cc1, cc2 = st.columns(2)
    tier_order = ["Platinum", "Gold", "Silver", "Bronze"]
    tiers = customers["ltv_tier"].value_counts().reindex(tier_order).reset_index()
    tiers.columns = ["tier", "customers"]
    f = px.bar(tiers, x="tier", y="customers", color="tier", template="plotly_dark",
               title="Customers by LTV Tier", text_auto=True,
               color_discrete_map={"Platinum": "#9b59b6", "Gold": "#f1c40f",
                                   "Silver": "#bdc3c7", "Bronze": "#cd7f32"})
    f.update_layout(height=350, showlegend=False, margin=dict(t=50, l=10, r=10, b=10))
    cc1.plotly_chart(f, use_container_width=True)

    reg = customers.groupby("region", as_index=False)["lifetime_value"].sum()
    f2 = px.bar(reg, x="region", y="lifetime_value", template="plotly_dark",
                title="Total Lifetime Value by Region", text_auto=".2s", color="region")
    f2.update_layout(height=350, showlegend=False, margin=dict(t=50, l=10, r=10, b=10))
    cc2.plotly_chart(f2, use_container_width=True)

    st.markdown("#### Top Customers by Lifetime Value")
    top_cust = customers.sort_values("lifetime_value", ascending=False).head(15)
    st.dataframe(top_cust, use_container_width=True, hide_index=True)

# ---- TAB 4: Data Quality ----------------------------------------------------
with tab4:
    st.markdown("#### Data Quality Gates — Latest Run")
    st.caption("Automated checks enforced between every Medallion layer before promotion.")

    checks = [
        ("Bronze → Silver", "Row count reconciliation", "PASS", "variance 0.4% (≤ 20%)"),
        ("Silver", "Null check · order_id", "PASS", "0.00% nulls (≤ 5%)"),
        ("Silver", "Null check · revenue", "PASS", "0.00% nulls (≤ 5%)"),
        ("Silver", "Uniqueness · order_id", "PASS", "0 duplicates"),
        ("Silver", "Schema validation", "PASS", "all expected columns present"),
        ("Gold", "Freshness", "PASS", "last load 38 min ago"),
        ("Gold", "Delta threshold", "WARN", "variance 16.2% (threshold 15%)"),
    ]
    dq = pd.DataFrame(checks, columns=["Layer", "Check", "Status", "Detail"])

    def badge(s):
        cls = {"PASS": "ok", "WARN": "warn", "FAIL": "fail"}[s]
        return f'<span class="pill {cls}">{s}</span>'

    passed = (dq["Status"] == "PASS").sum()
    k1, k2, k3 = st.columns(3)
    k1.metric("Checks Passed", f"{passed}/{len(dq)}")
    k2.metric("Warnings", int((dq["Status"] == "WARN").sum()))
    k3.metric("Failures", int((dq["Status"] == "FAIL").sum()))

    html = "<table style='width:100%; border-collapse:collapse;'>"
    html += "<tr style='text-align:left; color:#9aa4b8;'><th>Layer</th><th>Check</th><th>Status</th><th>Detail</th></tr>"
    for _, r in dq.iterrows():
        html += (f"<tr style='border-top:1px solid #2a3142;'>"
                 f"<td style='padding:8px 4px;'>{r['Layer']}</td>"
                 f"<td>{r['Check']}</td><td>{badge(r['Status'])}</td>"
                 f"<td class='muted'>{r['Detail']}</td></tr>")
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

# ---- TAB 5: Pipeline Health -------------------------------------------------
with tab5:
    st.markdown("#### Medallion Architecture — Layer Status")
    layers = [
        ("🥉 Bronze", "Raw ingestion (append-only)", "2,418,930", "Delta", "✅ Healthy"),
        ("🥈 Silver", "Cleaned · deduped · conformed", "2,401,772", "Delta", "✅ Healthy"),
        ("🥇 Gold", "Business aggregates / KPIs", "1,284", "Delta", "✅ Healthy"),
        ("📊 Marts", "dbt analytics models", "6 models", "dbt", "✅ Built"),
    ]
    cols = st.columns(4)
    for col, (name, desc, rec, fmt, status) in zip(cols, layers):
        col.markdown(
            f"<div class='layer-card'><h4 style='margin:0'>{name}</h4>"
            f"<div class='muted'>{desc}</div><br>"
            f"<div style='font-size:1.4rem;font-weight:700'>{rec}</div>"
            f"<div class='muted'>{fmt}</div><br>"
            f"<span class='pill ok'>{status}</span></div>",
            unsafe_allow_html=True,
        )

    st.markdown("#### Last DAG Run — `retail_lakehouse_pipeline`")
    runs = pd.DataFrame([
        ("bronze_ingest", "success", "1m 12s"),
        ("silver_transform", "success", "2m 04s"),
        ("gold_aggregate", "success", "1m 38s"),
        ("dbt_build", "success", "0m 51s"),
    ], columns=["Task", "Status", "Duration"])
    st.dataframe(runs, use_container_width=True, hide_index=True)
    st.caption("Orchestrated by Apache Airflow · schedule: daily @ 02:00 UTC")

st.markdown("---")
st.caption("Retail Lakehouse Analytics · Built by Aditya Yadav · PySpark · Delta Lake · dbt · Airflow")
