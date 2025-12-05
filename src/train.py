from data_ingestion import load_data_from_postgres
from preprocessing import preprocess_data
from models.regression import train_regression
from models.classification import train_classification
import joblib
import json
import os


if __name__ == "__main__":
    df = load_data_from_postgres()
    # Preprocess and get fitted MultiLabelBinarizer
    df_processed, mlb = preprocess_data(df)

    # Determine feature columns used for training (drop labels)
    feature_columns = [c for c in df_processed.columns if c not in ['popularity', 'popular']]

    # Save preprocessing artifacts to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mlb_path = os.path.join(project_root, "mlb.pkl")
    features_path = os.path.join(project_root, "feature_columns.json")
    joblib.dump(mlb, mlb_path)
    with open(features_path, 'w', encoding='utf-8') as f:
        json.dump(feature_columns, f)
    print(f"Saved ML preprocessing artifacts: {mlb_path}, {features_path}")

    # Train models (these functions save model .pkl files)
    train_regression(df_processed)
    train_classification(df_processed)
