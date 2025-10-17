"""
Enhanced Data Processor with persistent memory
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """Enhanced data processor with memory and advanced features"""
    
    def __init__(self, user_id: Optional[int] = None):
        self.data = None
        self.original_data = None
        self.filepath = None
        self.user_id = user_id
        self.metadata = {}
        self.transformations = []
    
    def load_data(self, filepath: str) -> pd.DataFrame:
        """
        Load data from file with support for multiple formats
        
        Args:
            filepath: Path to data file
            
        Returns:
            Loaded DataFrame
        """
        try:
            ext = os.path.splitext(filepath)[1].lower()
            
            if ext == '.csv':
                # Try different encodings
                encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
                for encoding in encodings:
                    try:
                        self.data = pd.read_csv(filepath, encoding=encoding)
                        logger.info(f"Loaded CSV with {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("Could not decode CSV file")
            
            elif ext in ['.xlsx', '.xls']:
                self.data = pd.read_excel(filepath)
            
            elif ext == '.json':
                self.data = pd.read_json(filepath)
            
            elif ext == '.parquet':
                self.data = pd.read_parquet(filepath)
            
            else:
                raise ValueError(f"Unsupported file type: {ext}")
            
            # Store original data for reset capability
            self.original_data = self.data.copy()
            self.filepath = filepath
            
            # Generate metadata
            self._generate_metadata()
            
            logger.info(f"Loaded data: {self.data.shape}")
            return self.data
        
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise Exception(f"Failed to load data: {str(e)}")
    
    def _generate_metadata(self):
        """Generate metadata about the dataset"""
        if self.data is None:
            return
        
        self.metadata = {
            'filename': os.path.basename(self.filepath) if self.filepath else None,
            'shape': self.data.shape,
            'columns': list(self.data.columns),
            'dtypes': {col: str(dtype) for col, dtype in self.data.dtypes.items()},
            'memory_usage': int(self.data.memory_usage(deep=True).sum()),
            'missing_values': self.data.isnull().sum().to_dict(),
            'numeric_columns': self.data.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical_columns': self.data.select_dtypes(include=['object']).columns.tolist(),
            'date_columns': self.data.select_dtypes(include=['datetime64']).columns.tolist()
        }
    
    def get_data_info(self) -> Dict[str, Any]:
        """Get information about loaded data"""
        if self.data is None:
            return {
                "shape": (0, 0),
                "columns": [],
                "dtypes": {},
                "loaded": False
            }
        
        return {
            "shape": self.data.shape,
            "columns": list(self.data.columns),
            "dtypes": {col: str(dtype) for col, dtype in self.data.dtypes.items()},
            "memory_usage": int(self.data.memory_usage(deep=True).sum()),
            "missing_values": self.data.isnull().sum().sum(),
            "numeric_columns": self.data.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_columns": self.data.select_dtypes(include=['object']).columns.tolist(),
            "loaded": True,
            "metadata": self.metadata
        }
    
    def get_sample(self, n: int = 5, sample_type: str = 'head') -> Dict[str, Any]:
        """Get sample of data"""
        if self.data is None:
            return {"error": "No data loaded"}
        
        if sample_type == 'head':
            sample = self.data.head(n)
        elif sample_type == 'tail':
            sample = self.data.tail(n)
        elif sample_type == 'random':
            sample = self.data.sample(min(n, len(self.data)))
        else:
            sample = self.data.head(n)
        
        return {
            "sample": sample.to_dict(orient='records'),
            "columns": list(sample.columns),
            "shape": sample.shape
        }
    
    def get_column_stats(self, column: str) -> Dict[str, Any]:
        """Get statistics for a specific column"""
        if self.data is None or column not in self.data.columns:
            return {"error": "Column not found"}
        
        col_data = self.data[column]
        stats = {
            "name": column,
            "dtype": str(col_data.dtype),
            "count": int(col_data.count()),
            "missing": int(col_data.isnull().sum()),
            "unique": int(col_data.nunique())
        }
        
        if pd.api.types.is_numeric_dtype(col_data):
            stats.update({
                "mean": float(col_data.mean()) if not col_data.empty else None,
                "median": float(col_data.median()) if not col_data.empty else None,
                "std": float(col_data.std()) if not col_data.empty else None,
                "min": float(col_data.min()) if not col_data.empty else None,
                "max": float(col_data.max()) if not col_data.empty else None,
                "quantiles": {
                    "25%": float(col_data.quantile(0.25)) if not col_data.empty else None,
                    "50%": float(col_data.quantile(0.50)) if not col_data.empty else None,
                    "75%": float(col_data.quantile(0.75)) if not col_data.empty else None
                }
            })
        else:
            # Categorical stats
            value_counts = col_data.value_counts().head(10)
            stats.update({
                "top_values": value_counts.to_dict(),
                "mode": col_data.mode()[0] if not col_data.mode().empty else None
            })
        
        return stats
    
    def search_data(self, query: str, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Search for data matching query"""
        if self.data is None:
            return {"error": "No data loaded"}
        
        search_cols = columns if columns else self.data.select_dtypes(include=['object']).columns.tolist()
        
        if not search_cols:
            return {"error": "No searchable columns"}
        
        mask = pd.Series([False] * len(self.data))
        for col in search_cols:
            mask |= self.data[col].astype(str).str.contains(query, case=False, na=False)
        
        results = self.data[mask]
        
        return {
            "matches": len(results),
            "results": results.head(50).to_dict(orient='records'),
            "columns_searched": search_cols
        }
    
    def apply_transformation(self, transformation: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a transformation to the data and track it"""
        if self.data is None:
            return {"error": "No data loaded"}
        
        try:
            transform_type = transformation.get('type')
            
            if transform_type == 'drop_column':
                column = transformation.get('column')
                if column in self.data.columns:
                    self.data = self.data.drop(columns=[column])
                    self.transformations.append(transformation)
                    return {"success": True, "message": f"Dropped column {column}"}
            
            elif transform_type == 'rename_column':
                old_name = transformation.get('old_name')
                new_name = transformation.get('new_name')
                if old_name in self.data.columns:
                    self.data = self.data.rename(columns={old_name: new_name})
                    self.transformations.append(transformation)
                    return {"success": True, "message": f"Renamed {old_name} to {new_name}"}
            
            elif transform_type == 'fill_missing':
                column = transformation.get('column')
                method = transformation.get('method', 'mean')
                if column in self.data.columns:
                    if method == 'mean' and pd.api.types.is_numeric_dtype(self.data[column]):
                        self.data[column].fillna(self.data[column].mean(), inplace=True)
                    elif method == 'median' and pd.api.types.is_numeric_dtype(self.data[column]):
                        self.data[column].fillna(self.data[column].median(), inplace=True)
                    elif method == 'mode':
                        self.data[column].fillna(self.data[column].mode()[0], inplace=True)
                    elif method == 'forward':
                        self.data[column].fillna(method='ffill', inplace=True)
                    self.transformations.append(transformation)
                    return {"success": True, "message": f"Filled missing values in {column}"}
            
            elif transform_type == 'convert_type':
                column = transformation.get('column')
                new_type = transformation.get('new_type')
                if column in self.data.columns:
                    self.data[column] = self.data[column].astype(new_type)
                    self.transformations.append(transformation)
                    return {"success": True, "message": f"Converted {column} to {new_type}"}
            
            self._generate_metadata()
            return {"error": "Unknown transformation type"}
        
        except Exception as e:
            logger.error(f"Error applying transformation: {str(e)}")
            return {"error": str(e)}
    
    def reset_data(self):
        """Reset data to original state"""
        if self.original_data is not None:
            self.data = self.original_data.copy()
            self.transformations = []
            self._generate_metadata()
            return {"success": True, "message": "Data reset to original state"}
        return {"error": "No original data to reset to"}
    
    def export_data(self, output_path: str, format: str = 'csv') -> Dict[str, Any]:
        """Export current data to file"""
        if self.data is None:
            return {"error": "No data to export"}
        
        try:
            if format == 'csv':
                self.data.to_csv(output_path, index=False)
            elif format == 'excel':
                self.data.to_excel(output_path, index=False)
            elif format == 'json':
                self.data.to_json(output_path, orient='records')
            elif format == 'parquet':
                self.data.to_parquet(output_path, index=False)
            else:
                return {"error": f"Unsupported format: {format}"}
            
            return {
                "success": True,
                "message": f"Data exported to {output_path}",
                "format": format,
                "size": os.path.getsize(output_path)
            }
        
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            return {"error": str(e)}
    
    def get_transformation_history(self) -> List[Dict[str, Any]]:
        """Get history of all transformations applied"""
        return self.transformations
    
    def get_data_quality_report(self) -> Dict[str, Any]:
        """Generate data quality report"""
        if self.data is None:
            return {"error": "No data loaded"}
        
        report = {
            "total_rows": len(self.data),
            "total_columns": len(self.data.columns),
            "memory_usage_mb": self.data.memory_usage(deep=True).sum() / 1024**2,
            "duplicate_rows": self.data.duplicated().sum(),
            "columns_with_missing": (self.data.isnull().sum() > 0).sum(),
            "total_missing_values": self.data.isnull().sum().sum(),
            "missing_percentage": round(self.data.isnull().sum().sum() / (len(self.data) * len(self.data.columns)) * 100, 2),
            "numeric_columns": len(self.data.select_dtypes(include=[np.number]).columns),
            "categorical_columns": len(self.data.select_dtypes(include=['object']).columns),
            "datetime_columns": len(self.data.select_dtypes(include=['datetime64']).columns)
        }
        
        # Column-level quality
        column_quality = []
        for col in self.data.columns:
            col_quality = {
                "column": col,
                "dtype": str(self.data[col].dtype),
                "missing_count": int(self.data[col].isnull().sum()),
                "missing_pct": round(self.data[col].isnull().sum() / len(self.data) * 100, 2),
                "unique_count": int(self.data[col].nunique()),
                "uniqueness_pct": round(self.data[col].nunique() / len(self.data) * 100, 2)
            }
            column_quality.append(col_quality)
        
        report["column_quality"] = column_quality
        return report