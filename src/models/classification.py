from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

def train_classification(df):
# For regression (predict popularity)
    X = df.drop(columns=['popularity', 'popular'])
    y = df['popular']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print("Classification Accuracy:", acc)
    
    joblib.dump(model, "clf_model.pkl")
    return model
