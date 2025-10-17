"""
Data Science Tools - Functions that the AI can call
"""

import os
import json
import uuid
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.tree import DecisionTreeClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, classification_report
import joblib
import logging

logger = logging.getLogger(__name__)


def analyze_dataset(df: pd.DataFrame, analysis_type: str, columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Analyze dataset with various methods
    
    Args:
        df: Pandas DataFrame
        analysis_type: Type of analysis (summary, missing_values, correlations, describe, info)
        columns: Specific columns to analyze
        
    Returns:
        Dict with analysis results and code
    """
    try:
        if df is None or df.empty:
            return {"error": "No data loaded"}
        
        result = {}
        code = ""
        
        if analysis_type == "summary" or analysis_type == "info":
            result = {
                "shape": df.shape,
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "memory_usage": int(df.memory_usage(deep=True).sum()),
                "total_rows": len(df),
                "total_columns": len(df.columns)
            }
            code = "df.info()\ndf.shape\ndf.dtypes"
        
        elif analysis_type == "missing_values":
            missing = df.isnull().sum()
            missing_pct = (missing / len(df) * 100).round(2)
            result = {
                "missing_counts": missing[missing > 0].to_dict(),
                "missing_percentages": missing_pct[missing_pct > 0].to_dict(),
                "total_missing": int(missing.sum())
            }
            code = "df.isnull().sum()\ndf.isnull().sum() / len(df) * 100"
        
        elif analysis_type == "describe":
            cols_to_describe = columns if columns else df.select_dtypes(include=[np.number]).columns.tolist()
            if cols_to_describe:
                desc = df[cols_to_describe].describe()
                result = {
                    "statistics": desc.to_dict(),
                    "columns_analyzed": cols_to_describe
                }
                code = f"df{[cols_to_describe]}.describe()" if columns else "df.describe()"
            else:
                result = {"error": "No numeric columns to describe"}
        
        elif analysis_type == "correlations":
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) > 1:
                corr_matrix = df[numeric_cols].corr()
                result = {
                    "correlation_matrix": corr_matrix.to_dict(),
                    "strong_correlations": _find_strong_correlations(corr_matrix)
                }
                code = "df.corr()"
            else:
                result = {"error": "Need at least 2 numeric columns for correlation"}
        
        result["code"] = code
        return result
    
    except Exception as e:
        logger.error(f"Error in analyze_dataset: {str(e)}")
        return {"error": str(e)}


def _find_strong_correlations(corr_matrix: pd.DataFrame, threshold: float = 0.7) -> List[Dict]:
    """Find strong correlations in correlation matrix"""
    strong_corr = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            corr_val = corr_matrix.iloc[i, j]
            if abs(corr_val) >= threshold:
                strong_corr.append({
                    "var1": corr_matrix.columns[i],
                    "var2": corr_matrix.columns[j],
                    "correlation": round(float(corr_val), 3)
                })
    return strong_corr


def create_plot(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create visualization using Plotly
    
    Args:
        df: Pandas DataFrame
        params: Plot parameters (plot_type, x_column, y_column, title, color_column)
        
    Returns:
        Dict with plot URL and code
    """
    try:
        if df is None or df.empty:
            return {"error": "No data loaded"}
        
        plot_type = params.get("plot_type")
        x_col = params.get("x_column")
        y_col = params.get("y_column")
        title = params.get("title", f"{plot_type.title()} Plot")
        color_col = params.get("color_column")
        
        fig = None
        code = ""
        
        if plot_type == "scatter":
            if not x_col or not y_col:
                return {"error": "Scatter plot requires x_column and y_column"}
            fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=title)
            code = f"px.scatter(df, x='{x_col}', y='{y_col}', title='{title}')"
        
        elif plot_type == "line":
            if not x_col or not y_col:
                return {"error": "Line plot requires x_column and y_column"}
            fig = px.line(df, x=x_col, y=y_col, color=color_col, title=title)
            code = f"px.line(df, x='{x_col}', y='{y_col}', title='{title}')"
        
        elif plot_type == "bar":
            if not x_col:
                return {"error": "Bar plot requires x_column"}
            y_col = y_col or df[x_col].value_counts().index.name
            if y_col:
                fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title)
                code = f"px.bar(df, x='{x_col}', y='{y_col}', title='{title}')"
            else:
                value_counts = df[x_col].value_counts()
                fig = px.bar(x=value_counts.index, y=value_counts.values, title=title)
                code = f"df['{x_col}'].value_counts().plot(kind='bar')"
        
        elif plot_type == "histogram":
            if not x_col:
                return {"error": "Histogram requires x_column"}
            fig = px.histogram(df, x=x_col, color=color_col, title=title)
            code = f"px.histogram(df, x='{x_col}', title='{title}')"
        
        elif plot_type == "box":
            if not y_col:
                return {"error": "Box plot requires y_column"}
            fig = px.box(df, x=x_col, y=y_col, color=color_col, title=title)
            code = f"px.box(df, y='{y_col}', title='{title}')"
        
        elif plot_type == "heatmap":
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) < 2:
                return {"error": "Heatmap requires at least 2 numeric columns"}
            corr = df[numeric_cols].corr()
            fig = px.imshow(corr, text_auto=True, title=title, color_continuous_scale='RdBu_r')
            code = "px.imshow(df.corr(), text_auto=True)"
        
        elif plot_type == "pairplot":
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()[:5]  # Limit to 5 cols
            if len(numeric_cols) < 2:
                return {"error": "Pairplot requires at least 2 numeric columns"}
            fig = px.scatter_matrix(df[numeric_cols], title=title)
            code = f"px.scatter_matrix(df{numeric_cols})"
        
        else:
            return {"error": f"Unknown plot type: {plot_type}"}
        
        # Save plot
        if fig:
            plot_id = str(uuid.uuid4())
            plot_path = f"static/plots/{plot_id}.html"
            os.makedirs("static/plots", exist_ok=True)
            fig.write_html(plot_path)
            
            return {
                "plot_url": f"/static/plots/{plot_id}.html",
                "plot_type": plot_type,
                "code": code
            }
        
        return {"error": "Failed to create plot"}
    
    except Exception as e:
        logger.error(f"Error creating plot: {str(e)}")
        return {"error": str(e)}


