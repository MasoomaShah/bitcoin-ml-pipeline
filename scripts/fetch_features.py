#!/usr/bin/env python3
import pandas as pd
import requests
from datetime import datetime

try:
    url = 'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart'
    params = {'vs_currency': 'usd', 'days': '365', 'interval': 'daily'}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    prices = resp.json().get('prices', [])
    
    if not prices:
        print('No data received')
        exit(1)
    
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['MA7'] = df['price'].rolling(7).mean()
    df['MA14'] = df['price'].rolling(14).mean()
    df['MA30'] = df['price'].rolling(30).mean()
    df['ROC'] = df['price'].pct_change(7)
    df['Volatility'] = df['price'].rolling(14).std()
    
    import os
    os.makedirs('data/features', exist_ok=True)
    
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    path = f'data/features/btc_features_{ts}.csv'
    df.to_csv(path, index=False)
    df.tail(1).to_csv('data/features/btc_latest.csv', index=False)
    
    print(f'Saved {len(df)} records to {path}')
    
except Exception as e:
    print(f'Error: {e}')
    exit(1)
