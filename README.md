# Airline Network Visualization (VTK + Trame v2)

Interactive 3D airline network using VTK & Trame with:
- Airports on globe (size=degree, color=betweenness)
- Routes colored by average arrival delay
- Filters: Year, Month, Airline
- Hub shutdown simulation (removes all routes for a hub)

## Run
```
pip install -r requirements.txt
python -m src.data_preprocessing
python -m src.app_trame
```
Then open the printed URL (e.g., http://localhost:1234).

## Real Data
This project ships with a **schema-compatible sample** of the BTS On-Time dataset for 2019 & 2020.
Swap in full BTS CSVs by editing paths in `src/data_preprocessing.py` and re-running it.