def train_ml_model(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Train machine learning model
    
    Args:
        df: Pandas DataFrame
        params: Model parameters (model_type, target_column, feature_columns, test_size)
        
    Returns:
        Dict with model results and code
    """
    try:
        if df is None or df.empty:
            return {"error": "No data loaded"}
        
        model_type = params.get("model_type")
        target_col = params.get("target_column")
        feature_cols = params.get("feature_columns")
        test_size = params.get("test_size", 0.2)
        
        # Auto-select features if not provided
        if not feature_cols:
            feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if target_col in feature_cols:
                feature_cols.remove(target_col)
        
        if not target_col and model_type != "kmeans":
            return {"error": "Target column required for supervised learning"}
        
        if not feature_cols:
            return {"error": "No feature columns available"}
        
        # Prepare data
        X = df[feature_cols].dropna()
        
        if model_type == "kmeans":
            # Clustering
            n_clusters = params.get("n_clusters", 3)
            model = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = model.fit_predict(X)
            
            result = {
                "model_type": "KMeans Clustering",
                "n_clusters": n_clusters,
                "inertia": float(model.inertia_),
                "features_used": feature_cols,
                "cluster_sizes": pd.Series(clusters).value_counts().to_dict()
            }
            code = f"from sklearn.cluster import KMeans\nmodel = KMeans(n_clusters={n_clusters})\nmodel.fit(X)"
        
        else:
            # Supervised learning
            y = df[target_col].dropna()
            
            # Align X and y
            common_idx = X.index.intersection(y.index)
            X = X.loc[common_idx]
            y = y.loc[common_idx]
            
            # Train-test split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            # Select and train model
            if model_type == "linear_regression":
                model = LinearRegression()
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
                result = {
                    "model_type": "Linear Regression",
                    "r2_score": float(r2_score(y_test, y_pred)),
                    "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
                    "features_used": feature_cols,
                    "coefficients": {col: float(coef) for col, coef in zip(feature_cols, model.coef_)},
                    "intercept": float(model.intercept_)
                }
                code = "from sklearn.linear_model import LinearRegression\nmodel = LinearRegression()\nmodel.fit(X_train, y_train)"
            
            elif model_type == "logistic_regression":
                model = LogisticRegression(random_state=42, max_iter=1000)
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
                result = {
                    "model_type": "Logistic Regression",
                    "accuracy": float(accuracy_score(y_test, y_pred)),
                    "features_used": feature_cols,
                    "classes": model.classes_.tolist()
                }
                code = "from sklearn.linear_model import LogisticRegression\nmodel = LogisticRegression()\nmodel.fit(X_train, y_train)"
            
            elif model_type == "random_forest":
                # Detect if classification or regression
                is_classification = y.dtype == 'object' or y.nunique() < 10
                
                if is_classification:
                    model = RandomForestClassifier(random_state=42, n_estimators=100)
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                    
                    result = {
                        "model_type": "Random Forest Classifier",
                        "accuracy": float(accuracy_score(y_test, y_pred)),
                        "features_used": feature_cols,
                        "feature_importance": {col: float(imp) for col, imp in zip(feature_cols, model.feature_importances_)},
                        "n_estimators": 100
                    }
                else:
                    model = RandomForestRegressor(random_state=42, n_estimators=100)
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                    
                    result = {
                        "model_type": "Random Forest Regressor",
                        "r2_score": float(r2_score(y_test, y_pred)),
                        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
                        "features_used": feature_cols,
                        "feature_importance": {col: float(imp) for col, imp in zip(feature_cols, model.feature_importances_)},
                        "n_estimators": 100
                    }
                code = f"from sklearn.ensemble import RandomForest{'Classifier' if is_classification else 'Regressor'}\nmodel = RandomForest{'Classifier' if is_classification else 'Regressor'}(n_estimators=100)\nmodel.fit(X_train, y_train)"
            
            elif model_type == "decision_tree":
                model = DecisionTreeClassifier(random_state=42, max_depth=5)
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
                result = {
                    "model_type": "Decision Tree",
                    "accuracy": float(accuracy_score(y_test, y_pred)),
                    "features_used": feature_cols,
                    "feature_importance": {col: float(imp) for col, imp in zip(feature_cols, model.feature_importances_)},
                    "max_depth": 5
                }
                code = "from sklearn.tree import DecisionTreeClassifier\nmodel = DecisionTreeClassifier(max_depth=5)\nmodel.fit(X_train, y_train)"
            
            else:
                return {"error": f"Unknown model type: {model_type}"}
            
            # Save model
            model_id = str(uuid.uuid4())
            model_path = f"models/{model_id}.pkl"
            os.makedirs("models", exist_ok=True)
            joblib.dump(model, model_path)
            result["model_saved"] = model_path
        
        result["code"] = code
        return result
    
    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        return {"error": str(e)}


def filter_dataframe(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter DataFrame based on conditions
    
    Args:
        df: Pandas DataFrame
        params: Filter parameters (column, condition, value)
        
    Returns:
        Dict with filtered data and code
    """
    try:
        if df is None or df.empty:
            return {"error": "No data loaded"}
        
        column = params.get("column")
        condition = params.get("condition")
        value = params.get("value")
        
        if column not in df.columns:
            return {"error": f"Column '{column}' not found"}
        
        # Convert value to appropriate type
        try:
            if df[column].dtype in [np.int64, np.float64]:
                value = float(value)
        except:
            pass
        
        # Apply filter
        if condition == ">":
            filtered_df = df[df[column] > value]
            code = f"df[df['{column}'] > {value}]"
        elif condition == "<":
            filtered_df = df[df[column] < value]
            code = f"df[df['{column}'] < {value}]"
        elif condition == ">=":
            filtered_df = df[df[column] >= value]
            code = f"df[df['{column}'] >= {value}]"
        elif condition == "<=":
            filtered_df = df[df[column] <= value]
            code = f"df[df['{column}'] <= {value}]"
        elif condition == "==":
            filtered_df = df[df[column] == value]
            code = f"df[df['{column}'] == '{value}']"
        elif condition == "!=":
            filtered_df = df[df[column] != value]
            code = f"df[df['{column}'] != '{value}']"
        elif condition == "contains":
            filtered_df = df[df[column].astype(str).str.contains(str(value), case=False, na=False)]
            code = f"df[df['{column}'].str.contains('{value}', case=False)]"
        else:
            return {"error": f"Unknown condition: {condition}"}
        
        result = {
            "original_shape": df.shape,
            "filtered_shape": filtered_df.shape,
            "rows_removed": len(df) - len(filtered_df),
            "code": code
        }
        
        result["filtered_data"] = filtered_df
        return result
    
    except Exception as e:
        logger.error(f"Error filtering data: {str(e)}")
        return {"error": str(e)}


def preprocess_data(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preprocess data (handle missing values, encode categoricals, scale)
    
    Args:
        df: Pandas DataFrame
        params: Preprocessing parameters
        
    Returns:
        Dict with preprocessed data and code
    """
    try:
        if df is None or df.empty:
            return {"error": "No data loaded"}
        
        result_df = df.copy()
        operations = []
        code_lines = []
        
        # Handle missing values
        if params.get("handle_missing"):
            strategy = params.get("missing_strategy", "drop")
            if strategy == "drop":
                result_df = result_df.dropna()
                code_lines.append("df = df.dropna()")
                operations.append("Dropped rows with missing values")
            elif strategy == "mean":
                numeric_cols = result_df.select_dtypes(include=[np.number]).columns
                result_df[numeric_cols] = result_df[numeric_cols].fillna(result_df[numeric_cols].mean())
                code_lines.append("df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())")
                operations.append("Filled missing numeric values with mean")
            elif strategy == "median":
                numeric_cols = result_df.select_dtypes(include=[np.number]).columns
                result_df[numeric_cols] = result_df[numeric_cols].fillna(result_df[numeric_cols].median())
                code_lines.append("df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())")
                operations.append("Filled missing numeric values with median")
        
        # Encode categorical variables
        if params.get("encode_categorical"):
            cat_cols = result_df.select_dtypes(include=['object']).columns.tolist()
            for col in cat_cols:
                result_df[col] = pd.Categorical(result_df[col]).codes
            code_lines.append("df[cat_cols] = df[cat_cols].apply(lambda x: pd.Categorical(x).codes)")
            operations.append(f"Encoded {len(cat_cols)} categorical columns")
        
        return {
            "operations_performed": operations,
            "original_shape": df.shape,
            "processed_shape": result_df.shape,
            "code": "\n".join(code_lines),
            "processed_data": result_df
        }
    
    except Exception as e:
        logger.error(f"Error preprocessing data: {str(e)}")
        return {"error": str(e)}