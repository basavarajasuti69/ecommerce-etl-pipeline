import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

def log_run(stage, table_name, rows_processed, rows_rejected, status, notes=""):
    rows_processed = int(rows_processed)
    rows_rejected = int(rows_rejected)
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO pipeline_run_log (stage, table_name, rows_processed, rows_rejected, status, notes)
                VALUES (:stage, :table_name, :rows_processed, :rows_rejected, :status, :notes)
            """),
            {"stage": stage, "table_name": table_name, "rows_processed": rows_processed,
             "rows_rejected": rows_rejected, "status": status, "notes": notes}
        )

def transform_customers():
    df = pd.read_sql("SELECT * FROM staging_customers", engine)
    before = len(df)
    df = df.drop_duplicates(subset="customer_id")
    after = len(df)
    log_run("transform", "dim_customers", after, before - after, "success")
    return df[["customer_id", "customer_unique_id", "customer_city",
               "customer_state", "customer_zip_code_prefix"]]

def transform_sellers():
    df = pd.read_sql("SELECT * FROM staging_sellers", engine)
    before = len(df)
    df = df.drop_duplicates(subset="seller_id")
    after = len(df)
    log_run("transform", "dim_sellers", after, before - after, "success")
    return df[["seller_id", "seller_city", "seller_state", "seller_zip_code_prefix"]]

def transform_products():
    df = pd.read_sql("SELECT * FROM staging_products", engine)
    translation = pd.read_sql("SELECT * FROM staging_category_translation", engine)

    before = len(df)
    df["product_category_name"] = df["product_category_name"].fillna("unknown")

    df = df.merge(translation, on="product_category_name", how="left")
    df["product_category_name_english"] = df["product_category_name_english"].fillna("unknown")

    after = len(df)
    log_run("transform", "dim_products", after, 0, "success",
            notes="610 missing categories filled with 'unknown'")

    return df[["product_id", "product_category_name", "product_category_name_english",
               "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"]]

def transform_order_items():
    order_items = pd.read_sql("SELECT * FROM staging_order_items", engine)
    orders = pd.read_sql("SELECT * FROM staging_orders", engine)

    before = len(order_items)

    for col in ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]:
        orders[col] = pd.to_datetime(orders[col], errors="coerce")

    orders["delivery_delay_days"] = (
        orders["order_delivered_customer_date"] - orders["order_estimated_delivery_date"]
    ).dt.days

    orders["order_purchase_date_id"] = orders["order_purchase_timestamp"].dt.strftime("%Y%m%d")
    orders["order_purchase_date_id"] = pd.to_numeric(orders["order_purchase_date_id"], errors="coerce")

    merged = order_items.merge(
        orders[["order_id", "customer_id", "order_status", "order_purchase_date_id", "delivery_delay_days"]],
        on="order_id", how="left"
    )

    rejected = int(merged["order_purchase_date_id"].isna().sum())
    merged = merged.dropna(subset=["order_purchase_date_id"])
    merged["order_purchase_date_id"] = merged["order_purchase_date_id"].astype(int)

    after = len(merged)
    log_run("transform", "fact_order_items", after, rejected, "success")

    return merged[["order_id", "order_item_id", "customer_id", "product_id", "seller_id",
                   "order_purchase_date_id", "order_status", "price", "freight_value",
                   "delivery_delay_days"]]

def transform_payments():
    df = pd.read_sql("SELECT * FROM staging_payments", engine)
    before = len(df)
    df = df.drop_duplicates(subset=["order_id", "payment_sequential"])
    after = len(df)
    log_run("transform", "fact_payments", after, before - after, "success")
    return df[["order_id", "payment_sequential", "payment_type",
               "payment_installments", "payment_value"]]

def transform_reviews():
    df = pd.read_sql("SELECT * FROM staging_reviews", engine)
    before = len(df)
    df = df.drop_duplicates(subset="review_id")
    df["has_comment"] = df["review_comment_message"].notna()
    after = len(df)
    log_run("transform", "fact_reviews", after, before - after, "success")
    return df[["review_id", "order_id", "review_score", "has_comment"]]

def run_all():
    print(f"Starting transform at {datetime.now()}")
    results = {
        "dim_customers": transform_customers(),
        "dim_sellers": transform_sellers(),
        "dim_products": transform_products(),
        "fact_order_items": transform_order_items(),
        "fact_payments": transform_payments(),
        "fact_reviews": transform_reviews(),
    }
    for name, df in results.items():
        print(f"  {name}: {len(df)} rows ready")
    print("Transform complete.")
    return results

if __name__ == "__main__":
    run_all()
