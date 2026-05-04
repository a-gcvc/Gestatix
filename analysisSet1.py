#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analysis script for pregnancy risk prediction.
Reusable functions and main pipeline.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import skew, kurtosis
from sklearn.model_selection import train_test_split, cross_validate, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, confusion_matrix)
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline

# ==============================
# Data loading and preprocessing
# ==============================

def load_data(filepath):
    """Load dataset from CSV."""
    return pd.read_csv(filepath)

def convert_temperature(df, col='tjelesna_temp'):
    """Convert Fahrenheit to Celsius."""
    df[col] = ((df[col] - 32) * 5/9).round(2)
    return df

def impute_numerical(df, skewness_dict, threshold=1.0):
    """
    Impute missing values for numerical columns based on skewness.
    If |skew| > threshold -> median, else mean.
    """
    for var, skew_val in skewness_dict.items():
        if var not in df.columns:
            continue
        if abs(skew_val) > threshold:
            fill_val = df[var].median(skipna=True)
        else:
            fill_val = df[var].mean(skipna=True)
        df[var] = df[var].fillna(fill_val)
    return df

def impute_categorical_mode(df, col):
    """Impute missing categorical values with mode."""
    mode_val = df[col].mode()[0]
    df[col] = df[col].fillna(mode_val)
    return df

def encode_target(df, col='nivo_rizika', mapping=None):
    """Encode target variable: map High->1, Low->0."""
    if mapping is None:
        mapping = {'High': 1, 'Low': 0}
    df[col] = df[col].map(mapping)
    return df

def preprocess_data(df):
    """
    Full preprocessing pipeline:
    - temperature conversion
    - imputation (numerical based on skewness, categorical with mode)
    - encode target
    - return features X and target y
    """
    # Convert temperature
    df = convert_temperature(df)

    # Skewness values (pre‑computed or compute on the fly)
    skewness_dict = {
        'sistolicki_krvni_tlak': 0.2571,
        'dijastolicki_krvni_tlak': 0.3772,
        'glukoza_u_krvi': 1.5781,
        'BMI': 0.4574,
        'komplikacije_u_proslosti': 1.7071,
        'dijabetes': 0.9339,
        'otkucaji_srca': 0.2097
    }
    df = impute_numerical(df, skewness_dict, threshold=1.0)

    # Impute categorical target with mode
    df = impute_categorical_mode(df, 'nivo_rizika')

    # Encode target
    df = encode_target(df, 'nivo_rizika')

    # Separate features and target
    X = df.drop(columns=['nivo_rizika'])
    y = df['nivo_rizika']
    return X, y

# ==============================
# Model evaluation utilities
# ==============================

def evaluate_classifier(model, X_train, y_train, X_test, y_test):
    """Train and evaluate classifier, return metrics dictionary."""
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

    metrics = {
        "Accuracy": accuracy_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred, zero_division=0),
        "Recall": recall_score(y_test, y_pred, zero_division=0),
        "F1 Score": f1_score(y_test, y_pred, zero_division=0),
        "ROC AUC": roc_auc_score(y_test, y_proba) if y_proba is not None else None
    }
    return metrics, y_pred, y_proba

def cross_validate_classifier(model, X, y, cv=5):
    """Perform 5‑fold cross‑validation and return mean scores."""
    scoring = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
    scores = cross_validate(model, X, y, cv=cv, scoring=scoring)
    results = {f"test_{metric}": scores[f"test_{metric}"].mean() for metric in scoring}
    return results

def get_classifiers():
    """Return dictionary of classifiers (some wrapped with scaler)."""
    classifiers = {
        "Logistic Regression": LogisticRegression(max_iter=1000),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
        "Naive Bayes": GaussianNB()
    }
    # Models that need scaling
    scaled_models = {
        "SVM (RBF)": Pipeline([('scaler', StandardScaler()),
                               ('svm', SVC(probability=True, random_state=42))]),
        "k-NN (k=5)": Pipeline([('scaler', StandardScaler()),
                                ('knn', KNeighborsClassifier(n_neighbors=5))])
    }
    return {**classifiers, **scaled_models}

# ==============================
# Visualization functions
# ==============================

def plot_histograms(df, numeric_cols, figsize=(15, 10), layout=(4, 3)):
    """Plot histograms for given numeric columns."""
    df[numeric_cols].hist(bins=15, figsize=figsize, layout=layout,
                          color='skyblue', edgecolor='black')
    plt.suptitle('Raspodjela numeričkih varijabli – histogrami', fontsize=16, y=1.02)
    plt.tight_layout()
    plt.show()

