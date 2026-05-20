import duckdb
import pandas as pd
import numpy as np


# ================= SQL VALIDATION =================
# Runs every generated SQL query inside DuckDB.
# If query executes, status = passed.
# If query fails, error message is returned.

def validate_sql_queries(raw_df, sql_fixes):

    validation_results = {}

    connection = duckdb.connect(
        database=":memory:"
    )

    connection.register(
        "raw_data",
        raw_df
    )

    for fix_name, sql_query in sql_fixes.items():

        try:

            connection.execute(
                sql_query
            ).fetchdf()

            validation_results[fix_name] = {
                "status": "passed",
                "message": "SQL executed successfully in DuckDB"
            }

        except Exception as error:

            validation_results[fix_name] = {
                "status": "failed",
                "message": str(error)
            }

    connection.close()

    return validation_results


# ================= NAME TITLE CASE HELPER =================
# Capitalizes every word.
# Keeps missing names as None, not Unknown.
# Example:
# navya kapoor -> Navya Kapoor
# ROHAN IYER -> Rohan Iyer
# ravi89 kumar -> Ravi Kumar
# NULL / NaN -> None

def title_case_name(value):

    if pd.isna(value):
        return None

    value = str(value).strip()

    if (
        value == ""
        or value.lower() == "null"
        or value.lower() == "nan"
    ):
        return None

    value = "".join(
        character
        for character in value
        if not character.isdigit()
    )

    value = " ".join(
        value.split()
    )

    if value == "":
        return None

    return " ".join(
        word.capitalize()
        for word in value.split()
    )


# ================= DATAFRAME CLEANUP HELPER =================
# Applies final frontend/download-safe cleanup.
# This runs after DuckDB SQL cleaning.

def finalize_cleaned_dataframe(cleaned_df):

    cleaned_df = cleaned_df.replace(
        [np.inf, -np.inf],
        np.nan
    )

    cleaned_df = cleaned_df.where(
        pd.notnull(cleaned_df),
        None
    )

    if "full_name" in cleaned_df.columns:

        cleaned_df["full_name"] = cleaned_df["full_name"].apply(
            title_case_name
        )

    cleaned_df = cleaned_df.where(
        pd.notnull(cleaned_df),
        None
    )

    return cleaned_df


# ================= CLEAN PREVIEW =================
# Returns first 20 cleaned records for Streamlit preview.

def generate_clean_preview(raw_df, master_sql):

    connection = duckdb.connect(
        database=":memory:"
    )

    connection.register(
        "raw_data",
        raw_df
    )

    cleaned_df = connection.execute(
        master_sql
    ).fetchdf()

    connection.close()

    cleaned_df = finalize_cleaned_dataframe(
        cleaned_df
    )

    return cleaned_df.head(
        20
    ).to_dict(
        orient="records"
    )


# ================= FULL CLEAN DATA =================
# Returns all cleaned records for CSV download.

def generate_full_clean_data(raw_df, master_sql):

    connection = duckdb.connect(
        database=":memory:"
    )

    connection.register(
        "raw_data",
        raw_df
    )

    cleaned_df = connection.execute(
        master_sql
    ).fetchdf()

    connection.close()

    cleaned_df = finalize_cleaned_dataframe(
        cleaned_df
    )

    return cleaned_df.to_dict(
        orient="records"
    )