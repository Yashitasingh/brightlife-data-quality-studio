def generate_sql_fixes():

    sql_fixes = {}

    # ================= SCHEMA FIX =================

    sql_fixes["schema_fix"] = """
    SELECT
        customer_id,
        email,
        full_name,
        phone,
        signup_date,
        country,
        city,
        segment,
        is_active
    FROM raw_data;
    """

    # ================= DUPLICATE FIX =================

    sql_fixes["duplicate_fix"] = """
    SELECT *
    FROM (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY customer_id
                ORDER BY customer_id
            ) AS rn
        FROM raw_data
    )
    WHERE rn = 1;
    """

    # ================= COUNTRY FIX =================

    sql_fixes["country_normalization_fix"] = """
    SELECT
        CASE
            WHEN LOWER(TRIM(country)) IN ('india', 'in') THEN 'IN'
            WHEN LOWER(TRIM(country)) IN ('usa', 'united states') THEN 'US'
            WHEN LOWER(TRIM(country)) IN ('u.k.', 'uk', 'united kingdom') THEN 'UK'
            WHEN LOWER(TRIM(country)) IN ('uae', 'united arab emirates') THEN 'AE'
            WHEN LOWER(TRIM(country)) IN ('singapore', 'sg') THEN 'SG'
            ELSE UPPER(TRIM(country))
        END AS country
    FROM raw_data;
    """

    # ================= SEGMENT FIX =================

    sql_fixes["segment_normalization_fix"] = """
    SELECT
        CASE
            WHEN segment IS NULL OR TRIM(segment) = '' THEN NULL
            WHEN LOWER(TRIM(segment)) = 'enterprize' THEN 'enterprise'
            WHEN LOWER(TRIM(segment)) = 'primium' THEN 'premium'
            WHEN LOWER(TRIM(segment)) IN ('retail', 'premium', 'enterprise')
            THEN LOWER(TRIM(segment))
            ELSE NULL
        END AS segment
    FROM raw_data;
    """

    # ================= BOOLEAN FIX =================

    sql_fixes["boolean_normalization_fix"] = """
    SELECT
        CASE
            WHEN LOWER(TRIM(is_active)) IN ('true', 'yes', 'y', '1') THEN 'TRUE'
            WHEN LOWER(TRIM(is_active)) IN ('false', 'no', 'n', '0') THEN 'FALSE'
            ELSE NULL
        END AS is_active
    FROM raw_data;
    """

    # ================= TEXT FORMAT FIX =================

    sql_fixes["text_format_fix"] = """
    SELECT
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                TRIM(full_name),
                '[0-9]',
                '',
                'g'
            ),
            '\\s+',
            ' ',
            'g'
        ) AS full_name,

        UPPER(LEFT(TRIM(city), 1)) ||
        LOWER(SUBSTRING(TRIM(city), 2)) AS city
    FROM raw_data;
    """

    # ================= PHONE FORMAT FIX =================

    sql_fixes["phone_format_fix"] = """
    SELECT
        CASE
            WHEN phone IS NULL OR TRIM(phone) = '' THEN NULL

            WHEN LENGTH(REGEXP_REPLACE(phone, '[^0-9]', '', 'g')) = 12
                 AND LEFT(REGEXP_REPLACE(phone, '[^0-9]', '', 'g'), 2) = '91'
            THEN '+91-' || SUBSTRING(REGEXP_REPLACE(phone, '[^0-9]', '', 'g'), 3)

            WHEN LENGTH(REGEXP_REPLACE(phone, '[^0-9]', '', 'g')) = 10
            THEN '+91-' || REGEXP_REPLACE(phone, '[^0-9]', '', 'g')

            ELSE NULL
        END AS phone
    FROM raw_data;
    """

    return sql_fixes


