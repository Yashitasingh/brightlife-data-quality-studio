import json
import pandas as pd
import requests
import streamlit as st


# ================= CONFIG =================

API_BASE_URL = "http://127.0.0.1:8000"
LOAD_DATA_URL = f"{API_BASE_URL}/load-data"
VALIDATE_RECORD_URL = f"{API_BASE_URL}/validate-record"
DOWNLOAD_CSV_URL = f"{API_BASE_URL}/download-cleaned-csv"


# ================= PAGE SETUP =================

st.set_page_config(
    page_title="BrightLife Data Quality Studio",
    layout="wide"
)

st.title("BrightLife Data Quality & SQL Repair Studio")
st.caption(
    "Raw customer data profiling, issue detection, SQL repair generation, DuckDB validation, and manual record cleaning."
)


# ================= API LOAD =================

response = requests.get(
    LOAD_DATA_URL
)

data = response.json()


# ================= TOP METRICS =================

total_nulls = sum(
    issue["missing_count"]
    for issue in data["null_issues"]
)

total_format = sum(
    issue["affected_count"]
    for issue in data["format_issues"]
)

total_duplicates = data["duplicate_issues"]["duplicate_count"]

total_sql = len(
    data["sql_fixes"]
)

passed_sql = sum(
    1
    for value in data["sql_validation"].values()
    if value["status"] == "passed"
)

health_score = max(
    0,
    100
    - min(20, total_duplicates)
    - min(20, total_nulls)
    - min(20, total_format // 3)
)

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Raw Rows",
    data["raw_rows"]
)

c2.metric(
    "Reference Rows",
    data["reference_rows"]
)

c3.metric(
    "Health Score",
    f"{health_score}/100"
)

c4.metric(
    "Issues Found",
    total_nulls + total_format + total_duplicates
)

c5.metric(
    "SQL Validated",
    f"{passed_sql}/{total_sql}"
)

st.divider()


# ================= TABS =================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Overview",
        "Issues Report",
        "Cleaned Data",
        "SQL Repair Studio",
        "Manual Validation",
        "Download Report"
    ]
)


# ================= TAB 1: OVERVIEW =================

with tab1:

    st.subheader("Executive Summary")

    if passed_sql == total_sql:
        st.success(
            "DuckDB validation completed successfully for all generated SQL fixes."
        )
    else:
        st.warning(
            "Some generated SQL fixes need review."
        )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### Schema-Level Issues")

        st.write(
            f"Extra Columns: `{data['schema_issues']['extra_columns']}`"
        )

        st.write(
            f"Missing Columns: `{data['schema_issues']['missing_columns']}`"
        )

    with col2:

        st.markdown("### Content-Level Issues")

        st.write(
            f"Null Values: `{total_nulls}`"
        )

        st.write(
            f"Duplicate Rows: `{total_duplicates}`"
        )

        st.write(
            f"Format Issues: `{total_format}`"
        )

    st.markdown("### Data Repair Examples")

    examples = [
        {
            "Issue Type": "Country Normalization",
            "Before": "India",
            "After": "IN"
        },
        {
            "Issue Type": "Segment Correction",
            "Before": "enterprize",
            "After": "enterprise"
        },
        {
            "Issue Type": "Boolean Standardization",
            "Before": "yes",
            "After": "TRUE"
        },
        {
            "Issue Type": "Phone Cleanup",
            "Before": "(+91) 8943640872",
            "After": "+91-8943640872"
        },
        {
            "Issue Type": "Name Formatting",
            "Before": "ANAYA KUMAR",
            "After": "Anaya Kumar"
        },
        {
            "Issue Type": "City Formatting",
            "Before": " hyderabad",
            "After": "Hyderabad"
        },
        {
            "Issue Type": "Duplicate Removal",
            "Before": "2 rows with C200371",
            "After": "1 unique record retained"
        },
        {
            "Issue Type": "Schema Alignment",
            "Before": "notes column present",
            "After": "removed to match reference schema"
        }
    ]

    st.dataframe(
        pd.DataFrame(examples),
        use_container_width=True
    )


# ================= TAB 2: ISSUES REPORT =================

with tab2:

    st.subheader("Detailed Issues Report")

    st.markdown("### Null Violations")

    st.dataframe(
        pd.DataFrame(data["null_issues"]),
        use_container_width=True
    )

    st.markdown("### Duplicate Keys")

    st.json(
        data["duplicate_issues"]
    )

    st.markdown("### Domain Normalization")

    st.json(
        data["domain_issues"]
    )

    st.markdown("### Format Inconsistencies")

    st.dataframe(
        pd.DataFrame(data["format_issues"]),
        use_container_width=True
    )


