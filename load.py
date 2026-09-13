import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from datetime import datetime
from transform import (
    transform_customers, transform_sellers, transform_products,
    transform_order_items, transform_payments, transform_reviews
)

load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?sslmode=require",
    pool_pre_ping=True,
    pool_recycle=300,
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

def bulk_upsert(df, temp_table, target_table, columns, conflict_cols, update_cols):
    df = df.where(pd.notnull(df), None)

    # Step 1: bulk load into temp table (fast, uses executemany internally but no ON CONFLICT overhead)
    df.to_sql(temp_table, engine, if_exists="replace", index=False, method="multi", chunksize=5000)

    # Step 2: single INSERT...SELECT...ON CONFLICT — one round trip, done server-side
    col_list = ", ".join(columns)
    update_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])
    conflict_clause = ", ".join(conflict_cols)

    sql = f"""
        INSERT INTO {target_table} ({col_list})
        SELECT {col_list} FROM {temp_table}
        ON CONFLICT ({conflict_clause}) DO UPDATE SET {update_clause}
    """
    with engine.begin() as conn:
        conn.execute(text(sql))
        conn.execute(text(f"DROP TABLE IF EXISTS {temp_table}"))

    log_run("load", target_table, len(df), 0, "success")

def run_load():
    print(f"Starting load at {datetime.now()}")

    print("  Loading dim_customers...")
    df = transform_customers()
    bulk_upsert(df, "temp_customers", "dim_customers",
                ["customer_id", "customer_unique_id", "customer_city", "customer_state", "customer_zip_code_prefix"],
                ["customer_id"],
                ["customer_unique_id", "customer_city", "customer_state", "customer_zip_code_prefix"])

    print("  Loading dim_sellers...")
    df = transform_sellers()
    bulk_upsert(df, "temp_sellers", "dim_sellers",
                ["seller_id", "seller_city", "seller_state", "seller_zip_code_prefix"],
                ["seller_id"],
                ["seller_city", "seller_state", "seller_zip_code_prefix"])

    print("  Loading dim_products...")
    df = transform_products()
    bulk_upsert(df, "temp_products", "dim_products",
                ["product_id", "product_category_name", "product_category_name_english",
                 "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"],
                ["product_id"],
                ["product_category_name", "product_category_name_english",
                 "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"])

    print("  Loading fact_order_items...")
    df = transform_order_items()
    bulk_upsert(df, "temp_order_items", "fact_order_items",
                ["order_id", "order_item_id", "customer_id", "product_id", "seller_id",
                 "order_purchase_date_id", "order_status", "price", "freight_value", "delivery_delay_days"],
                ["order_id", "order_item_id"],
                ["order_status", "price", "freight_value", "delivery_delay_days"])

    print("  Loading fact_payments...")
    df = transform_payments()
    bulk_upsert(df, "temp_payments", "fact_payments",
                ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"],
                ["order_id", "payment_sequential"],
                ["payment_type", "payment_installments", "payment_value"])

    print("  Loading fact_reviews...")
    df = transform_reviews()
    bulk_upsert(df, "temp_reviews", "fact_reviews",
                ["review_id", "order_id", "review_score", "has_comment"],
                ["review_id"],
                ["review_score", "has_comment"])

    print("Load complete.")

if __name__ == "__main__":
    run_load()
