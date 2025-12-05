# Model Evaluation Notes

## Dataset Size Issue

The World Bank GDP dataset is quite small: **15 total samples (2010-2024)**.

### Current Train/Test Split (test_years=3)
- **Training samples:** 12 (2010-2021)
- **Test samples:** 3 (2022-2024)
- **Train/Test ratio:** 80/20 (reasonable)

### Classification Accuracy = 1.0 (Why this is misleading)

While the test set accuracy shows 1.0, this is **statistically unreliable** because:

1. **Test set is tiny:** Only 3 samples
   - 1 "Low Growth" sample (class 0)
   - 2 "High Growth" samples (class 1)
   
2. **Perfect accuracy by chance:** With 3 samples, random guessing could achieve high accuracy

3. **Class imbalance:** The test set is imbalanced (1 vs 2), which skews metrics

### Regression Performance (More Realistic)

The regression model shows a **negative R² (-0.048)**, which is more honest:
- This means the model performs **worse than simply predicting the training set mean**
- With only 12 training samples and 6 features, overfitting is likely
- RMSE of 0.0918 is difficult to interpret without domain knowledge

## Recommendations for Better Evaluation

### 1. **Use Cross-Validation**
   ```python
   from sklearn.model_selection import TimeSeriesSplit
   tscv = TimeSeriesSplit(n_splits=5)
   # Use for time-series aware cross-validation
   ```

### 2. **Collect More Data**
   - Current: 15 annual samples
   - Better: 50+ samples for reliable evaluation
   - Consider: monthly or quarterly data instead of annual

### 3. **Use Adjusted Metrics**
   - For classification: Use precision-recall instead of accuracy with imbalanced sets
   - For regression: Use mean absolute percentage error (MAPE) or other domain-specific metrics

### 4. **Increase Training Data Utilization**
   - With only 15 samples, using 12 for training leaves little for testing
   - Consider: 10 train / 5 test split to get more test samples for evaluation

## Current Parameter: test_years=3

Set in both `prefect/flows/ml_pipeline.py` and `test_prefect_pipeline.py` to balance:
- Training data size (need enough to learn patterns)
- Test set size (need enough for reliable evaluation)

With 15-year dataset: 3 test years = ~3-4 samples for evaluation.

---

**TL;DR:** Perfect metrics on tiny test sets are not reliable. The negative R² regression score is more trustworthy - it shows the model needs more data or better features to generalize well.
