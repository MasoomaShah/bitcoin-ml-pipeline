import pandas as pd
from src.preprocess_timeseries import create_classification_target
import numpy as np

df = pd.read_csv('data/raw/world_bank_gdp.csv')
print('DataFrame shape:', df.shape)
print('\nGDP_growth values:')
print(df['GDP_growth'].values)
print('\nClassification targets (threshold=0.05):')
targets = create_classification_target(df['GDP_growth'], threshold=0.05)
print('Targets:', targets)
print('Unique classes:', np.unique(targets))
print('\nValue counts:')
print(pd.Series(targets).value_counts())

# Check train/test split
df['year'] = df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year
df['growth_class'] = targets
df = df.sort_values('date').reset_index(drop=True)

unique_years = sorted(df['year'].unique())
test_years = 2
test_threshold_year = unique_years[-test_years]

train_mask = df['year'] < test_threshold_year
test_mask = df['year'] >= test_threshold_year

print('\n=== Train/Test Split ===')
print(f'Threshold year: {test_threshold_year}')
print(f'Train size: {train_mask.sum()}, Test size: {test_mask.sum()}')
print(f'\nTrain growth_class values: {df[train_mask]["growth_class"].values}')
print(f'Test growth_class values: {df[test_mask]["growth_class"].values}')
