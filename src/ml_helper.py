import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.svm import SVC, SVR
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report, confusion_matrix
from sklearn.feature_selection import SelectKBest, f_classif, f_regression
import joblib
import os
from typing import Dict, List, Tuple, Any

class MLHelper:
    """
    Machine Learning helper class for model training and evaluation
    """
    
    def __init__(self):
        self.trained_models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_selectors = {}
    
    def suggest_models(self, df: pd.DataFrame, target_column: str = None) -> Dict[str, Any]:
        """
        Suggest appropriate models based on the dataset characteristics
        
        Args:
            df: Input DataFrame
            target_column: Name of target column (if None, will try to detect)
            
        Returns:
            Dictionary with model suggestions and dataset analysis
        """
        if df is None or df.empty:
            return {'error': 'No valid dataset provided'}
        
        analysis = {
            'dataset_info': {
                'shape': df.shape,
                'columns': list(df.columns),
                'numeric_columns': list(df.select_dtypes(include=[np.number]).columns),
                'categorical_columns': list(df.select_dtypes(include=['object', 'category']).columns)
            },
            'suggested_models': []
        }
        
        # If no target column specified, suggest based on data characteristics
        if target_column is None:
            analysis['suggestions'] = self._suggest_based_on_data(df)
            return analysis
        
        if target_column not in df.columns:
            return {'error': f'Target column {target_column} not found in dataset'}
        
        target_series = df[target_column]
        
        # Determine problem type
        if pd.api.types.is_numeric_dtype(target_series):
            # Check if it's regression or classification
            unique_values = target_series.nunique()
            if unique_values <= 10 and target_series.dtype in ['int64', 'int32']:
                problem_type = 'classification'
            else:
                problem_type = 'regression'
        else:
            problem_type = 'classification'
        
        analysis['problem_type'] = problem_type
        analysis['target_info'] = {
            'unique_values': target_series.nunique(),
            'null_count': target_series.isnull().sum(),
            'dtype': str(target_series.dtype)
        }
        
        # Suggest models based on problem type
        if problem_type == 'classification':
            analysis['suggested_models'] = [
                {
                    'name': 'Random Forest Classifier',
                    'description': 'Great for most classification problems, handles mixed data types well',
                    'pros': ['Handles missing values', 'Feature importance', 'Less overfitting'],
                    'suitable_for': 'Medium to large datasets with mixed features'
                },
                {
                    'name': 'Logistic Regression',
                    'description': 'Simple and interpretable for binary/multiclass classification',
                    'pros': ['Fast training', 'Interpretable', 'Good baseline'],
                    'suitable_for': 'Linear relationships, smaller datasets'
                },
                {
                    'name': 'Support Vector Classifier',
                    'description': 'Effective for high-dimensional data',
                    'pros': ['Works well with high dimensions', 'Memory efficient'],
                    'suitable_for': 'Text classification, high-dimensional data'
                }
            ]
        else:
            analysis['suggested_models'] = [
                {
                    'name': 'Random Forest Regressor',
                    'description': 'Robust regression model for continuous targets',
                    'pros': ['Handles non-linear relationships', 'Feature importance', 'Less overfitting'],
                    'suitable_for': 'Most regression problems'
                },
                {
                    'name': 'Linear Regression',
                    'description': 'Simple and interpretable regression model',
                    'pros': ['Fast', 'Interpretable', 'Good baseline'],
                    'suitable_for': 'Linear relationships between features and target'
                },
                {
                    'name': 'Support Vector Regressor',
                    'description': 'Effective for complex non-linear relationships',
                    'pros': ['Handles non-linearity', 'Robust to outliers'],
                    'suitable_for': 'Complex relationships, smaller datasets'
                }
            ]
        
        return analysis
    
    def prepare_data(self, df: pd.DataFrame, target_column: str, test_size: float = 0.2) -> Dict[str, Any]:
        """
        Prepare data for machine learning
        
        Args:
            df: Input DataFrame
            target_column: Name of target column
            test_size: Proportion of dataset for testing
            
        Returns:
            Dictionary with prepared data splits
        """
        if target_column not in df.columns:
            return {'error': f'Target column {target_column} not found'}
        
        # Separate features and target
        X = df.drop(columns=[target_column])
        y = df[target_column]
        
        # Handle missing values in target
        if y.isnull().any():
            missing_count = y.isnull().sum()
            X = X[~y.isnull()]
            y = y.dropna()
            print(f"Removed {missing_count} rows with missing target values")
        
        # Encode categorical variables
        X_processed = X.copy()
        categorical_columns = X.select_dtypes(include=['object', 'category']).columns
        
        for col in categorical_columns:
            if col not in self.encoders:
                self.encoders[col] = LabelEncoder()
            X_processed[col] = self.encoders[col].fit_transform(X[col].astype(str))
        
        # Handle missing values in features
        X_processed = X_processed.fillna(X_processed.mean())
        
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X_processed, y, test_size=test_size, random_state=42
        )
        
        # Scale numerical features
        numerical_columns = X_processed.select_dtypes(include=[np.number]).columns
        if len(numerical_columns) > 0:
            scaler = StandardScaler()
            X_train[numerical_columns] = scaler.fit_transform(X_train[numerical_columns])
            X_test[numerical_columns] = scaler.transform(X_test[numerical_columns])
            self.scalers['features'] = scaler
        
        return {
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'feature_names': list(X_processed.columns),
            'target_name': target_column
        }
    
    def train_model(self, model_name: str, data: Dict, **kwargs) -> Dict[str, Any]:
        """
        Train a machine learning model
        
        Args:
            model_name: Name of the model to train
            data: Prepared data dictionary from prepare_data
            **kwargs: Additional model parameters
            
        Returns:
            Training results and model performance
        """
        X_train = data['X_train']
        X_test = data['X_test']
        y_train = data['y_train']
        y_test = data['y_test']
        
        # Initialize model
        models = {
            'random_forest_classifier': RandomForestClassifier(random_state=42, **kwargs),
            'random_forest_regressor': RandomForestRegressor(random_state=42, **kwargs),
            'linear_regression': LinearRegression(**kwargs),
            'logistic_regression': LogisticRegression(random_state=42, max_iter=1000, **kwargs),
            'svc': SVC(random_state=42, **kwargs),
            'svr': SVR(**kwargs)
        }
        
        model_key = model_name.lower().replace(' ', '_')
        if model_key not in models:
            return {'error': f'Model {model_name} not supported'}
        
        model = models[model_key]
        
        try:
            # Train the model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            is_classifier = 'classifier' in model_key or model_key in ['logistic_regression', 'svc']
            
            if is_classifier:
                accuracy = accuracy_score(y_test, y_pred)
                metrics = {
                    'accuracy': accuracy,
                    'classification_report': classification_report(y_test, y_pred, output_dict=True),
                    'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
                }
            else:
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                
                # Calculate R² score
                r2 = model.score(X_test, y_test)
                
                metrics = {
                    'mse': mse,
                    'rmse': rmse,
                    'r2_score': r2,
                    'mean_absolute_error': np.mean(np.abs(y_test - y_pred))
                }
            
            # Feature importance (if available)
            feature_importance = None
            if hasattr(model, 'feature_importances_'):
                feature_importance = dict(zip(data['feature_names'], model.feature_importances_))
                # Sort by importance
                feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
            
            # Save the model
            model_id = f"{model_key}_{len(self.trained_models)}"
            self.trained_models[model_id] = {
                'model': model,
                'model_name': model_name,
                'feature_names': data['feature_names'],
                'target_name': data['target_name'],
                'metrics': metrics,
                'feature_importance': feature_importance
            }
            
            return {
                'model_id': model_id,
                'model_name': model_name,
                'metrics': metrics,
                'feature_importance': feature_importance,
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
        
        except Exception as e:
            return {'error': f'Training failed: {str(e)}'}
    
    def make_predictions(self, model_id: str, X_new: pd.DataFrame) -> Dict[str, Any]:
        """
        Make predictions using a trained model
        
        Args:
            model_id: ID of the trained model
            X_new: New data for predictions
            
        Returns:
            Predictions and confidence scores
        """
        if model_id not in self.trained_models:
            return {'error': f'Model {model_id} not found'}
        
        model_info = self.trained_models[model_id]
        model = model_info['model']
        
        try:
            # Prepare the new data (same preprocessing as training)
            X_processed = X_new.copy()
            
            # Apply same encoders
            for col in X_processed.select_dtypes(include=['object', 'category']).columns:
                if col in self.encoders:
                    X_processed[col] = self.encoders[col].transform(X_new[col].astype(str))
            
            # Handle missing values
            X_processed = X_processed.fillna(X_processed.mean())
            
            # Apply same scaling
            if 'features' in self.scalers:
                numerical_columns = X_processed.select_dtypes(include=[np.number]).columns
                X_processed[numerical_columns] = self.scalers['features'].transform(X_processed[numerical_columns])
            
            # Make predictions
            predictions = model.predict(X_processed)
            
            # Get prediction probabilities for classifiers
            probabilities = None
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(X_processed)
            
            return {
                'predictions': predictions.tolist(),
                'probabilities': probabilities.tolist() if probabilities is not None else None,
                'model_name': model_info['model_name'],
                'feature_names': model_info['feature_names']
            }
        
        except Exception as e:
            return {'error': f'Prediction failed: {str(e)}'}
    
    def save_model(self, model_id: str, filepath: str) -> str:
        """Save a trained model to disk"""
        if model_id not in self.trained_models:
            return f'Model {model_id} not found'
        
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            joblib.dump(self.trained_models[model_id], filepath)
            return f'Model saved successfully to {filepath}'
        except Exception as e:
            return f'Failed to save model: {str(e)}'
    
    def load_model(self, filepath: str, model_id: str = None) -> str:
        """Load a trained model from disk"""
        try:
            model_info = joblib.load(filepath)
            if model_id is None:
                model_id = f"loaded_model_{len(self.trained_models)}"
            self.trained_models[model_id] = model_info
            return f'Model loaded successfully as {model_id}'
        except Exception as e:
            return f'Failed to load model: {str(e)}'
    
    def compare_models(self, model_ids: List[str]) -> Dict[str, Any]:
        """Compare performance of multiple trained models"""
        if not model_ids:
            return {'error': 'No model IDs provided'}
        
        comparison = {'models': []}
        
        for model_id in model_ids:
            if model_id in self.trained_models:
                model_info = self.trained_models[model_id]
                comparison['models'].append({
                    'model_id': model_id,
                    'model_name': model_info['model_name'],
                    'metrics': model_info['metrics']
                })
        
        return comparison
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get detailed information about a trained model"""
        if model_id not in self.trained_models:
            return {'error': f'Model {model_id} not found'}
        
        model_info = self.trained_models[model_id]
        return {
            'model_id': model_id,
            'model_name': model_info['model_name'],
            'feature_names': model_info['feature_names'],
            'target_name': model_info['target_name'],
            'metrics': model_info['metrics'],
            'feature_importance': model_info['feature_importance']
        }
    
    def _suggest_based_on_data(self, df: pd.DataFrame) -> List[str]:
        """Suggest analysis approaches based on data characteristics"""
        suggestions = []
        
        numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
        categorical_cols = len(df.select_dtypes(include=['object', 'category']).columns)
        
        if numeric_cols > 0:
            suggestions.append("Correlation analysis between numeric variables")
            suggestions.append("Distribution analysis of numeric columns")
        
        if categorical_cols > 0:
            suggestions.append("Frequency analysis of categorical variables")
        
        if numeric_cols > 1:
            suggestions.append("Principal Component Analysis (PCA) for dimensionality reduction")
        
        if df.shape[0] > 100:
            suggestions.append("Consider clustering analysis to find patterns")
        
        suggestions.append("Identify potential target variables for supervised learning")
        
        return suggestions