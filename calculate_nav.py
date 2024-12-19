import json
import plotly.graph_objects as go
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Sökväg till JSON-filerna
file_path_fundamental = "../data/fundamental_data_cache.json"
file_path_price = "../data/price_data_cache.json"

# Läs in JSON-filerna
with open(file_path_fundamental, "r") as file:
    fundamentals_data = json.load(file)

with open(file_path_price, "r") as file:
    price_data = json.load(file)

# Extrahera fundamentala data
ticker = "MSFT"  # Ändra till AAPL om det behövs
reports = sorted(fundamentals_data[ticker]["data"], key=lambda x: x["fiscalDateEnding"])

years = []
total_assets = []
total_liabilities = []
equity = []
cash_flow = []  # Lägg till kassaflöde

for report in reports:
    try:
        year = report["fiscalDateEnding"]
        assets = int(report["totalAssets"])
        liabilities = int(report["totalLiabilities"])
        nav = assets - liabilities
        cash = int(report["cashAndShortTermInvestments"])  # Kassaflöde

        years.append(year)
        total_assets.append(assets)
        total_liabilities.append(liabilities)
        equity.append(nav)
        cash_flow.append(cash)
    except (TypeError, ValueError):
        print(f"Ogiltig data för {report.get('fiscalDateEnding', 'Okänt år')}")

# Omvandla till DataFrame
fundamental_df = pd.DataFrame({
    "Date": pd.to_datetime(years),
    "Total Assets": total_assets,
    "Total Liabilities": total_liabilities,
    "Equity": equity,
    "Cash Flow": cash_flow  # Lägg till kassaflöde
})
fundamental_df.set_index("Date", inplace=True)

# Extrahera prisdata
price_entries = price_data[ticker]["data"]
price_df = pd.DataFrame({
    "Date": pd.to_datetime(list(price_entries.keys())),
    "Price": list(price_entries.values())
})
price_df.set_index("Date", inplace=True)

# Normalisera alla kolumner
scaler = MinMaxScaler()
normalized_fundamentals = pd.DataFrame(
    scaler.fit_transform(fundamental_df),
    index=fundamental_df.index,
    columns=[f"{col} (Normalized)" for col in fundamental_df.columns]
)

price_df["Price (Normalized)"] = scaler.fit_transform(price_df[["Price"]])

# Skapa figuren med Plotly
fig = go.Figure()

# Lägg till normaliserade fundamentala nyckeltal
for column in normalized_fundamentals.columns:
    fig.add_trace(go.Scatter(
        x=normalized_fundamentals.index,
        y=normalized_fundamentals[column],
        mode='lines+markers',
        name=column
    ))

# Lägg till prisutveckling
fig.add_trace(go.Scatter(
    x=price_df.index,
    y=price_df["Price (Normalized)"],
    mode='lines',
    name="Price (Normalized)"
))

# Anpassa layouten
fig.update_layout(
    title="Normaliserad utveckling av fundamentala nyckeltal och prisdata",
    xaxis_title="Datum",
    yaxis_title="Normaliserat värde (0-100)",
    legend_title="Nyckeltal",
    template="plotly"
)

# Visa figuren
fig.show()
