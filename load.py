import pandas as pd
import math
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
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

def clean_row(row_dict):
    return {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in row_dict.items()}

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

def upsert_dim_customers(df):
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO dim_customers (customer_id, customer_unique_id, customer_city, customer_state, customer_zip_code_prefix)
                VALUES (:customer_id, :customer_unique_id, :customer_city, :customer_state, :customer_zip_code_prefix)
                ON CONFLICT (customer_id) DO UPDATE SET
                    customer_unique_id = EXCLUDED.customer_unique_id,
                    customer_city = EXCLUDED.customer_city,
                    customer_state = EXCLUDED.customer_state,
                    customer_zip_code_prefix = EXCLUDED.customer_zip_code_prefix
            """), clean_row(row.to_dict()))
    log_run("load", "dim_customers", len(df), 0, "success")

def upsert_dim_sellers(df):
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO dim_sellers (seller_id, seller_city, seller_state, seller_zip_code_prefix)
                VALUES (:seller_id, :seller_city, :seller_state, :seller_zip_code_prefix)
                ON CONFLICT (seller_id) DO UPDATE SET
                    seller_city = EXCLUDED.seller_city,
                    seller_state = EXCLUDED.seller_state,
                    seller_zip_code_prefix = EXCLUDED.seller_zip_code_prefix
            """), clean_row(row.to_dict()))
    log_run("load", "dim_sellers", len(df), 0, "success")

def upsert_dim_products(df):
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO dim_products (product_id, product_category_name, product_category_name_english,
                    product_weight_g, product_length_cm, product_height_cm, product_width_cm)
                VALUES (:product_id, :product_category_name, :product_category_name_english,
                    :product_weight_g, :product_length_cm, :product_height_cm, :product_width_cm)
                ON CONFLICT (product_id) DO UPDATE SET
                    product_category_name = EXCLUDED.product_category_name,
                    product_category_name_english = EXCLUDED.product_category_name_english,
                    product_weight_g = EXCLUDED.product_weight_g,
                    product_length_cm = EXCLUDED.product_length_cm,
                    product_height_cm = EXCLUDED.product_height_cm,
                    product_width_cm = EXCLUDED.product_width_cm
            """), clean_row(row.to_dict()))
    log_run("load", "dim_products", len(df), 0, "success")

def upsert_fact_order_items(df):
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO fact_order_items (order_id, order_item_id, customer_id, product_id, seller_id,
                    order_purchase_date_id, order_status, price, freight_value, delivery_delay_days)
                VALUES (:order_id, :order_item_id, :customer_id, :product_id, :seller_id,
                    :order_purchase_date_id, :order_status, :price, :freight_value, :delivery_delay_days)
                ON CONFLICT (order_id, order_item_id) DO UPDATE SET
                    order_status = EXCLUDED.order_status,
                    price = EXCLUDED.price,
                    freight_value = EXCLUDED.freight_value,
                    delivery_delay_days = EXCLUDED.delivery_delay_days
            """), clean_row(row.to_dict()))
    log_run("load", "fact_order_items", len(df), 0, "success")

def upsert_fact_payments(df):
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO fact_payments (order_id, payment_sequential, payment_type, payment_installments, payment_value)
                VALUES (:order_id, :payment_sequential, :payment_type, :payment_installments, :payment_value)
                ON CONFLICT (order_id, payment_sequential) DO UPDATE SET
                    payment_type = EXCLUDED.payment_type,
                    payment_installments = EXCLUDED.payment_installments,
                    payment_value = EXCLUDED.payment_value
            """), clean_row(row.to_dict()))
    log_run("load", "fact_payments", len(df), 0, "success")

def upsert_fact_reviews(df):
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO fact_reviews (review_id, order_id, review_score, has_comment)
                VALUES (:review_id, :order_id, :review_score, :has_comment)
                ON CONFLICT (review_id) DO UPDATE SET
                    review_score = EXCLUDED.review_score,
                    has_comment = EXCLUDED.has_comment
            """), clean_row(row.to_dict()))
    log_run("load", "fact_reviews", len(df), 0, "success")

def run_load():
    print(f"Starting load at {datetime.now()}")

    print("  Loading dim_customers...")
    upsert_dim_customers(transform_customers())

    print("  Loading dim_sellers...")
    upsert_dim_sellers(transform_sellers())

    print("  Loading dim_products...")
    upsert_dim_products(transform_products())

    print("  Loading fact_order_items...")
    upsert_fact_order_items(transform_order_items())

    print("  Loading fact_payments...")
    upsert_fact_payments(transform_payments())

    print("  Loading fact_reviews...")
    upsert_fact_reviews(transform_reviews())

    print("Load complete.")

if __name__ == "__main__":
    run_load()
