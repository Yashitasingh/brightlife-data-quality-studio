import pandas as pd


RAW_DATA_PATH = "data/raw/customers_raw (1).csv"
REFERENCE_DATA_PATH = "data/reference/customers_reference (1).csv"


def load_raw_data():
    return pd.read_csv(RAW_DATA_PATH)


def load_reference_data():
    return pd.read_csv(REFERENCE_DATA_PATH)