# ================= TAB 3: CLEANED DATA =================

with tab3:

    st.subheader("Corrected Data Preview")

    st.info(
        "Preview shows cleaned output aligned with the reference schema. The raw `notes` column is removed because it is not part of the reference schema."
    )

    clean_df = pd.DataFrame(
        data["clean_preview"]
    )

    st.dataframe(
        clean_df,
        use_container_width=True,
        height=500
    )


# ================= TAB 4: SQL REPAIR STUDIO =================

with tab4:

    st.subheader("Generated SQL Fixes")

    for fix_name, sql in data["sql_fixes"].items():

        status = data["sql_validation"][fix_name]["status"]

        if status == "passed":

            st.success(
                f"{fix_name} | DuckDB validation passed"
            )

        else:

            st.error(
                f"{fix_name} | DuckDB validation failed"
            )

        st.code(
            sql,
            language="sql"
        )


# ================= TAB 5: MANUAL VALIDATION =================

with tab5:

    st.subheader("Manual Record Validation")

    st.caption(
        "Enter one customer record and validate it using the same backend cleaning rules used for the full CSV."
    )

    with st.form("manual_record_form"):

        col1, col2 = st.columns(2)

        with col1:

            customer_id = st.text_input(
                "Customer ID",
                "C999999"
            )

            email = st.text_input(
                "Email",
                "test@@gmail.com"
            )

            full_name = st.text_input(
                "Full Name",
                "NAVYA KAPOOR89"
            )

            phone = st.text_input(
                "Phone",
                "(+91) 98765 43210"
            )

            signup_date = st.text_input(
                "Signup Date",
                "2025/05/20"
            )

        with col2:

            country = st.text_input(
                "Country",
                "India"
            )

            city = st.text_input(
                "City",
                " delhi"
            )

            segment = st.text_input(
                "Segment",
                "primium"
            )

            is_active = st.text_input(
                "Is Active",
                "yes"
            )

        submitted = st.form_submit_button(
            "Validate Record"
        )

    if submitted:

        record = {
            "customer_id": customer_id.strip() or None,
            "email": email.strip() or None,
            "full_name": full_name.strip() or None,
            "phone": phone.strip() or None,
            "signup_date": signup_date.strip() or None,
            "country": country.strip() or None,
            "city": city.strip() or None,
            "segment": segment.strip() or None,
            "is_active": is_active.strip() or None
        }

        validation_response = requests.post(
            VALIDATE_RECORD_URL,
            json=record
        )

        if validation_response.status_code != 200:

            st.error(
                "Backend validation failed. Please check the FastAPI terminal."
            )

            st.code(
                validation_response.text
            )

        else:

            result = validation_response.json()

            input_record = result["input_record"]
            corrected_record = result["corrected_record"]

            st.markdown("### Input Record")

            st.dataframe(
                pd.DataFrame([input_record]),
                use_container_width=True
            )

            st.markdown("### Corrected Record")

            st.dataframe(
                pd.DataFrame([corrected_record]),
                use_container_width=True
            )

            changes = []

            for column in corrected_record:

                original_value = input_record.get(column)
                corrected_value = corrected_record.get(column)

                if original_value != corrected_value:

                    changes.append(
                        {
                            "Column": column,
                            "Input": original_value,
                            "Corrected": corrected_value
                        }
                    )

            if changes:

                st.warning(
                    "Record needed corrections."
                )

                st.dataframe(
                    pd.DataFrame(changes),
                    use_container_width=True
                )

            else:

                st.success(
                    "Record is already valid."
                )


# ================= TAB 6: DOWNLOAD REPORT =================

with tab6:

    st.subheader("Download Generated Report")

    report_json = json.dumps(
        data,
        indent=4
    )

    st.download_button(
        label="Download Issues Report JSON",
        data=report_json,
        file_name="brightlife_issues_report.json",
        mime="application/json"
    )

    full_cleaned_csv = requests.get(
        DOWNLOAD_CSV_URL
    ).content

    st.download_button(
        label="Download Full Cleaned CSV",
        data=full_cleaned_csv,
        file_name="customers_cleaned.csv",
        mime="text/csv"
    )