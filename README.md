# BrightLife Data Quality & SQL Repair Studio

A Python-based data quality web application that loads raw and reference customer datasets, profiles issues, generates SQL repair queries, validates them using DuckDB, and produces cleaned output.

---

## Features

- Loads raw and reference datasets
- Detects schema mismatches
- Detects null violations
- Detects duplicate keys
- Detects out-of-domain values
- Detects format inconsistencies
- Detects type drift
- Generates SQL repair queries
- Validates generated SQL using DuckDB
- Provides cleaned data preview
- Downloads full cleaned CSV
- Supports manual record validation

---

## Tech Stack

- Python
- FastAPI
- Streamlit
- DuckDB
- Pandas
- Requests

---

## Project Structure

```text
brightlife-data-quality-studio/
│
├── backend/
│   └── app/
│       ├── main.py
│       ├── profiler.py
│       ├── sql_generator.py
│       ├── duckdb_runner.py
│       └── loader.py
│
├── frontend/
│   └── app.py
│
├── data/
│
├── README.md
├── LICENSE
├── requirements.txt
├── run_app.bat