def plot_density_curves(df, cont_cols, figsize=(16, 8), subplot_shape=(2, 4)):
    """Plot density curves (KDE) for continuous variables."""
    fig, axes = plt.subplots(*subplot_shape, figsize=figsize)
    axes = axes.flatten()
    for i, var in enumerate(cont_cols):
        sns.histplot(df[var], kde=True, bins=20, ax=axes[i], color='coral')
        axes[i].set_title(var)
    for j in range(len(cont_cols), len(axes)):
        axes[j].set_visible(False)
    plt.suptitle('Distribucija s KDE (procjena gustoće vjerojatnosti)', fontsize=14)
    plt.tight_layout()
    plt.show()

def plot_correlation_heatmap(df, figsize=(14, 10)):
    """Plot correlation heatmap."""
    corr = df.corr(numeric_only=True)
    plt.figure(figsize=figsize)
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
    plt.title('Korelacijska matrica varijabli trudnoće')
    plt.show()

def plot_pie_chart(df, col):
    """Plot pie chart for a categorical variable."""
    data = df[col].dropna()
    data.value_counts().plot(kind='pie', autopct='%1.1f%%',
                             colors=['#66b3ff','#ff9999'],
                             startangle=90, explode=(0.05, 0))
    plt.title(f'Distribucija {col} (bez missing vrijednosti)')
    plt.ylabel('')
    plt.show()

def plot_confusion_matrices(models, X_train, X_test, y_train, y_test, scaler=None):
    """
    Plot confusion matrices for all models.
    If scaler is None, uses original X_train, X_test; otherwise scales them.
    """
    n_models = len(models)
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    axes = axes.flatten()

    for idx, (name, model) in enumerate(models.items()):
        # Use scaled data if model is SVM or k-NN
        if scaler and name in ["SVM (RBF)", "k-NN (k=5)"]:
            X_tr = scaler.fit_transform(X_train)
            X_te = scaler.transform(X_test)
        else:
            X_tr, X_te = X_train, X_test

        model.fit(X_tr, y_train)
        y_pred = model.predict(X_te)
        cm = confusion_matrix(y_test, y_pred)

        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx],
                    xticklabels=['Low', 'High'], yticklabels=['Low', 'High'])
        axes[idx].set_title(name)
        axes[idx].set_xlabel('Predicted')
        axes[idx].set_ylabel('Actual')

    for j in range(len(models), len(axes)):
        axes[j].axis('off')
    plt.tight_layout()
    plt.show()

# ==============================
# Main execution
# ==============================

def main():
    # 1. Load and preprocess
    df = load_data('datasets/dataset1.csv')
    X, y = preprocess_data(df)

    # 2. Train / test split (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=0, stratify=y
    )

    # 3. Optionally scale for models that need it (done inside classifiers pipeline)
    #    but we keep original for logistic, tree, etc.
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 4. Get classifiers
    classifiers = get_classifiers()

    # 5. Evaluate each model on test set
    results = {}
    for name, clf in classifiers.items():
        print(f"\nEvaluacija: {name}")
        if name in ["SVM (RBF)", "k-NN (k=5)"]:
            metrics, _, _ = evaluate_classifier(clf, X_train_scaled, y_train,
                                                 X_test_scaled, y_test)
        else:
            metrics, _, _ = evaluate_classifier(clf, X_train, y_train,
                                                 X_test, y_test)
        results[name] = metrics
        for metric, value in metrics.items():
            if value is not None:
                print(f"  {metric}: {value:.4f}")
            else:
                print(f"  {metric}: nije podržan")

    # 6. Cross‑validation on entire dataset
    print("\n--- CROSS-VALIDATION (5-fold) ---")
    for name, clf in classifiers.items():
        print(f"\n{name}:")
        cv_res = cross_validate_classifier(clf, X, y, cv=5)
        for k, v in cv_res.items():
            print(f"  {k}: {v:.4f}")

    # 7. Confusion matrices (using scaled data for SVM/k‑NN)
    plot_confusion_matrices(classifiers, X_train, X_test, y_train, y_test, scaler)

    # 8. Visualisations (optional)
    # Uncomment if needed:
    # numeric_cols = [col for col in X.columns if X[col].dtype in ['int64','float64']]
    # plot_histograms(df, numeric_cols)
    # cont_cols = ['dob', 'sistolicki_krvni_tlak', 'dijastolicki_krvni_tlak',
    #              'glukoza_u_krvi', 'tjelesna_temp', 'BMI', 'otkucaji_srca']
    # plot_density_curves(df, cont_cols)
    # plot_correlation_heatmap(df)
    # plot_pie_chart(df, 'nivo_rizika')

    # 9. Output best model
    best_model = max(results.keys(), key=lambda k: results[k]['F1 Score'])
    print(f"\nNajbolji algoritam po F1 score: {best_model}")

if __name__ == "__main__":
    main()