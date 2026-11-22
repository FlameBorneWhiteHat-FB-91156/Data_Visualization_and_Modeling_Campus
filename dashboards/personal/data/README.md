# Energy Efficiency: fixed course lab copy

UCI Machine Learning Repository: **Energy Efficiency**, Tsanas and Xifara (2012).
Official source documentation: https://archive.ics.uci.edu/dataset/242/energy+efficiency
DOI: https://doi.org/10.24432/C51307. Licensed CC BY 4.0.

The official dataset is published as ENB2012_data.xlsx (768 rows); this dashboard
uses a fixed CSV-formatted copy with the same standard X1-X8, Y1-Y2 column names,
retrieved on November 22, 2026, from the public CSV mirror:
https://github.com/Yrzxiong/Energy-Efficiency-Analysis/blob/master/ENB2012_data.csv

This is disclosed as a mirror copy; the CSV was checked for 768 complete numeric rows,
ten columns, and the UCI-documented feature names. It was not byte-for-byte compared
with the official XLSX because that file was not downloaded in this session.

X1 relative compactness; X2 surface area; X3 wall area; X4 roof area;
X5 overall height; X6 orientation; X7 glazing area; X8 glazing-area distribution;
Y1 heating load; Y2 cooling load. The official metadata gives no load or height
units; labels therefore say "reported simulation units" or "dataset values"
rather than inventing physical units. One row is one computer-simulated design
scenario, not one measured building. There are no missing values.

The dashboard's filters are height (all, 3.5, 7.0) and glazing (all, 0,
0.10, 0.25, 0.40). Both controls update all four Plotly figures and sample
summary. Two all-data conclusions are descriptive only; because design
features co-vary, causal interpretations are not warranted.
