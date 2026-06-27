# 📊 Retail Lakehouse — Analytics Dashboard

> An interactive, production-style analytics dashboard that visualizes the **Gold-layer marts** produced by the [Retail Lakehouse Pipeline](https://github.com/adityayadav97/retail-lakehouse-pipeline) (PySpark + Delta Lake + dbt + Airflow).

<p align="left">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white">
  <img alt="Plotly" src="https://img.shields.io/badge/Plotly-3F4F75?logo=plotly&logoColor=white">
  <img alt="Pandas" src="https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=white">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green">
</p>

### 🔴 Live Demo: **[ADD-YOUR-STREAMLIT-URL-HERE]**

---

## ✨ Features

A multi-tab, company-grade BI dashboard with:

- **📊 Executive Overview** — revenue KPIs with period-over-period deltas, revenue trend with 7-day moving average, revenue by region and category
- **🛍️ Sales Analytics** — top products, category mix, and an order heatmap (day × hour)
- **👥 Customer Analytics** — LTV-tier segmentation (Platinum/Gold/Silver/Bronze), lifetime value by region, top customers
- **✅ Data Quality** — live data-quality gate panel (row reconciliation, null checks, uniqueness, schema validation, freshness, delta thresholds)
- **🏗️ Pipeline Health** — Medallion (Bronze/Silver/Gold) layer status, record counts, and last Airflow DAG run

Interactive filters (date range, region), downloadable data, and a polished dark theme.

---

## 🖼️ Screenshots

> _Add screenshots here after deploying (drag images into this README on GitHub)._

---

## 🧰 Tech Stack

- **Frontend / App:** Streamlit
- **Charts:** Plotly
- **Data:** Pandas, NumPy
- **Upstream pipeline:** PySpark · Delta Lake · dbt · Apache Airflow

> For this hosted demo the data is generated deterministically in-memory so the app is fully self-contained. In production the dashboard reads directly from the Gold Delta tables / dbt marts created by the pipeline.

---

## 🚀 Run Locally

```bash
git clone https://github.com/adityayadav97/retail-analytics-dashboard.git
cd retail-analytics-dashboard
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open http://localhost:8501

---

## 🔗 Related

- **Batch pipeline:** [retail-lakehouse-pipeline](https://github.com/adityayadav97/retail-lakehouse-pipeline)
- **Streaming pipeline:** [realtime-events-pipeline](https://github.com/adityayadav97/realtime-events-pipeline)

---

## 📜 License

MIT © Aditya Yadav
