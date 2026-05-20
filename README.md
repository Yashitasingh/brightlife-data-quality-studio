# BrightLife Data Quality & SQL Repair Studio

BrightLife Data Quality & SQL Repair Studio is a Python-based web application that profiles raw customer data against a reference dataset, detects data quality issues, generates SQL repair queries, validates those queries using DuckDB, and produces cleaned output for download.

The project acts as a lightweight data quality assistant where users can inspect detected issues, understand generated SQL repairs, validate corrected records, and download cleaned datasets through an interactive interface.

---

## Key Features

- Loads raw and reference datasets
- Profiles raw data against reference schema
- Separates schema-level and content-level issues
- Detects schema mismatches
- Detects type drift
- Detects null violations
- Detects duplicate keys
- Detects out-of-domain values
- Detects format inconsistencies
- Generates SQL repair queries for every issue category
- Validates generated SQL using DuckDB
- Displays cleaned data preview
- Supports full cleaned CSV download
- Supports manual single-record validation
- Generates downloadable issues report

---

## Tech Stack

- Python
- FastAPI
- Streamlit
- DuckDB
- Pandas
- Requests
- Pydantic

---

## Project Structure

```text
brightlife-data-quality-studio/
│
├── backend/
│   └── app/
│       ├── main.py
│       ├── loader.py
│       ├── profiler.py
│       ├── sql_generator.py
│       └── duckdb_runner.py
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
└── .gitignore
```

---

## Application Workflow

```text
Raw Dataset + Reference Dataset
            ↓
     Data Profiling
            ↓
     Issue Detection
            ↓
    SQL Generation
            ↓
   DuckDB Validation
            ↓
Cleaned Output + Reports
```

---

## Detected Issue Categories

### Schema-Level Issues

Schema-level issues compare the raw dataset structure with the reference dataset.

Detected issues:

- Extra columns
- Missing columns

Example:

```text
Extra column detected: notes
```

---

### Content-Level Issues

Content-level issues inspect values inside records.

Detected issues:

- Null violations
- Duplicate keys
- Type drift
- Out-of-domain values
- Format inconsistencies

Examples:

```text
Country: India → IN
Segment: primium → premium
Boolean: yes → TRUE
Phone: (+91)9876543210 → +91-9876543210
Date: 2025/05/20 → 20-05-2025
```

---

## SQL Repair Generation

For each issue category, SQL repair queries are automatically generated.

Examples include:

- Duplicate removal
- Schema alignment
- Country normalization
- Segment correction
- Date formatting
- Phone normalization
- Text cleanup
- Boolean standardization

Generated SQL follows DuckDB-compatible syntax.

---

## DuckDB Validation

All generated SQL repair queries are executed against the raw dataset using DuckDB.

Validation results:

```text
DuckDB validation passed
```

If SQL execution fails, the generated error is returned.

This ensures all generated SQL is executable.

---

## Cleaned Output Rules

| Field | Rule |
|---|---|
| customer_id | preserved |
| email | invalid values become NULL |
| full_name | digits removed + capitalization fixed |
| phone | converted to +91-XXXXXXXXXX |
| signup_date | converted to dd-mm-yyyy |
| country | standardized country code |
| city | trimmed and title-cased |
| segment | normalized values |
| is_active | TRUE/FALSE standardized |

Missing values remain NULL.

No artificial values are generated.

---

## Manual Record Validation

Users can manually validate individual records.

Example input:

```text
email=test@@gmail.com
full_name=NAVYA KAPOOR89
phone=(+91)9876543210
country=India
segment=primium
is_active=yes
```

Output:

- original record
- corrected record
- before-vs-after comparison

This demonstrates real-time data cleaning.

---

## Setup

Clone repository:

```bash
git clone https://github.com/Yashitasingh/brightlife-data-quality-studio.git
cd brightlife-data-quality-studio
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Run With Single Command

```bash
run_app.bat
```

This launches:

- FastAPI backend
- Streamlit frontend

---

## Manual Run

Terminal 1:

```bash
uvicorn backend.app.main:app --reload
```

Terminal 2:

```bash
streamlit run frontend/app.py
```

---

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /load-data | profiles dataset and returns report |
| GET | /download-cleaned-csv | downloads cleaned dataset |
| POST | /validate-record | validates individual record |

---

## Generated Outputs

- Issues Report JSON
- Cleaned CSV
- SQL Repair Scripts
- DuckDB Validation Results
- Corrected Preview Data

---

## Adding a New Issue Type

The system follows a modular issue-detection approach.

Steps:

1. Create a detector function in:

```text
backend/app/profiler.py
```

2. Add SQL repair logic in:

```text
backend/app/sql_generator.py
```

3. Add frontend visualization in:

```text
frontend/app.py
```

This keeps issue detection extensible without rewriting the existing profiling workflow.

Future issue examples:

- postal code validation
- negative numeric values
- invalid currency format
- invalid ID patterns

---

## Repository Readiness

Repository includes:

- README
- Requirements file
- License
- Git ignore
- Single-command launcher
- Backend source
- Frontend source

The repository is structured so it can be released under an OSI-approved license.


---

## Author

Yashita Singh