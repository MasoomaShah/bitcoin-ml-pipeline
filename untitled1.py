import requests
import pandas as pd
from functools import reduce

# Country and indicators
country = "PAK"
indicators = {
    "GDP": "NY.GDP.MKTP.CD",
    "Population": "SP.POP.TOTL",
    "Inflation": "FP.CPI.TOTL.ZG",
    "Unemployment": "SL.UEM.TOTL.ZS"
}

dfs = []

# Fetch each indicator
for name, code in indicators.items():
    url = f"http://api.worldbank.org/v2/country/{country}/indicator/{code}?format=json&date=2000:2025"
    data = requests.get(url).json()
    df = pd.DataFrame(data[1])[['date','value']]
    df.rename(columns={'value': name}, inplace=True)
    dfs.append(df)

# Merge all indicators on 'date'
df = reduce(lambda left, right: pd.merge(left, right, on='date'), dfs)
df['date'] = pd.to_datetime(df['date'], format='%Y')
df = df.sort_values('date').reset_index(drop=True)

# Create target and one rolling feature
df['GDP_growth'] = df['GDP'].pct_change()          # Target
df['GDP_rolling3'] = df['GDP'].rolling(3).mean()   # Trend feature

# Select only 7 columns
df_final = df[['date', 'GDP', 'GDP_growth', 'Population', 'Inflation', 'Unemployment', 'GDP_rolling3']]

# Drop rows with NaN (from pct_change and rolling)
df_final = df_final.dropna().reset_index(drop=True)

print(df_final)
