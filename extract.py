import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

RAW_DIR = Path("data/raw")

files = {
    "staging_customers": "olist_customers_dataset.csv",
    "staging_orders": "olist_orders_dataset.csv",
    "staging_order_items": "olist_order_items_dataset.csv",
    "staging_products": "olist_products_dataset.csv",
    "staging_payments": "olist_order_payments_dataset.csv",
    "staging_reviews": "olist_order_reviews_dataset.csv",
    "staging_sellers": "olist_sellers_dataset.csv",
    "staging_geolocation": "olist_geolocation_dataset.csv",
    "staging_category_translation": "product_category_name_translation.csv",
}

def log_run(stage, table_name, rows_processed, status, notes=""):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO pipeline_run_log (stage, table_name, rows_processed, rows_rejected, status, notes)
                VALUES (:stage, :table_name, :rows_processed, 0, :status, :notes)
            """),
            {"stage": stage, "table_name": table_name, "rows_processed": rows_processed,
             "status": status, "notes": notes}
        )

def extract():
    print(f"Starting extraction at {datetime.now()}")
    total_rows = 0

    for table_name, filename in files.items():
        filepath = RAW_DIR / filename
        try:
            df = pd.read_csv(filepath)
            df.to_sql(table_name, engine, if_exists="replace", index=False)
            row_count = len(df)
            total_rows += row_count
            print(f"  {table_name}: {row_count} rows loaded")
            log_run("extract", table_name, row_count, "success")
        except Exception as e:
            print(f"  ERROR loading {table_name}: {e}")
            log_run("extract", table_name, 0, "failed", notes=str(e))

    print(f"\nExtraction complete. Total rows loaded: {total_rows}")

if __name__ == "__main__":
    extract()
