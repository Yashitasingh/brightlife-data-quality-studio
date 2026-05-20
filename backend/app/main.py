# ================= IMPORTS =================

from fastapi import FastAPI
from fastapi.responses import Response
import pandas as pd
import math
from pydantic import BaseModel

from backend.app.loader import load_raw_data, load_reference_data

from backend.app.profiler import (
    compare_schema,
    detect_null_violations,
    detect_duplicate_keys,
    detect_domain_violations,
    detect_format_inconsistencies,
    detect_type_drift
)

from backend.app.sql_generator import (
    generate_sql_fixes,
    generate_master_cleaning_sql
)

from backend.app.duckdb_runner import (
    validate_sql_queries,
    generate_clean_preview,
    generate_full_clean_data
)


# ================= APP =================

app = FastAPI(
    title="BrightLife Data Quality Studio"
)
class CustomerRecord(BaseModel):
    customer_id: str
    email: str | None = None
    full_name: str | None = None
    phone: str | None = None
    signup_date: str | None = None
    country: str | None = None
    city: str | None = None
    segment: str | None = None
    is_active: str | None = None


# ================= JSON SANITIZER =================
# converts NaN / inf into JSON-safe values

def sanitize_for_json(value):

    if isinstance(value, float):

        if math.isnan(value) or math.isinf(value):
            return None

        return value

    if isinstance(value, dict):

        return {
            key: sanitize_for_json(item)
            for key, item in value.items()
        }

    if isinstance(value, list):

        return [
            sanitize_for_json(item)
            for item in value
        ]

    return value


# ================= HOME =================

@app.get("/")
def home():

    return {
        "message": "Backend is alive 🚀"
    }


# ================= MAIN REPORT API =================

@app.get("/load-data")
def load_data():

    raw = load_raw_data()

    reference = load_reference_data()


    # schema issues

    schema_issues = compare_schema(
        raw.columns.tolist(),
        reference.columns.tolist()
    )


    # null issues

    null_issues = detect_null_violations(
        raw,
        reference.columns.tolist()
    )


    # duplicate issues

    duplicate_issues = detect_duplicate_keys(
        raw,
        "customer_id"
    )


    # domain rules

    domain_rules = {

        "country": {

            "valid": [
                "IN",
                "US",
                "UK",
                "AE",
                "SG"
            ],

            "normalize": {

                "india": "IN",
                "in": "IN",
                "usa": "US",
                "united states": "US",
                "u.k.": "UK",
                "uk": "UK",
                "united kingdom": "UK",
                "uae": "AE",
                "united arab emirates": "AE",
                "singapore": "SG"
            }
        },

        "segment": {

            "valid": [
                "retail",
                "premium",
                "enterprise"
            ],

            "normalize": {

                "retail": "retail",
                "premium": "premium",
                "enterprise": "enterprise",
                "enterprize": "enterprise",
                "primium": "premium"
            }
        },

        "is_active": {

            "valid": [
                "TRUE",
                "FALSE"
            ],

            "normalize": {

                "true": "TRUE",
                "false": "FALSE",
                "yes": "TRUE",
                "y": "TRUE",
                "1": "TRUE",
                "no": "FALSE",
                "n": "FALSE",
                "0": "FALSE"
            }
        }
    }


    # domain issues

    domain_issues = detect_domain_violations(
        raw,
        domain_rules
    )


    # format issues

    format_issues = detect_format_inconsistencies(
        raw
    )


    # type issues

    type_issues = detect_type_drift(
        raw
    )


    # sql generation

    sql_fixes = generate_sql_fixes()


    # sql validation

    sql_validation = validate_sql_queries(
        raw,
        sql_fixes
    )


    # cleaned preview

    master_sql = generate_master_cleaning_sql()

    clean_preview = generate_clean_preview(
        raw,
        master_sql
    )


    # response object

    response_data = {

        "raw_rows": len(raw),

        "reference_rows": len(reference),

        "schema_issues": schema_issues,

        "null_issues": null_issues,

        "duplicate_issues": duplicate_issues,

        "domain_issues": domain_issues,

        "format_issues": format_issues,

        "type_issues": type_issues,

        "sql_fixes": sql_fixes,

        "sql_validation": sql_validation,

        "clean_preview": clean_preview
    }


    return sanitize_for_json(
        response_data
    )


# ================= DOWNLOAD CLEANED CSV =================

@app.get("/download-cleaned-csv")
def download_cleaned_csv():

    raw = load_raw_data()

    master_sql = generate_master_cleaning_sql()

    cleaned_data = generate_full_clean_data(
        raw,
        master_sql
    )

    cleaned_df = pd.DataFrame(
        cleaned_data
    )

    cleaned_df = cleaned_df.fillna("NULL")

    cleaned_df["phone"] = cleaned_df["phone"].apply(
        lambda value: f'="{value}"'
        if value != "NULL"
        else "NULL"
    )

    csv_data = cleaned_df.to_csv(
        index=False,
        na_rep="NULL"
    )

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=customers_cleaned.csv"
        }
    )

@app.post("/validate-record")
def validate_record(record: CustomerRecord):

    raw = pd.DataFrame(
        [record.model_dump()]
    )

    master_sql = generate_master_cleaning_sql()

    cleaned_data = generate_full_clean_data(
        raw,
        master_sql
    )

    return {
        "input_record": record.model_dump(),
        "corrected_record": cleaned_data[0]
    }