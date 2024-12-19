import yfinance as yf
import json
import os
from datetime import datetime
import pandas as pd
import requests

PRICE_CACHE_FILE = "../data/price_data_cache.json"
FUNDAMENTAL_CACHE_FILE = "../data/fundamental_data_cache.json"  # Cachad datafil
API_KEY = "7YCY5TPOOQ3YZR0K"


def convert_keys_to_str(data):
    """
    Rekursiv funktion som konverterar alla nycklar i en dictionary till strängar.
    """
    if isinstance(data, dict):
        return {str(key): convert_keys_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_str(item) for item in data]
    else:
        return data


def fetch_fundamental_data(ticker):
    """
    Hämtar fundamentala data från Alpha Vantage och cachar resultatet.
    """
    # Kontrollera om cachad data finns
    if os.path.exists(FUNDAMENTAL_CACHE_FILE):
        try:
            with open(FUNDAMENTAL_CACHE_FILE, "r") as file:
                cached_data = json.load(file)
        except json.JSONDecodeError:
            print("Ogiltig JSON-fil. Raderar och skapar ny.")
            os.remove(FUNDAMENTAL_CACHE_FILE)
            cached_data = {}
    else:
        cached_data = {}

    # Om data för ticker redan finns och är aktuell
    today = datetime.now().strftime("%Y-%m-%d")
    if ticker in cached_data and cached_data[ticker]["last_updated"] == today:
        print(f"Använder cachad fundament-data för {ticker}.")
        return cached_data[ticker]["data"]

    # Hämta ny data från Alpha Vantage
    url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={API_KEY}"
    print(f"Hämtar fundament-data för {ticker}...")
    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise ValueError(f"Fel vid API-anrop: {response.status_code}")

        data = response.json()
        if "annualReports" not in data:
            raise ValueError("API-anrop lyckades, men inga data hittades.")

        # Extrahera relevanta data
        fundamental_data = data["annualReports"]

        # Uppdatera cache
        try:
            cached_data[ticker] = {
                "last_updated": today,
                "data": fundamental_data
            }
            with open(FUNDAMENTAL_CACHE_FILE, "w") as file:
                json.dump(cached_data, file, indent=4)
                print(f"Fundament-data för {ticker} har sparats i cache.")
        except Exception as e:
            print(f"Fel vid skrivning till cache: {e}")

        return fundamental_data
    except Exception as e:
        print(f"Fel vid hämtning av data: {e}")
        return {}
def fetch_stock_prices(ticker, fundamental_data):
    """
    Hämtar prisdata för ett företag baserat på fundamentaldatan och cachar resultatet.
    """
    # Extrahera start- och slutdatum från fundamentaldatan
    dates = [report["fiscalDateEnding"] for report in fundamental_data]
    start_date = min(dates)
    end_date = max(dates)

    # Kontrollera om cachad data finns
    if os.path.exists(PRICE_CACHE_FILE):
        try:
            with open(PRICE_CACHE_FILE, "r") as file:
                cached_data = json.load(file)
        except json.JSONDecodeError:
            print("Ogiltig JSON-fil. Raderar och skapar ny.")
            os.remove(PRICE_CACHE_FILE)
            cached_data = {}
    else:
        cached_data = {}

    # Om data för ticker redan finns och är aktuell
    today = datetime.now().strftime("%Y-%m-%d")
    if ticker in cached_data and cached_data[ticker]["last_updated"] == today:
        print(f"Använder cachad prisdata för {ticker}.")
        return cached_data[ticker]["data"]

    # Hämta ny data från yfinance
    print(f"Hämtar prisdata för {ticker} från {start_date} till {end_date}...")
    try:
        data = yf.download(ticker, start=start_date, end=end_date, group_by='ticker', progress=False)
        if data.empty:
            raise ValueError(f"Inga prisdata hittades för {ticker} under perioden {start_date} till {end_date}.")
    except Exception as e:
        print(f"Fel vid hämtning av data från yfinance: {e}")
        return {}

    # Hantera nästlad data och välj rätt kolumn
    if isinstance(data.columns, pd.MultiIndex):
        if (ticker, 'Close') not in data.columns:
            raise KeyError(f"Kolumnen ('{ticker}', 'Close') saknas i data. Kontrollera ticker eller datakällan.")
        close_prices = data[(ticker, 'Close')]
    else:
        if 'Close' not in data.columns:
            raise KeyError(f"Kolumnen 'Close' saknas i data. Kontrollera ticker eller datakällan.")
        close_prices = data['Close']

    # Rensa NaN och konvertera index till datum
    close_prices.index = pd.to_datetime(close_prices.index, errors='coerce')
    close_prices = close_prices.dropna()

    # Skapa en dictionary med datum och pris
    data_dict = {
        str(date.date()): float(price) for date, price in close_prices.items()
    }

    # Uppdatera cache
    try:
        cached_data[ticker] = {
            "last_updated": today,
            "data": data_dict
        }
        with open(PRICE_CACHE_FILE, "w") as file:
            json.dump(cached_data, file, indent=4)
            print(f"Prisdata för {ticker} har sparats i cache.")
    except Exception as e:
        print(f"Fel vid skrivning till cache: {e}")

    return data_dict

# Exempelanvändning
if __name__ == "__main__":
    ticker = "MSFT"
    fundamental_data = fetch_fundamental_data(ticker)
    prices = fetch_stock_prices(ticker, fundamental_data)
    print(f"Prisdata för {ticker}:")
    print(json.dumps(prices, indent=4))
