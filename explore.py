import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")

files = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "products": "olist_products_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

dataframes = {}

for name, filename in files.items():
    df = pd.read_csv(RAW_DIR / filename)
    dataframes[name] = df

    print(f"\n{'='*60}")
    print(f"TABLE: {name}  ({filename})")
    print(f"{'='*60}")
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"\nColumns & dtypes:")
    print(df.dtypes)
    print(f"\nNull counts (non-zero only):")
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    print(nulls if not nulls.empty else "  none")
    print(f"\nSample rows:")
    print(df.head(3))
