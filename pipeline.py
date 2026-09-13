from datetime import datetime
from extract import extract
from load import run_load

def run_pipeline():
    start = datetime.now()
    print(f"{'='*60}")
    print(f"PIPELINE RUN STARTED: {start}")
    print(f"{'='*60}\n")

    print(">>> STAGE 1: EXTRACT")
    extract()

    print("\n>>> STAGE 2: TRANSFORM + LOAD")
    run_load()

    end = datetime.now()
    print(f"\n{'='*60}")
    print(f"PIPELINE RUN COMPLETE: {end}")
    print(f"Total duration: {end - start}")
    print(f"{'='*60}")

if __name__ == "__main__":
    run_pipeline()
