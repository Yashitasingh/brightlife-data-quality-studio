import pandas as pd
import re


def compare_schema(raw_columns, reference_columns):

    extra_columns = list(
        set(raw_columns) - set(reference_columns)
    )

    missing_columns = list(
        set(reference_columns) - set(raw_columns)
    )

    return {
        "extra_columns": extra_columns,
        "missing_columns": missing_columns
    }


def detect_null_violations(raw_df, required_columns):

    null_issues = []

    for column in required_columns:

        if column in raw_df.columns:

            null_count = raw_df[column].isna().sum()

            blank_count = (
                raw_df[column]
                .astype(str)
                .str.strip()
                .eq("")
                .sum()
            )

            total_missing = int(
                null_count + blank_count
            )

            if total_missing > 0:

                null_issues.append({
                    "column": column,
                    "missing_count": total_missing,
                    "issue_type": "null_violation"
                })

    return null_issues


def detect_duplicate_keys(raw_df, key_column):

    if key_column not in raw_df.columns:

        return {
            "key_column": key_column,
            "duplicate_count": 0,
            "duplicate_values": [],
            "issue_type": "duplicate_key"
        }

    duplicate_rows = raw_df[
        raw_df.duplicated(
            subset=[key_column],
            keep=False
        )
    ]

    duplicate_values = (
        duplicate_rows[key_column]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    return {

        "key_column": key_column,

        "duplicate_count":
        len(duplicate_rows),

        "duplicate_values":
        duplicate_values,

        "issue_type":
        "duplicate_key"
    }


def detect_domain_violations(raw_df, domain_rules):

    domain_issues = []

    for column, rules in domain_rules.items():

        if column not in raw_df.columns:
            continue

        valid_codes = rules["valid"]

        normalization_map = rules["normalize"]

        values = (
            raw_df[column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        needs_normalization = {}

        invalid_values = []

        for value in values.unique():

            lower_value = value.lower()

            if value in valid_codes:
                continue

            elif lower_value in normalization_map:

                needs_normalization[value] = (
                    normalization_map[lower_value]
                )

            else:

                invalid_values.append(value)

        domain_issues.append({

            "column": column,

            "needs_normalization":
            needs_normalization,

            "invalid_values":
            invalid_values,

            "issue_type":
            "out_of_domain"
        })

    return domain_issues


def detect_format_inconsistencies(raw_df):

    format_issues = []

    email_pattern = (
        r"^[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\."
        r"[A-Za-z]{2,}$"
    )

    if "email" in raw_df.columns:

        email_values = (
            raw_df["email"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        invalid_emails = email_values[
            ~email_values.str.match(
                email_pattern
            )
        ]

        if len(invalid_emails) > 0:

            format_issues.append({
                "column": "email",
                "issue":
                "invalid_email_format",

                "affected_count":
                int(len(invalid_emails)),

                "sample_values":
                invalid_emails
                .head(10)
                .tolist(),

                "issue_type":
                "format_inconsistency"
            })

    if "phone" in raw_df.columns:

        phone_values = (
            raw_df["phone"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        phone_digits = (
            phone_values
            .str.replace(
                r"[^0-9]",
                "",
                regex=True
            )
        )

        invalid_phones = phone_values[
            (phone_digits.str.len() < 10) |
            (phone_digits.str.len() > 12) |
            (phone_values.str.contains(
                r"E\+",
                regex=True
            )) |
            (phone_values.str.contains(
                r"[().\s]",
                regex=True
            ))
        ]

        if len(invalid_phones) > 0:

            format_issues.append({

                "column":"phone",

                "issue":
                "invalid_or_non_standard_phone_format",

                "affected_count":
                int(len(invalid_phones)),

                "sample_values":
                invalid_phones
                .head(10)
                .tolist(),

                "issue_type":
                "format_inconsistency"
            })

    if "signup_date" in raw_df.columns:

        date_values = (
            raw_df["signup_date"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        parsed_dates = pd.to_datetime(
            date_values,
            errors="coerce",
            dayfirst=True
        )

        inconsistent_dates = date_values[
            parsed_dates.isna()
        ]

        if len(inconsistent_dates) > 0:

            format_issues.append({

                "column":
                "signup_date",

                "issue":
                "non_standard_date_format",

                "expected_format":
                "YYYY-MM-DD",

                "affected_count":
                int(
                    len(
                        inconsistent_dates
                    )
                ),

                "sample_values":
                inconsistent_dates
                .head(10)
                .tolist(),

                "issue_type":
                "format_inconsistency"
            })

    for column in [
        "full_name",
        "city"
    ]:

        if column in raw_df.columns:

            values = (
                raw_df[column]
                .dropna()
                .astype(str)
            )

            messy_values = values[
                (values != values.str.strip()) |
                (values.str.contains(
                    r"\s{2,}",
                    regex=True
                )) |
                (values.str.isupper()) |
                (values.str.islower())
            ]

            if len(messy_values) > 0:

                format_issues.append({

                    "column":column,

                    "issue":
                    "spacing_or_casing_inconsistency",

                    "affected_count":
                    int(len(messy_values)),

                    "sample_values":
                    messy_values
                    .head(10)
                    .tolist(),

                    "issue_type":
                    "format_inconsistency"
                })

    return format_issues


def detect_type_drift(raw_df):

    type_rules = {

        "customer_id":"string",
        "email":"string",
        "full_name":"string",
        "phone":"phone",
        "country":"string",
        "city":"string",
        "segment":"string",
        "is_active":"boolean"
    }

    type_issues=[]

    for column,expected_type in type_rules.items():

        if column not in raw_df.columns:
            continue

        values=(
            raw_df[column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        if expected_type=="boolean":

            valid_boolean_values=[

                "TRUE","FALSE",
                "true","false",
                "True","False",
                "Y","N",
                "yes","no",
                "1","0"
            ]

            invalid_values=values[
                ~values.isin(
                    valid_boolean_values
                )
            ]

        elif expected_type=="phone":

            digits=values.str.replace(
                r"[^0-9]",
                "",
                regex=True
            )

            invalid_values=values[
                (digits.str.len()<10) |
                (digits.str.len()>12)
            ]

        else:

            invalid_values=values[
                values.eq("")
            ]

        if len(
            invalid_values
        )>0:

            type_issues.append({

                "column":
                column,

                "expected_type":
                expected_type,

                "affected_count":
                int(
                    len(
                        invalid_values
                    )
                ),

                "sample_values":
                invalid_values
                .head(10)
                .tolist(),

                "issue_type":
                "type_drift"
            })

    return type_issues