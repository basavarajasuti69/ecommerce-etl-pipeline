-- schema.sql
-- E-commerce ETL Pipeline — Star Schema (Olist dataset)

DROP TABLE IF EXISTS fact_order_items CASCADE;
DROP TABLE IF EXISTS fact_payments CASCADE;
DROP TABLE IF EXISTS fact_reviews CASCADE;
DROP TABLE IF EXISTS dim_customers CASCADE;
DROP TABLE IF EXISTS dim_products CASCADE;
DROP TABLE IF EXISTS dim_sellers CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;
DROP TABLE IF EXISTS pipeline_run_log CASCADE;

-- ===================== DIMENSIONS =====================

CREATE TABLE dim_customers (
    customer_id             VARCHAR(32) PRIMARY KEY,
    customer_unique_id      VARCHAR(32) NOT NULL,
    customer_city           VARCHAR(100),
    customer_state          VARCHAR(2),
    customer_zip_code_prefix INTEGER
);

CREATE TABLE dim_products (
    product_id                     VARCHAR(32) PRIMARY KEY,
    product_category_name          VARCHAR(100),
    product_category_name_english  VARCHAR(100),
    product_weight_g               NUMERIC,
    product_length_cm              NUMERIC,
    product_height_cm              NUMERIC,
    product_width_cm               NUMERIC
);

CREATE TABLE dim_sellers (
    seller_id               VARCHAR(32) PRIMARY KEY,
    seller_city              VARCHAR(100),
    seller_state              VARCHAR(2),
    seller_zip_code_prefix   INTEGER
);

CREATE TABLE dim_date (
    date_id       INTEGER PRIMARY KEY,        -- format: YYYYMMDD
    full_date     DATE NOT NULL,
    year          INTEGER,
    month         INTEGER,
    day           INTEGER,
    day_of_week   VARCHAR(10),
    quarter       INTEGER
);

-- ===================== FACTS =====================

CREATE TABLE fact_order_items (
    order_item_sk           SERIAL PRIMARY KEY,
    order_id                VARCHAR(32) NOT NULL,
    order_item_id           INTEGER NOT NULL,
    customer_id             VARCHAR(32) REFERENCES dim_customers(customer_id),
    product_id              VARCHAR(32) REFERENCES dim_products(product_id),
    seller_id               VARCHAR(32) REFERENCES dim_sellers(seller_id),
    order_purchase_date_id  INTEGER REFERENCES dim_date(date_id),
    order_status             VARCHAR(20),
    price                    NUMERIC(10,2),
    freight_value             NUMERIC(10,2),
    delivery_delay_days       INTEGER,   -- delivered_date - estimated_date; NULL if not delivered
    UNIQUE (order_id, order_item_id)
);

CREATE TABLE fact_payments (
    payment_sk              SERIAL PRIMARY KEY,
    order_id                VARCHAR(32) NOT NULL,
    payment_sequential      INTEGER,
    payment_type            VARCHAR(20),
    payment_installments    INTEGER,
    payment_value            NUMERIC(10,2),
    UNIQUE (order_id, payment_sequential)
);

CREATE TABLE fact_reviews (
    review_id       VARCHAR(32) PRIMARY KEY,
    order_id        VARCHAR(32) NOT NULL,
    review_score    INTEGER,
    has_comment     BOOLEAN
);

-- ===================== PIPELINE LOGGING =====================

CREATE TABLE pipeline_run_log (
    run_id           SERIAL PRIMARY KEY,
    run_timestamp    TIMESTAMP DEFAULT NOW(),
    stage            VARCHAR(50),      -- 'extract', 'transform', 'load'
    table_name       VARCHAR(50),
    rows_processed   INTEGER,
    rows_rejected    INTEGER,
    status           VARCHAR(20),      -- 'success', 'failed'
    notes            TEXT
);
