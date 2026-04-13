import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_AIRPORTS_CSV = ROOT / "data" / "airports.csv"
INPUT_FLIGHTS_CSV  = ROOT / "data" / "flights_small.csv"

OUT_DIR = ROOT / "data"
OUT_DIR.mkdir(exist_ok=True, parents=True)

def preprocess():
    airports = pd.read_csv(INPUT_AIRPORTS_CSV)
    flights = pd.read_csv(INPUT_FLIGHTS_CSV)

    # Route-month aggregates
    route_month = (
        flights.groupby(["YEAR","MONTH","OP_UNIQUE_CARRIER","ORIGIN","DEST"])
               .agg(flights=("ARR_DELAY","count"),
                    avg_arr_delay=("ARR_DELAY","mean"),
                    avg_dep_delay=("DEP_DELAY","mean"))
               .reset_index()
    )
    route_month.to_csv(OUT_DIR/"route_month.csv", index=False)

    # Airport-month aggregates
    airport_month = (
        flights.groupby(["YEAR","MONTH","ORIGIN"])
               .agg(flights=("DEP_DELAY","count"),
                    avg_dep_delay=("DEP_DELAY","mean"))
               .reset_index()
               .rename(columns={"ORIGIN":"AIRPORT"})
    )
    airport_month.to_csv(OUT_DIR/"airport_month.csv", index=False)

    print("Wrote:", OUT_DIR/"route_month.csv", OUT_DIR/"airport_month.csv")

if __name__ == "__main__":
    preprocess()