def generate_master_cleaning_sql():

    return """
    WITH prepared AS (

        SELECT
            *,

            CASE
                WHEN phone IS NULL OR TRIM(phone) = '' THEN NULL

                WHEN REGEXP_MATCHES(
                    TRIM(phone),
                    '^[0-9]+(\\.[0-9]+)?E\\+[0-9]+$'
                )
                THEN CAST(CAST(TRIM(phone) AS DOUBLE) AS BIGINT)::VARCHAR

                ELSE REGEXP_REPLACE(
                    phone,
                    '[^0-9]',
                    '',
                    'g'
                )
            END AS phone_digits

        FROM raw_data
    )

    SELECT
        customer_id,

        -- Missing or invalid email remains NULL.

        CASE
            WHEN email IS NULL
                 OR TRIM(email) = ''
                 OR LOWER(TRIM(email)) = 'null'
            THEN NULL

            WHEN REGEXP_MATCHES(
                LOWER(TRIM(email)),
                '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'
            )
            THEN LOWER(TRIM(email))

            ELSE NULL
        END AS email,

        -- Missing full_name remains NULL.
        -- Existing full_name is cleaned, digits removed, and spacing normalized.
        -- No name is extracted from email because that would manipulate data.

        CASE
            WHEN full_name IS NULL
                 OR TRIM(full_name) = ''
                 OR LOWER(TRIM(full_name)) = 'null'
            THEN NULL

            ELSE
                REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        TRIM(full_name),
                        '[0-9]',
                        '',
                        'g'
                    ),
                    '\\s+',
                    ' ',
                    'g'
                )
        END AS full_name,

        -- Final phone format: +91-XXXXXXXXXX.
        -- Invalid or missing phone becomes NULL.

        CASE
            WHEN phone_digits IS NULL OR phone_digits = '' THEN NULL

            WHEN LENGTH(phone_digits) = 12
                 AND LEFT(phone_digits, 2) = '91'
            THEN '+91-' || SUBSTRING(phone_digits, 3)

            WHEN LENGTH(phone_digits) = 10
            THEN '+91-' || phone_digits

            WHEN LENGTH(phone_digits) > 10
            THEN '+91-' || RIGHT(phone_digits, 10)

            ELSE NULL
        END AS phone,

        -- Final date format: dd-mm-yyyy.
        -- Invalid or missing date becomes NULL.

        CASE
            WHEN signup_date IS NULL
                 OR TRIM(signup_date) = ''
                 OR LOWER(TRIM(signup_date)) = 'null'
            THEN NULL

            WHEN TRY_STRPTIME(TRIM(signup_date), '%d/%m/%Y') IS NOT NULL
            THEN STRFTIME(TRY_STRPTIME(TRIM(signup_date), '%d/%m/%Y'), '%d-%m-%Y')

            WHEN TRY_STRPTIME(TRIM(signup_date), '%m/%d/%Y') IS NOT NULL
            THEN STRFTIME(TRY_STRPTIME(TRIM(signup_date), '%m/%d/%Y'), '%d-%m-%Y')

            WHEN TRY_STRPTIME(TRIM(signup_date), '%Y/%m/%d') IS NOT NULL
            THEN STRFTIME(TRY_STRPTIME(TRIM(signup_date), '%Y/%m/%d'), '%d-%m-%Y')

            WHEN TRY_STRPTIME(TRIM(signup_date), '%d.%m.%Y') IS NOT NULL
            THEN STRFTIME(TRY_STRPTIME(TRIM(signup_date), '%d.%m.%Y'), '%d-%m-%Y')

            WHEN TRY_STRPTIME(TRIM(signup_date), '%d-%b-%Y') IS NOT NULL
            THEN STRFTIME(TRY_STRPTIME(TRIM(signup_date), '%d-%b-%Y'), '%d-%m-%Y')

            WHEN TRY_STRPTIME(TRIM(signup_date), '%d-%b-%y') IS NOT NULL
            THEN STRFTIME(TRY_STRPTIME(TRIM(signup_date), '%d-%b-%y'), '%d-%m-%Y')

            WHEN TRY_STRPTIME(TRIM(signup_date), '%Y-%m-%d') IS NOT NULL
            THEN STRFTIME(TRY_STRPTIME(TRIM(signup_date), '%Y-%m-%d'), '%d-%m-%Y')

            WHEN TRY_STRPTIME(TRIM(signup_date), '%d-%m-%Y') IS NOT NULL
            THEN STRFTIME(TRY_STRPTIME(TRIM(signup_date), '%d-%m-%Y'), '%d-%m-%Y')

            ELSE NULL
        END AS signup_date,

        -- Country is standardized into uppercase 2-letter code.

        CASE
            WHEN country IS NULL
                 OR TRIM(country) = ''
                 OR LOWER(TRIM(country)) = 'null'
            THEN NULL

            WHEN LOWER(TRIM(country)) IN ('india', 'in') THEN 'IN'
            WHEN LOWER(TRIM(country)) IN ('usa', 'united states') THEN 'US'
            WHEN LOWER(TRIM(country)) IN ('u.k.', 'uk', 'united kingdom') THEN 'UK'
            WHEN LOWER(TRIM(country)) IN ('uae', 'united arab emirates') THEN 'AE'
            WHEN LOWER(TRIM(country)) IN ('singapore', 'sg') THEN 'SG'

            WHEN REGEXP_MATCHES(TRIM(country), '^[A-Z]{2}$')
            THEN TRIM(country)

            ELSE NULL
        END AS country,

        -- Missing city remains NULL.
        -- Existing city is cleaned and normalized.

        CASE
            WHEN city IS NULL
                 OR TRIM(city) = ''
                 OR LOWER(TRIM(city)) = 'null'
            THEN NULL

            ELSE
                UPPER(LEFT(TRIM(city), 1)) ||
                LOWER(SUBSTRING(TRIM(city), 2))
        END AS city,

        -- Segment is normalized.
        -- Missing or unknown segment remains NULL.

        CASE
            WHEN segment IS NULL
                 OR TRIM(segment) = ''
                 OR LOWER(TRIM(segment)) = 'null'
            THEN NULL

            WHEN LOWER(TRIM(segment)) = 'enterprize' THEN 'enterprise'
            WHEN LOWER(TRIM(segment)) = 'primium' THEN 'premium'

            WHEN LOWER(TRIM(segment)) IN ('retail', 'premium', 'enterprise')
            THEN LOWER(TRIM(segment))

            ELSE NULL
        END AS segment,

        -- Boolean values are standardized.
        -- Unknown values remain NULL.

        CASE
            WHEN is_active IS NULL
                 OR TRIM(is_active) = ''
                 OR LOWER(TRIM(is_active)) = 'null'
            THEN NULL

            WHEN LOWER(TRIM(is_active)) IN ('true', 'yes', 'y', '1') THEN 'TRUE'
            WHEN LOWER(TRIM(is_active)) IN ('false', 'no', 'n', '0') THEN 'FALSE'

            ELSE NULL
        END AS is_active

    FROM (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY customer_id
                ORDER BY customer_id
            ) AS rn
        FROM prepared
    )
    WHERE rn = 1;
    """