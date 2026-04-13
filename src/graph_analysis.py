import pandas as pd
import networkx as nx
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTE_MONTH = ROOT / "data" / "route_month.csv"

def build_graph(year=2019, month=1, carrier="All", shutdown_hub=None):
    df = pd.read_csv(ROUTE_MONTH)
    q = df[(df["YEAR"] == year) & (df["MONTH"] == month)]
    if carrier and carrier != "All":
        q = q[q["OP_UNIQUE_CARRIER"] == carrier]
    if shutdown_hub:
        q = q[(q["ORIGIN"] != shutdown_hub) & (q["DEST"] != shutdown_hub)]

    G = nx.DiGraph()
    for _, r in q.iterrows():
        G.add_edge(r["ORIGIN"], r["DEST"],
                   flights=int(r["flights"]),
                   delay=float(r["avg_arr_delay"]))

    n = G.number_of_nodes()
    deg = nx.degree_centrality(G) if n > 0 else {}
    if n < 3:
        bet = {node: 0.0 for node in G.nodes()}
    else:
        k = min(200, max(1, n // 2))
        bet = nx.betweenness_centrality(G, k=k, weight=None)

    nx.set_node_attributes(G, deg, "deg_cent")
    nx.set_node_attributes(G, bet, "bet_cent")
    return G, q  # return both graph and filtered route df
