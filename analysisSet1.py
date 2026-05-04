import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import joblib

class PregnancyRiskPredictor:
    """
    A pipeline for predicting pregnancy risk level (High/Low) based on maternal health data.
    """

    def __init__(self, model=None, scaler=None, feature_columns=None):
        self.model = model
        self.scaler = scaler
        self.feature_columns = feature_columns
        self.skewness_dict = {
            'sistolicki_krvni_tlak': 0.2571,
            'dijastolicki_krvni_tlak': 0.3772,
            'glukoza_u_krvi': 1.5781,
            'BMI': 0.4574,
            'komplikacije_u_proslosti': 1.7071,
            'dijabetes': 0.9339,
            'otkucaji_srca': 0.2097
        }

    def load_data(self, filepath):
        """Load dataset from CSV."""
        df = pd.read_csv(filepath)
        return df

    def preprocess(self, df, fit_scaler=False):
        """
        Apply all necessary preprocessing steps.
        - Convert Fahrenheit to Celsius
        - Impute missing numeric values (mean/median based on skewness)
        - Drop rows missing target
        - Encode target (High->1, Low->0)
        - Remove outlier (age 325) and restrict age 15-50
        - Optionally fit a StandardScaler on features (for later use)
        Returns processed X, y.
        """
        df = df.copy()

        # Convert temperature
        df['tjelesna_temp'] = ((df['tjelesna_temp'] - 32) * 5/9).round(2)

        # Impute numeric columns based on skewness
        for var, skew_val in self.skewness_dict.items():
            if var not in df.columns:
                continue
            if abs(skew_val) > 1:
                fill_value = df[var].median(skipna=True)
            else:
                fill_value = df[var].mean(skipna=True)
            df[var] = df[var].fillna(fill_value)

        # Drop rows where target is missing
        df = df.dropna(subset=['nivo_rizika'])

        # Encode target
        df['nivo_rizika'] = df['nivo_rizika'].map({'High': 1, 'Low': 0})

        # Remove age outlier (325) and restrict age range 15-50
        df = df[df['dob'] != 325]
        df = df[(df['dob'] >= 15) & (df['dob'] <= 50)]

        # Separate features and target
        X = df.drop(columns=['nivo_rizika'])
        y = df['nivo_rizika']

        # Store feature names
        self.feature_columns = X.columns.tolist()

        # Optionally fit scaler (for models that need scaling, though Gradient Boosting does not)
        if fit_scaler:
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            return X_scaled, y
        else:
            return X, y

    def train(self, X, y, model_params=None):
        """Train a Gradient Boosting classifier."""
        if model_params is None:
            model_params = {'n_estimators': 100, 'random_state': 42}
        self.model = GradientBoostingClassifier(**model_params)
        self.model.fit(X, y)
        return self.model

    def evaluate(self, X_test, y_test):
        """Evaluate the trained model on a test set."""
        if self.model is None:
            raise ValueError("Model not trained yet. Call train() first.")
        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_proba),
            'confusion_matrix': confusion_matrix(y_test, y_pred)
        }
        return metrics

    def cross_validate(self, X, y, cv=5):
        """Perform stratified cross-validation and return scores."""
        if self.model is None:
            self.model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        scoring = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
        cv_results = cross_validate(self.model, X, y, cv=cv, scoring=scoring, return_train_score=False)
        results = {f'mean_{m}': np.mean(cv_results[f'test_{m}']) for m in scoring}
        results.update({f'std_{m}': np.std(cv_results[f'test_{m}']) for m in scoring})
        return results

    def predict(self, X_new):
        """Predict risk for new samples. X_new must have same columns as training data."""
        if self.model is None:
            raise ValueError("Model not trained.")
        # If scaler exists, apply it (though not needed for Gradient Boosting, kept for consistency)
        if self.scaler is not None:
            X_new = self.scaler.transform(X_new)
        return self.model.predict(X_new)

    def predict_proba(self, X_new):
        """Return probability of High risk (class 1)."""
        if self.model is None:
            raise ValueError("Model not trained.")
        if self.scaler is not None:
            X_new = self.scaler.transform(X_new)
        return self.model.predict_proba(X_new)[:, 1]

    def feature_importance(self):
        """Return feature importance DataFrame."""
        if self.model is None:
            raise ValueError("Model not trained.")
        imp = pd.DataFrame({
            'Feature': self.feature_columns,
            'Importance': self.model.feature_importances_
        }).sort_values('Importance', ascending=False)
        return imp

    def save_model(self, filepath):
        """Save model and scaler to disk."""
        joblib.dump({'model': self.model, 'scaler': self.scaler, 'feature_columns': self.feature_columns}, filepath)

    def load_model(self, filepath):
        """Load model and scaler from disk."""
        data = joblib.load(filepath)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_columns = data['feature_columns']


# ======================= Example usage =======================
if __name__ == "__main__":
    # Initialize predictor
    predictor = PregnancyRiskPredictor()

    # Load and preprocess data
    df = predictor.load_data('datasets/dataset1.csv')
    X, y = predictor.preprocess(df, fit_scaler=False)   # scaler not needed for tree-based model

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)

    # Train model
    predictor.train(X_train, y_train)

    # Evaluate on test set
    metrics = predictor.evaluate(X_test, y_test)
    print("Test set performance:")
    for k, v in metrics.items():
        if k != 'confusion_matrix':
            print(f"  {k}: {v:.4f}")
    print("Confusion matrix:\n", metrics['confusion_matrix'])

    # Cross-validation
    cv_results = predictor.cross_validate(X, y, cv=5)
    print("\n5-fold CV results:")
    for k in ['mean_accuracy', 'mean_precision', 'mean_recall', 'mean_f1', 'mean_roc_auc']:
        print(f"  {k}: {cv_results[k]:.4f} (+/- {cv_results[k.replace('mean','std')]:.4f})")

    # Feature importance
    print("\nFeature importance:")
    print(predictor.feature_importance())

    # Save model for later use
    predictor.save_model('pregnancy_risk_model.pkl')

    # Load model (example)
    predictor2 = PregnancyRiskPredictor()
    predictor2.load_model('pregnancy_risk_model.pkl')
    # Now predictor2 can be used for predictions on new data