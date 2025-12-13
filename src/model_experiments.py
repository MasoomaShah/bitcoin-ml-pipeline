"""
Model Experimentation Module
Tests multiple ML models and selects the best one
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge, Lasso
from sklearn.svm import SVC, SVR
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from typing import Dict, Tuple, List
import warnings
warnings.filterwarnings('ignore')


class ModelExperiments:
    """Experiment with multiple ML models and find the best one"""
    
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.classification_models = {}
        self.regression_models = {}
        self.results = {
            'classification': [],
            'regression': []
        }
        
    def get_classification_models(self) -> Dict:
        """Get dictionary of classification models to test"""
        return {
            'RandomForest': RandomForestClassifier(
                n_estimators=300,
                max_depth=20,
                max_features='log2',
                class_weight='balanced',
                random_state=self.random_state,
                n_jobs=-1
            ),
            'GradientBoosting': GradientBoostingClassifier(
                n_estimators=200,
                max_depth=10,
                learning_rate=0.1,
                random_state=self.random_state
            ),
            'LogisticRegression': LogisticRegression(
                max_iter=1000,
                class_weight='balanced',
                random_state=self.random_state,
                n_jobs=-1
            ),
            'SVM': SVC(
                kernel='rbf',
                class_weight='balanced',
                random_state=self.random_state
            )
        }
    
    def get_regression_models(self) -> Dict:
        """Get dictionary of regression models to test"""
        return {
            'RandomForest': RandomForestRegressor(
                n_estimators=300,
                max_depth=20,
                max_features='log2',
                random_state=self.random_state,
                n_jobs=-1
            ),
            'GradientBoosting': GradientBoostingRegressor(
                n_estimators=200,
                max_depth=10,
                learning_rate=0.1,
                random_state=self.random_state
            ),
            'Ridge': Ridge(
                alpha=1.0,
                random_state=self.random_state
            ),
            'Lasso': Lasso(
                alpha=1.0,
                random_state=self.random_state
            ),
            'SVR': SVR(
                kernel='rbf'
            )
        }
    
    def evaluate_classification(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray
    ) -> Tuple[object, Dict, List]:
        """
        Train and evaluate multiple classification models
        
        Returns:
            best_model: The best performing model
            best_metrics: Metrics of the best model
            all_results: List of all model results
        """
        print("\n" + "="*60)
        print("CLASSIFICATION MODEL EXPERIMENTS")
        print("="*60)
        
        models = self.get_classification_models()
        results = []
        
        for name, model in models.items():
            print(f"\nTraining {name}...")
            try:
                # Train
                model.fit(X_train, y_train)
                
                # Predict
                y_pred = model.predict(X_test)
                
                # Evaluate
                metrics = {
                    'model_name': name,
                    'accuracy': accuracy_score(y_test, y_pred),
                    'f1_score': f1_score(y_test, y_pred, average='weighted'),
                    'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
                    'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0)
                }
                
                results.append({
                    'model': model,
                    'metrics': metrics
                })
                
                print(f"  Accuracy:  {metrics['accuracy']:.4f}")
                print(f"  F1-Score:  {metrics['f1_score']:.4f}")
                print(f"  Precision: {metrics['precision']:.4f}")
                print(f"  Recall:    {metrics['recall']:.4f}")
                
            except Exception as e:
                print(f"  ✗ Failed: {str(e)}")
        
        # Find best model by accuracy
        best_result = max(results, key=lambda x: x['metrics']['accuracy'])
        
        print(f"\n{'='*60}")
        print(f"BEST CLASSIFICATION MODEL: {best_result['metrics']['model_name']}")
        print(f"Accuracy: {best_result['metrics']['accuracy']:.4f}")
        print(f"{'='*60}")
        
        self.results['classification'] = results
        return best_result['model'], best_result['metrics'], results
    
    def evaluate_regression(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray
    ) -> Tuple[object, Dict, List]:
        """
        Train and evaluate multiple regression models
        
        Returns:
            best_model: The best performing model
            best_metrics: Metrics of the best model
            all_results: List of all model results
        """
        print("\n" + "="*60)
        print("REGRESSION MODEL EXPERIMENTS")
        print("="*60)
        
        models = self.get_regression_models()
        results = []
        
        for name, model in models.items():
            print(f"\nTraining {name}...")
            try:
                # Train
                model.fit(X_train, y_train)
                
                # Predict
                y_pred = model.predict(X_test)
                
                # Evaluate
                metrics = {
                    'model_name': name,
                    'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                    'mae': mean_absolute_error(y_test, y_pred),
                    'r2': r2_score(y_test, y_pred)
                }
                
                results.append({
                    'model': model,
                    'metrics': metrics
                })
                
                print(f"  RMSE: {metrics['rmse']:.4f}")
                print(f"  MAE:  {metrics['mae']:.4f}")
                print(f"  R²:   {metrics['r2']:.4f}")
                
            except Exception as e:
                print(f"  ✗ Failed: {str(e)}")
        
        # Find best model by R² score
        valid_results = [r for r in results if r['metrics']['r2'] > -100]  # Filter extreme values
        if valid_results:
            best_result = max(valid_results, key=lambda x: x['metrics']['r2'])
        else:
            best_result = results[0] if results else None
        
        if best_result:
            print(f"\n{'='*60}")
            print(f"BEST REGRESSION MODEL: {best_result['metrics']['model_name']}")
            print(f"R²: {best_result['metrics']['r2']:.4f}")
            print(f"RMSE: {best_result['metrics']['rmse']:.4f}")
            print(f"{'='*60}")
        
        self.results['regression'] = results
        return best_result['model'], best_result['metrics'], results if best_result else (None, {}, [])
    
    def get_results_dataframe(self, task='classification') -> pd.DataFrame:
        """Get results as a DataFrame for easy comparison"""
        if task == 'classification':
            data = [r['metrics'] for r in self.results['classification']]
        else:
            data = [r['metrics'] for r in self.results['regression']]
        
        return pd.DataFrame(data).sort_values(
            by='accuracy' if task == 'classification' else 'r2',
            ascending=False
        )


def test_model_experiments():
    """Test the model experiments module"""
    from sklearn.datasets import make_classification, make_regression
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    
    print("Testing Model Experiments Module...")
    print()
    
    # Generate synthetic data
    X_clf, y_clf = make_classification(n_samples=1000, n_features=20, random_state=42)
    X_reg, y_reg = make_regression(n_samples=1000, n_features=20, random_state=42)
    
    # Split
    X_train_clf, X_test_clf, y_train_clf, y_test_clf = train_test_split(
        X_clf, y_clf, test_size=0.2, random_state=42
    )
    X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(
        X_reg, y_reg, test_size=0.2, random_state=42
    )
    
    # Scale
    scaler = StandardScaler()
    X_train_clf_scaled = scaler.fit_transform(X_train_clf)
    X_test_clf_scaled = scaler.transform(X_test_clf)
    X_train_reg_scaled = scaler.fit_transform(X_train_reg)
    X_test_reg_scaled = scaler.transform(X_test_reg)
    
    # Test
    experiments = ModelExperiments()
    
    best_clf, clf_metrics, clf_results = experiments.evaluate_classification(
        X_train_clf_scaled, X_test_clf_scaled, y_train_clf, y_test_clf
    )
    
    best_reg, reg_metrics, reg_results = experiments.evaluate_regression(
        X_train_reg_scaled, X_test_reg_scaled, y_train_reg, y_test_reg
    )
    
    print("\n✓ Model Experiments Module Working!")


if __name__ == "__main__":
    test_model_experiments()
