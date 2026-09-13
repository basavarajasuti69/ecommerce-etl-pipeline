import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

# Cover 2016-01-01 through 2018-12-31 (dataset range with buffer)
date_range = pd.date_range(start="2016-01-01", end="2018-12-31", freq="D")

dim_date = pd.DataFrame({
    "date_id": date_range.strftime("%Y%m%d").astype(int),
    "full_date": date_range,
    "year": date_range.year,
    "month": date_range.month,
    "day": date_range.day,
    "day_of_week": date_range.strftime("%A"),
    "quarter": date_range.quarter,
})

dim_date.to_sql("dim_date", engine, if_exists="append", index=False)

print(f"Loaded {len(dim_date)} rows into dim_date")

