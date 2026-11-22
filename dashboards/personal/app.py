"""Interactive building energy efficiency dashboard from the UCI 2012 simulations.

Audience: building designers and energy analysts.
The figures describe simulated design alternatives, not measured building energy use.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

HEIGHT_COLORS = {"3.5": "#2675a5", "7.0": "#d47c4a"}
HEIGHT_ORDER = ["3.5", "7.0"]
GLAZING_ORDER = ["0.00", "0.10", "0.25", "0.40"]


def prepare_energy(data):
    """Prepare a fresh copy of the original ten-column UCI dataset."""
    source = data.copy(deep=True)
    names = {
        "X1": "relative_compactness",
        "X2": "surface_area",
        "X3": "wall_area",
        "X4": "roof_area",
        "X5": "overall_height",
        "X6": "orientation",
        "X7": "glazing_area",
        "X8": "glazing_distribution",
        "Y1": "heating_load",
        "Y2": "cooling_load",
    }
    if not set(names).issubset(source.columns):
        raise ValueError("The original UCI Energy Efficiency columns X1-X8, Y1, Y2 are required.")
    source = source.rename(columns=names)
    for field in names.values():
        source[field] = pd.to_numeric(source[field], errors="coerce")
    if source[list(names.values())].isna().any().any():
        raise ValueError("Unexpected missing or nonnumeric values in original dataset.")
    source["height_label"] = source["overall_height"].map(lambda x: f"{x:.1f}")
    source["glazing_label"] = source["glazing_area"].map(lambda x: f"{x:.2f}")
    source["simulation_id"] = range(1, len(source) + 1)
    return source


def filter_energy(prepared, height_choice="all", glazing_choice="all"):
    """All means no filter. Invalid/unmatched values return an empty subset."""
    result = prepared
    if height_choice != "all":
        result = result.loc[result["height_label"] == str(height_choice)]
    if glazing_choice != "all":
        result = result.loc[result["glazing_label"] == str(glazing_choice)]
    return result.copy()


def energy_figures(filtered):
    """Four Plotly figures mirroring the four notebook static analyses."""
    n = len(filtered)
    title_tail = f"({n} simulated designs)"
    if n == 0:
        empty = []
        for title in [
            "Heating-load distribution",
            "Heating load by glazing area",
            "Compactness and heating load",
            "Average cooling load by height and glazing",
        ]:
            fig = go.Figure()
            fig.update_layout(title=title + " (0 designs)", template="plotly_white", height=360)
            fig.add_annotation(text="No designs match this combination of filters.",
                               xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            empty.append(fig)
        return tuple(empty)

    histogram = px.histogram(
        filtered, x="heating_load", color="height_label", barmode="overlay",
        category_orders={"height_label": HEIGHT_ORDER},
        color_discrete_map=HEIGHT_COLORS,
        labels={"heating_load": "Heating load (reported simulation units)",
                "height_label": "Overall height"},
        title="Heating-load distribution " + title_tail,
    )
    histogram.update_traces(xbins=dict(start=5, end=45, size=5), opacity=0.78)
    histogram.update_layout(yaxis_title="Number of designs", bargap=0.08,
                            legend_title_text="Overall height", template="plotly_white",
                            height=380)

    box = px.box(
        filtered, x="glazing_label", y="heating_load", color="height_label",
        category_orders={"glazing_label": GLAZING_ORDER, "height_label": HEIGHT_ORDER},
        color_discrete_map=HEIGHT_COLORS, points=False,
        labels={"glazing_label": "Glazing area (dataset values)",
                "heating_load": "Heating load (reported simulation units)",
                "height_label": "Overall height"},
        title="Heating load by glazing area " + title_tail,
    )
    box.update_layout(template="plotly_white", height=380, legend_title_text="Overall height")

    scatter = px.scatter(
        filtered, x="relative_compactness", y="heating_load",
        color="height_label", hover_data=["simulation_id", "glazing_label", "cooling_load"],
        category_orders={"height_label": HEIGHT_ORDER},
        color_discrete_map=HEIGHT_COLORS, opacity=0.66,
        labels={"relative_compactness": "Relative compactness",
                "heating_load": "Heating load (reported simulation units)",
                "height_label": "Overall height", "glazing_label": "Glazing area",
                "simulation_id": "Simulation ID", "cooling_load": "Cooling load"},
        title="Compactness vs. heating load " + title_tail,
    )
    scatter.update_layout(template="plotly_white", height=390, legend_title_text="Overall height")

    means = filtered.groupby(["height_label", "glazing_label"])["cooling_load"].mean()
    heat_z = []
    heat_text = []
    for height in HEIGHT_ORDER:
        row, row_text = [], []
        for glaze in GLAZING_ORDER:
            val = means.get((height, glaze))
            row.append(round(float(val), 4) if val is not None else None)
            row_text.append(f"{val:.2f}" if val is not None else "")
        heat_z.append(row)
        heat_text.append(row_text)
    heatmap = go.Figure(go.Heatmap(
        z=heat_z, x=GLAZING_ORDER, y=HEIGHT_ORDER, text=heat_text,
        texttemplate="%{text}", colorscale="YlGnBu",
        colorbar=dict(title="Mean cooling load"),
        hovertemplate="Height %{y}, glazing %{x}<br>Mean cooling load: %{z:.2f}<extra></extra>",
    ))
    heatmap.update_layout(
        title="Average cooling load by height and glazing " + title_tail,
        xaxis_title="Glazing area (dataset values)", yaxis_title="Overall height",
        height=390, template="plotly_white",
    )
    return histogram, box, scatter, heatmap


def build_dashboard(data):
    """Create a new, independent Dash app and register the interactive callback."""
    prepared = prepare_energy(data)
    app = Dash(__name__)
    app.title = "Building Energy Design Explorer"

    panel = {"padding": "18px", "border": "1px solid #dae3ef",
             "backgroundColor": "#fff", "borderRadius": "14px"}
    heading = {"color": "#203452", "fontWeight": 700}
    app.layout = html.Div(
        style={"fontFamily": "Arial, sans-serif", "maxWidth": "1220px",
               "margin": "auto", "padding": "30px 20px", "color": "#253750",
               "backgroundColor": "#f5f7fb"},
        children=[
            html.P("UCI ENERGY EFFICIENCY | 2012 SIMULATIONS",
                   style={"fontSize": "12px", "letterSpacing": "2px",
                          "fontWeight": "bold", "color": "#4d6691"}),
            html.H1("Building Energy Design Explorer", style=heading),
            html.P("For building designers: explore how height, glazing, and compactness are "
                   "associated with simulated heating and cooling loads. These are modeled "
                   "design scenarios, not measured energy bills."),
            html.Div([
                html.Div([
                    html.Label("Overall building height", htmlFor="height-choice"),
                    dcc.Dropdown(id="height-choice",
                                 options=[{"label": "All heights", "value": "all"},
                                          {"label": "3.5 (dataset units)", "value": "3.5"},
                                          {"label": "7.0 (dataset units)", "value": "7.0"}],
                                 value="all", clearable=False),
                ], style={"flex": "1", "minWidth": "215px"}),
                html.Div([
                    html.Label("Glazing area", htmlFor="glazing-choice"),
                    dcc.Dropdown(id="glazing-choice",
                                 options=[{"label": "All glazing values", "value": "all"}]
                                          + [{"label": value, "value": value}
                                             for value in GLAZING_ORDER],
                                 value="all", clearable=False),
                ], style={"flex": "1", "minWidth": "215px"}),
            ], style={**panel, "display": "flex", "flexWrap": "wrap", "gap": "24px"}),
            html.Div([
                html.H2("Selected designs", style={"fontSize": "19px", **heading}),
                html.P(id="sample-count"),
                html.P(id="summary-text", style={"lineHeight": "1.55"}),
            ], style={**panel, "marginTop": "18px"}, role="status"),
            html.Div([
                html.Div([html.H2("Heating-load distribution", style=heading),
                          dcc.Graph(id="heating-histogram")], style=panel),
                html.Div([html.H2("Heating load by glazing area", style=heading),
                          dcc.Graph(id="heating-box")], style=panel),
                html.Div([html.H2("Compactness and heating load", style=heading),
                          dcc.Graph(id="compactness-scatter")], style=panel),
                html.Div([html.H2("Cooling-load comparison", style=heading),
                          dcc.Graph(id="cooling-heatmap")], style=panel),
            ], style={"display": "grid",
                      "gridTemplateColumns": "repeat(auto-fit, minmax(420px, 1fr))",
                      "gap": "16px", "marginTop": "18px"}),
            html.Div([
                html.H2("What the full dataset suggests", style=heading),
                html.P("Across all 768 simulated designs, the mean heating load is 31.28 "
                       "for designs with height 7.0 and 13.34 for designs with height 3.5. "
                       "This is a descriptive association, not a controlled causal effect. "
                       "Filtering above changes the selected charts and summary, not this "
                       "full-dataset conclusion."),
                html.H2("Source and limitations", style=heading),
                html.P("UCI Machine Learning Repository: Energy Efficiency (Tsanas and "
                       "Xifara, 2012). Fixed 768-row dataset; eight design features, "
                       "two simulated responses."),
                html.A("UCI dataset documentation",
                       href="https://archive.ics.uci.edu/dataset/242/energy+efficiency",
                       target="_blank"),
                html.P("Limitations: (1) the records are Ecotect computer simulations, "
                       "not observed building utility use or representative real buildings; "
                       "(2) height, compactness, geometry, and glazing vary together across "
                       "the design scenarios. These plots do not isolate a causal effect "
                       "or validate predictions on new buildings."),
            ], style={**panel, "marginTop": "18px", "lineHeight": "1.55"}),
        ],
    )

    @app.callback(
        Output("heating-histogram", "figure"),
        Output("heating-box", "figure"),
        Output("compactness-scatter", "figure"),
        Output("cooling-heatmap", "figure"),
        Output("sample-count", "children"),
        Output("summary-text", "children"),
        Input("height-choice", "value"),
        Input("glazing-choice", "value"),
    )
    def update_dashboard(height_choice, glazing_choice):
        selected = filter_energy(prepared, height_choice, glazing_choice)
        figures = energy_figures(selected)
        if selected.empty:
            return (*figures, "0 of 768 simulated designs",
                    "No designs match these filters. Select All to reset.")
        avg_heat = selected["heating_load"].mean()
        avg_cool = selected["cooling_load"].mean()
        summary = (f"Mean heating load: {avg_heat:.2f}; mean cooling load: {avg_cool:.2f} "
                   f"(simulation dataset units). The charts reflect the {len(selected)} "
                   "matching designs; no missing combinations are treated as zero.")
        return (*figures, f"{len(selected)} of {len(prepared)} simulated designs", summary)
    return app


data = pd.read_csv(Path(__file__).resolve().parent / "data" / "energy_efficiency_uci.csv")
app = build_dashboard(data)
server = app.server

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8055, debug=False)
