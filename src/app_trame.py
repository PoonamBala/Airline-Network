import pandas as pd
from pathlib import Path
import vtk

from trame.app import get_server
from trame.ui.vuetify import SinglePageWithDrawerLayout
from trame.widgets import vtk as vtk_widgets
from trame.widgets import vuetify, html
from trame.widgets import plotly as tpl_plotly

from .graph_analysis import build_graph
from .vtk_viz import build_earth, build_airport_glyphs, build_route_lines

ROOT = Path(__file__).resolve().parents[1]
AIRPORTS = ROOT / "data" / "airports.csv"
ROUTE_MONTH = ROOT / "data" / "route_month.csv"

airports_df = pd.read_csv(AIRPORTS)
coords = {r.IATA_CODE: (r.LAT, r.LON) for _, r in airports_df.iterrows()}

server = get_server()
state, ctrl = server.state, server.controller

state.setdefault("year", 2019)
state.setdefault("month", 1)
state.setdefault("carrier", "All")
state.setdefault("hub", "")
state.setdefault("status", "Ready")

renderer = vtk.vtkRenderer(); renderer.SetBackground(0.02,0.02,0.05)
render_window = vtk.vtkRenderWindow(); render_window.AddRenderer(renderer)
earth_actor = build_earth(1.0); renderer.AddActor(earth_actor)

airports_actor = None
routes_actor = None

def centrality_lookup(G):
    d = {}
    for n, data in G.nodes(data=True):
        d[n] = {"deg_cent": float(data.get("deg_cent",0.0)), "bet_cent": float(data.get("bet_cent",0.0))}
    return d

def update_scene():
    global airports_actor, routes_actor
    # Build graph and filtered routes
    shutdown = state.hub.strip().upper() or None
    G, routes_df = build_graph(year=state.year, month=state.month, carrier=state.carrier, shutdown_hub=shutdown)

    # Remove old actors
    if airports_actor: renderer.RemoveActor(airports_actor); airports_actor = None
    if routes_actor: renderer.RemoveActor(routes_actor); routes_actor = None

    # Build & add new actors
    airports_actor = build_airport_glyphs(airports_df, centrality_lookup(G), R=1.02)
    routes_actor = build_route_lines(routes_df[["ORIGIN","DEST","avg_arr_delay"]], coords, R=1.0)
    renderer.AddActor(airports_actor); renderer.AddActor(routes_actor)
    render_window.Render()

    # Update status and chart
    state.status = f"Year={state.year}, Month={state.month}, Carrier={state.carrier}, Shutdown={shutdown or 'None'}"
    update_chart()

def update_chart():
    from plotly import express as px
    df = pd.read_csv(ROUTE_MONTH)
    q = df[(df["YEAR"] == state.year)]
    if state.carrier != "All":
        q = q[q["OP_UNIQUE_CARRIER"] == state.carrier]
    # avg delay per month (year-level)
    m = q.groupby("MONTH")["avg_arr_delay"].mean().reset_index()
    fig = px.line(m, x="MONTH", y="avg_arr_delay", title=f"Average Arrival Delay — {state.year} ({state.carrier})")
    ctrl.update_plot(fig)

@ctrl.add("apply_filters")
def apply_filters():
    update_scene()

@ctrl.add("shutdown_hub")
def shutdown_hub():
    update_scene()

# Auto-apply on changes
@state.change("year", "month", "carrier")
def _auto_apply(**kwargs):
    update_scene()

with SinglePageWithDrawerLayout(server) as layout:
    layout.title.set_text("Airline Network — VTK + Trame (v2)")

    with layout.toolbar:
        vuetify.VSelect(items=([2019, 2020],), v_model=("year", 2019), label="Year", dense=True, hide_details=True, style="max-width:120px")
        vuetify.VSelect(items=(["All","AA","DL","UA","WN"],), v_model=("carrier", "All"), label="Airline", dense=True, hide_details=True, style="max-width:140px")
        vuetify.VSlider(v_model=("month", 1), min=1, max=12, step=1, label="Month", hide_details=True, style="max-width:320px; margin-left:12px")
        vuetify.VTextField(v_model=("hub",""), label="Shutdown Hub (IATA)", hide_details=True, style="max-width:200px; margin-left:12px")
        vuetify.VBtn("Apply", click=ctrl.apply_filters, class_="mx-2", color="primary")
        vuetify.VBtn("Shutdown Hub", click=ctrl.shutdown_hub, color="error")
        vuetify.VSpacer()
        html.Div(["Status: ", (state, "status")])

    with layout.content:
        vtk_widgets.VtkLocalView(render_window, ref="view", interactive_ratio=1)
        # Placeholder plot area that we update via controller
        from plotly import graph_objs as go
        ctrl.update_plot = lambda fig: plot_widget.update(figure=fig)
        plot_widget = tpl_plotly.Figure(go.Figure(), style="height:320px;")

if __name__ == "__main__":
    update_scene()
    server.start()
