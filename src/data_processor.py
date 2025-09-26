import pandas as pd
import numpy as np
import json
import os
from typing import Dict, List, Optional, Union

class DataProcessor:
    """
    Handle data loading, processing, and manipulation tasks
    """
    
    def __init__(self):
        self.current_data = None
        self.data_cache = {}
        self.processing_history = []
    
    def load_data(self, filepath: str) -> pd.DataFrame:
        """
        Load data from various file formats
        
        Args:
            filepath: Path to the data file
            
        Returns:
            Loaded DataFrame
        """
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                # Try in data directory
                data_path = os.path.join('data', filepath)
                if os.path.exists(data_path):
                    filepath = data_path
                else:
                    raise FileNotFoundError(f"File not found: {filepath}")
            
            # Get file extension
            _, ext = os.path.splitext(filepath.lower())
            
            # Load based on file type
            if ext == '.csv':
                self.current_data = pd.read_csv(filepath)
            elif ext == '.json':
                self.current_data = pd.read_json(filepath)
            elif ext in ['.xlsx', '.xls']:
                self.current_data = pd.read_excel(filepath)
            elif ext == '.parquet':
                self.current_data = pd.read_parquet(filepath)
            else:
                raise ValueError(f"Unsupported file format: {ext}")
            
            # Add to processing history
            self.processing_history.append({
                'action': 'load_data',
                'filepath': filepath,
                'shape': self.current_data.shape
            })
            
            return self.current_data
        
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}")
    
    def get_data_info(self) -> Dict:
        """Get basic information about the current dataset"""
        if self.current_data is None:
            return {'error': 'No data loaded'}
        
        return {
            'shape': self.current_data.shape,
            'columns': self.current_data.columns.tolist(),
            'data_types': self.current_data.dtypes.to_dict(),
            'memory_usage': self.current_data.memory_usage(deep=True).sum(),
            'missing_values': self.current_data.isnull().sum().to_dict(),
            'duplicates': self.current_data.duplicated().sum()
        }
    
    def clean_data(self, operations: List[str] = None) -> Dict:
        """
        Clean the dataset based on specified operations
        
        Args:
            operations: List of cleaning operations to perform
            
        Returns:
            Summary of cleaning operations performed
        """
        if self.current_data is None:
            return {'error': 'No data loaded'}
        
        if operations is None:
            operations = ['remove_duplicates', 'handle_missing', 'fix_dtypes']
        
        cleaning_summary = {'operations_performed': []}
        original_shape = self.current_data.shape
        
        for operation in operations:
            if operation == 'remove_duplicates':
                before = len(self.current_data)
                self.current_data = self.current_data.drop_duplicates()
                after = len(self.current_data)
                if before != after:
                    cleaning_summary['operations_performed'].append(
                        f"Removed {before - after} duplicate rows"
                    )
            
            elif operation == 'handle_missing':
                missing_summary = self._handle_missing_values()
                if missing_summary:
                    cleaning_summary['operations_performed'].extend(missing_summary)
            
            elif operation == 'fix_dtypes':
                dtype_summary = self._fix_data_types()
                if dtype_summary:
                    cleaning_summary['operations_performed'].extend(dtype_summary)
        
        cleaning_summary['shape_change'] = f"{original_shape} → {self.current_data.shape}"
        
        # Add to processing history
        self.processing_history.append({
            'action': 'clean_data',
            'operations': operations,
            'summary': cleaning_summary
        })
        
        return cleaning_summary
    
    def _handle_missing_values(self) -> List[str]:
        """Handle missing values in the dataset"""
        operations = []
        
        for column in self.current_data.columns:
            missing_count = self.current_data[column].isnull().sum()
            if missing_count > 0:
                missing_pct = (missing_count / len(self.current_data)) * 100
                
                if missing_pct > 50:
                    # Drop columns with >50% missing values
                    self.current_data = self.current_data.drop(columns=[column])
                    operations.append(f"Dropped column '{column}' ({missing_pct:.1f}% missing)")
                
                elif pd.api.types.is_numeric_dtype(self.current_data[column]):
                    # Fill numeric columns with median
                    median_val = self.current_data[column].median()
                    self.current_data[column].fillna(median_val, inplace=True)
                    operations.append(f"Filled missing values in '{column}' with median ({median_val})")
                
                else:
                    # Fill categorical columns with mode
                    mode_val = self.current_data[column].mode()
                    if not mode_val.empty:
                        self.current_data[column].fillna(mode_val[0], inplace=True)
                        operations.append(f"Filled missing values in '{column}' with mode ('{mode_val[0]}')")
        
        return operations
    
    def _fix_data_types(self) -> List[str]:
        """Optimize data types for better memory usage"""
        operations = []
        
        for column in self.current_data.columns:
            col_data = self.current_data[column]
            original_dtype = str(col_data.dtype)
            
            # Try to optimize numeric columns
            if pd.api.types.is_numeric_dtype(col_data):
                # Check if it's actually integers stored as float
                if col_data.dtype == 'float64' and col_data.dropna().apply(lambda x: x.is_integer()).all():
                    self.current_data[column] = col_data.astype('int64')
                    operations.append(f"Changed '{column}' from {original_dtype} to int64")
                
                # Downcast integers
                elif col_data.dtype in ['int64', 'int32']:
                    downcast_int = pd.to_numeric(col_data, downcast='integer')
                    if downcast_int.dtype != col_data.dtype:
                        self.current_data[column] = downcast_int
                        operations.append(f"Downcasted '{column}' from {original_dtype} to {downcast_int.dtype}")
                
                # Downcast floats
                elif col_data.dtype in ['float64', 'float32']:
                    downcast_float = pd.to_numeric(col_data, downcast='float')
                    if downcast_float.dtype != col_data.dtype:
                        self.current_data[column] = downcast_float
                        operations.append(f"Downcasted '{column}' from {original_dtype} to {downcast_float.dtype}")
            
            # Convert object columns that might be categorical
            elif col_data.dtype == 'object':
                unique_ratio = col_data.nunique() / len(col_data)
                if unique_ratio < 0.5:  # Less than 50% unique values
                    self.current_data[column] = col_data.astype('category')
                    operations.append(f"Changed '{column}' from object to category")
        
        return operations
    
    def get_column_stats(self, column: str) -> Dict:
        """Get detailed statistics for a specific column"""
        if self.current_data is None or column not in self.current_data.columns:
            return {'error': f'Column {column} not found'}
        
        col_data = self.current_data[column]
        stats = {
            'name': column,
            'dtype': str(col_data.dtype),
            'count': len(col_data),
            'non_null': col_data.count(),
            'null_count': col_data.isnull().sum(),
            'null_percentage': (col_data.isnull().sum() / len(col_data)) * 100,
            'unique_count': col_data.nunique(),
            'unique_percentage': (col_data.nunique() / len(col_data)) * 100
        }
        
        if pd.api.types.is_numeric_dtype(col_data):
            stats.update({
                'mean': col_data.mean(),
                'median': col_data.median(),
                'mode': col_data.mode().tolist()[:3],  # Top 3 modes
                'std': col_data.std(),
                'var': col_data.var(),
                'min': col_data.min(),
                'max': col_data.max(),
                'q25': col_data.quantile(0.25),
                'q75': col_data.quantile(0.75),
                'skewness': col_data.skew(),
                'kurtosis': col_data.kurtosis()
            })
        else:
            # For categorical data
            value_counts = col_data.value_counts().head(10)
            stats.update({
                'top_values': value_counts.to_dict(),
                'mode': col_data.mode().tolist()[:3]
            })
        
        return stats
    
    def filter_data(self, conditions: Dict) -> Dict:
        """
        Filter data based on conditions
        
        Args:
            conditions: Dictionary of column: condition pairs
            
        Returns:
            Summary of filtering operation
        """
        if self.current_data is None:
            return {'error': 'No data loaded'}
        
        original_shape = self.current_data.shape
        
        for column, condition in conditions.items():
            if column not in self.current_data.columns:
                continue
            
            # Parse condition (simplified for now)
            if isinstance(condition, dict):
                if 'min' in condition:
                    self.current_data = self.current_data[self.current_data[column] >= condition['min']]
                if 'max' in condition:
                    self.current_data = self.current_data[self.current_data[column] <= condition['max']]
                if 'equals' in condition:
                    self.current_data = self.current_data[self.current_data[column] == condition['equals']]
                if 'not_equals' in condition:
                    self.current_data = self.current_data[self.current_data[column] != condition['not_equals']]
        
        # Add to processing history
        self.processing_history.append({
            'action': 'filter_data',
            'conditions': conditions,
            'shape_change': f"{original_shape} → {self.current_data.shape}"
        })
        
        return {
            'original_shape': original_shape,
            'new_shape': self.current_data.shape,
            'rows_removed': original_shape[0] - self.current_data.shape[0]
        }
    
    def create_sample_data(self, filename: str = 'sample_data.csv', rows: int = 1000):
        """Create sample dataset for testing"""
        np.random.seed(42)
        
        data = {
            'age': np.random.randint(18, 80, rows),
            'income': np.random.normal(50000, 15000, rows),
            'education': np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], rows, p=[0.4, 0.35, 0.2, 0.05]),
            'experience': np.random.randint(0, 40, rows),
            'salary': np.random.normal(65000, 20000, rows),
            'department': np.random.choice(['IT', 'Finance', 'HR', 'Marketing', 'Operations'], rows),
            'satisfaction': np.random.uniform(1, 10, rows),
            'remote_work': np.random.choice([True, False], rows, p=[0.3, 0.7])
        }
        
        # Add some correlations
        for i in range(rows):
            # Salary should correlate with experience and education
            if data['education'][i] == 'PhD':
                data['salary'][i] *= 1.3
            elif data['education'][i] == 'Master':
                data['salary'][i] *= 1.15
            
            data['salary'][i] += data['experience'][i] * 1000
            
            # Income should correlate with salary
            data['income'][i] = data['salary'][i] * 0.8 + np.random.normal(0, 5000)
        
        # Add some missing values
        missing_indices = np.random.choice(rows, int(rows * 0.05), replace=False)
        for idx in missing_indices:
            data['satisfaction'][idx] = np.nan
        
        df = pd.DataFrame(data)
        
        # Save to file
        os.makedirs('data', exist_ok=True)
        filepath = os.path.join('data', filename)
        df.to_csv(filepath, index=False)
        
        return f"Sample dataset created: {filepath} with {rows} rows"
    
    def get_processing_history(self) -> List[Dict]:
        """Get history of data processing operations"""
        return self.processing_history
    
    def export_data(self, filepath: str, format: str = 'csv') -> str:
        """Export current data to file"""
        if self.current_data is None:
            return "No data to export"
        
        try:
            if format.lower() == 'csv':
                self.current_data.to_csv(filepath, index=False)
            elif format.lower() == 'json':
                self.current_data.to_json(filepath, orient='records')
            elif format.lower() == 'excel':
                self.current_data.to_excel(filepath, index=False)
            else:
                return f"Unsupported export format: {format}"
            
            return f"Data exported successfully to {filepath}"
        
        except Exception as e:
            return f"Export failed: {str(e)}"