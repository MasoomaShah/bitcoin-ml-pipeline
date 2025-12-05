from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib

def train_regression(df):
# For regression (predict popularity)
    X = df.drop(columns=['popularity', 'popular'])
    y = df['popularity']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse=mse**0.5
    print("Regression RMSE:", rmse)
    
    joblib.dump(model, "reg_model.pkl")
    return model
