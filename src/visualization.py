import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os
from typing import Dict, List, Optional, Union
from datetime import datetime

class VisualizationHelper:
    """
    Helper class for creating various data visualizations
    """
    
    def __init__(self):
        # Set style preferences
        plt.style.use('default')
        sns.set_palette("husl")
        self.plot_counter = 0
        self.plot_history = []
        
        # Create plots directory if it doesn't exist
        os.makedirs('static/plots', exist_ok=True)
    
    def create_basic_plot(self, df: pd.DataFrame, plot_type: str = 'histogram') -> str:
        """
        Create a basic plot of the dataset
        
        Args:
            df: Input DataFrame
            plot_type: Type of plot to create
            
        Returns:
            Path to the saved plot
        """
        if df is None or df.empty:
            return None
        
        self.plot_counter += 1
        filename = f'plot_{self.plot_counter}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join('static/plots', filename)
        
        plt.figure(figsize=(12, 8))
        
        if plot_type == 'histogram':
            numeric_cols = df.select_dtypes(include=[np.number]).columns[:6]  # Limit to 6 columns
            if len(numeric_cols) > 0:
                df[numeric_cols].hist(bins=30, figsize=(12, 8))
                plt.suptitle('Distribution of Numeric Variables')
            else:
                plt.text(0.5, 0.5, 'No numeric columns found for histogram', 
                        ha='center', va='center', transform=plt.gca().transAxes)
                plt.title('Dataset Overview')
        
        elif plot_type == 'correlation':
            numeric_df = df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) > 1:
                corr = numeric_df.corr()
                sns.heatmap(corr, annot=True, cmap='coolwarm', center=0)
                plt.title('Correlation Matrix')
            else:
                plt.text(0.5, 0.5, 'Need at least 2 numeric columns for correlation', 
                        ha='center', va='center', transform=plt.gca().transAxes)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()
        
        # Add to history
        self.plot_history.append({
            'filename': filename,
            'plot_type': plot_type,
            'timestamp': datetime.now(),
            'columns_used': list(df.columns)
        })
        
        return filename
    
    def create_distribution_plot(self, df: pd.DataFrame, column: str, plot_type: str = 'histogram') -> str:
        """Create distribution plot for a specific column"""
        if column not in df.columns:
            return None
        
        self.plot_counter += 1
        filename = f'dist_{self.plot_counter}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join('static/plots', filename)
        
        fig, ax = plt.subplots(1, 2, figsize=(15, 6))
        
        col_data = df[column].dropna()
        
        if pd.api.types.is_numeric_dtype(col_data):
            # Histogram
            ax[0].hist(col_data, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            ax[0].set_title(f'Distribution of {column}')
            ax[0].set_xlabel(column)
            ax[0].set_ylabel('Frequency')
            
            # Box plot
            ax[1].boxplot(col_data)
            ax[1].set_title(f'Box Plot of {column}')
            ax[1].set_ylabel(column)
        else:
            # Bar plot for categorical data
            value_counts = col_data.value_counts().head(20)  # Top 20 categories
            ax[0].bar(range(len(value_counts)), value_counts.values)
            ax[0].set_title(f'Value Counts for {column}')
            ax[0].set_xlabel('Categories')
            ax[0].set_ylabel('Count')
            ax[0].set_xticks(range(len(value_counts)))
            ax[0].set_xticklabels(value_counts.index, rotation=45, ha='right')
            
            # Pie chart for top categories
            top_categories = value_counts.head(10)
            ax[1].pie(top_categories.values, labels=top_categories.index, autopct='%1.1f%%')
            ax[1].set_title(f'Top Categories in {column}')
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def create_scatter_plot(self, df: pd.DataFrame, x_col: str, y_col: str, color_col: str = None) -> str:
        """Create scatter plot between two numeric columns"""
        if x_col not in df.columns or y_col not in df.columns:
            return None
        
        self.plot_counter += 1
        filename = f'scatter_{self.plot_counter}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join('static/plots', filename)
        
        plt.figure(figsize=(10, 8))
        
        if color_col and color_col in df.columns:
            # Colored scatter plot
            if pd.api.types.is_numeric_dtype(df[color_col]):
                scatter = plt.scatter(df[x_col], df[y_col], c=df[color_col], alpha=0.6, cmap='viridis')
                plt.colorbar(scatter, label=color_col)
            else:
                # Categorical color
                categories = df[color_col].unique()[:10]  # Limit to 10 categories
                colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
                for i, category in enumerate(categories):
                    mask = df[color_col] == category
                    plt.scatter(df[x_col][mask], df[y_col][mask], 
                              c=[colors[i]], label=category, alpha=0.6)
                plt.legend(title=color_col, bbox_to_anchor=(1.05, 1), loc='upper left')
        else:
            plt.scatter(df[x_col], df[y_col], alpha=0.6)
        
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.title(f'Scatter Plot: {x_col} vs {y_col}')
        plt.tight_layout()
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def create_correlation_heatmap(self, df: pd.DataFrame, method: str = 'pearson') -> str:
        """Create correlation heatmap for numeric columns"""
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) < 2:
            return None
        
        self.plot_counter += 1
        filename = f'corr_{self.plot_counter}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join('static/plots', filename)
        
        plt.figure(figsize=(12, 10))
        
        corr = numeric_df.corr(method=method)
        
        # Create mask for upper triangle
        mask = np.triu(np.ones_like(corr, dtype=bool))
        
        sns.heatmap(corr, mask=mask, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5, cbar_kws={"shrink": .8})
        
        plt.title(f'Correlation Heatmap ({method.capitalize()})')
        plt.tight_layout()
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def create_time_series_plot(self, df: pd.DataFrame, date_col: str, value_col: str) -> str:
        """Create time series plot"""
        if date_col not in df.columns or value_col not in df.columns:
            return None
        
        self.plot_counter += 1
        filename = f'timeseries_{self.plot_counter}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join('static/plots', filename)
        
        plt.figure(figsize=(12, 6))
        
        # Convert to datetime if needed
        date_data = pd.to_datetime(df[date_col])
        
        plt.plot(date_data, df[value_col], linewidth=2)
        plt.xlabel(date_col)
        plt.ylabel(value_col)
        plt.title(f'Time Series: {value_col} over {date_col}')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def create_interactive_plot(self, df: pd.DataFrame, plot_type: str = 'scatter', **kwargs) -> str:
        """Create interactive plots using Plotly"""
        self.plot_counter += 1
        filename = f'interactive_{self.plot_counter}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        filepath = os.path.join('static/plots', filename)
        
        if plot_type == 'scatter' and 'x' in kwargs and 'y' in kwargs:
            fig = px.scatter(df, x=kwargs['x'], y=kwargs['y'], 
                           color=kwargs.get('color'), size=kwargs.get('size'),
                           title=f"Interactive Scatter: {kwargs['x']} vs {kwargs['y']}")
        
        elif plot_type == 'histogram' and 'column' in kwargs:
            fig = px.histogram(df, x=kwargs['column'], 
                             title=f"Interactive Histogram: {kwargs['column']}")
        
        elif plot_type == 'box' and 'column' in kwargs:
            fig = px.box(df, y=kwargs['column'],
                        title=f"Interactive Box Plot: {kwargs['column']}")
        
        elif plot_type == 'correlation':
            numeric_df = df.select_dtypes(include=[np.number])
            corr = numeric_df.corr()
            fig = px.imshow(corr, text_auto=True, aspect="auto",
                          title="Interactive Correlation Heatmap")
        
        else:
            # Default: simple scatter of first two numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns[:2]
            if len(numeric_cols) >= 2:
                fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1])
            else:
                return None
        
        fig.write_html(filepath)
        return filename
    
    def create_multi_plot(self, df: pd.DataFrame, columns: List[str], plot_type: str = 'distribution') -> str:
        """Create multiple subplots for selected columns"""
        if not columns or not all(col in df.columns for col in columns):
            return None
        
        self.plot_counter += 1
        filename = f'multi_{self.plot_counter}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join('static/plots', filename)
        
        n_cols = min(len(columns), 3)
        n_rows = (len(columns) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
        if n_rows == 1 and n_cols == 1:
            axes = [axes]
        elif n_rows == 1 or n_cols == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()
        
        for i, col in enumerate(columns):
            if i < len(axes):
                ax = axes[i]
                col_data = df[col].dropna()
                
                if plot_type == 'distribution':
                    if pd.api.types.is_numeric_dtype(col_data):
                        ax.hist(col_data, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
                    else:
                        value_counts = col_data.value_counts().head(10)
                        ax.bar(range(len(value_counts)), value_counts.values)
                        ax.set_xticks(range(len(value_counts)))
                        ax.set_xticklabels(value_counts.index, rotation=45, ha='right')
                
                elif plot_type == 'boxplot' and pd.api.types.is_numeric_dtype(col_data):
                    ax.boxplot(col_data)
                
                ax.set_title(f'{col}')
                ax.set_xlabel(col)
                ax.set_ylabel('Frequency' if plot_type == 'distribution' else 'Value')
        
        # Hide empty subplots
        for i in range(len(columns), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def create_feature_importance_plot(self, feature_names: List[str], importances: List[float], 
                                     model_name: str = 'Model') -> str:
        """Create feature importance visualization"""
        self.plot_counter += 1
        filename = f'feature_imp_{self.plot_counter}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join('static/plots', filename)
        
        # Sort features by importance
        feature_imp_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values('importance', ascending=True)
        
        plt.figure(figsize=(10, max(6, len(feature_names) * 0.3)))
        plt.barh(feature_imp_df['feature'], feature_imp_df['importance'])
        plt.xlabel('Feature Importance')
        plt.title(f'Feature Importance - {model_name}')
        plt.tight_layout()
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def create_confusion_matrix_plot(self, y_true, y_pred, class_names=None) -> str:
        """Create confusion matrix visualization"""
        from sklearn.metrics import confusion_matrix
        
        self.plot_counter += 1
        filename = f'confusion_{self.plot_counter}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join('static/plots', filename)
        
        cm = confusion_matrix(y_true, y_pred)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=class_names, yticklabels=class_names)
        plt.xlabel('Predicted Label')
        plt.ylabel('True Label')
        plt.title('Confusion Matrix')
        plt.tight_layout()
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def create_residuals_plot(self, y_true, y_pred) -> str:
        """Create residuals plot for regression models"""
        self.plot_counter += 1
        filename = f'residuals_{self.plot_counter}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join('static/plots', filename)
        
        residuals = y_true - y_pred
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        
        # Residuals vs Predicted
        axes[0].scatter(y_pred, residuals, alpha=0.6)
        axes[0].axhline(y=0, color='red', linestyle='--')
        axes[0].set_xlabel('Predicted Values')
        axes[0].set_ylabel('Residuals')
        axes[0].set_title('Residuals vs Predicted')
        
        # Q-Q plot of residuals
        from scipy import stats
        stats.probplot(residuals, dist="norm", plot=axes[1])
        axes[1].set_title('Q-Q Plot of Residuals')
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def get_plot_suggestions(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Get plot suggestions based on data characteristics"""
        suggestions = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        
        if len(numeric_cols) >= 1:
            suggestions.append({
                'plot_type': 'histogram',
                'description': 'Distribution plots for numeric variables',
                'command': 'create histogram plots'
            })
        
        if len(numeric_cols) >= 2:
            suggestions.append({
                'plot_type': 'scatter',
                'description': 'Scatter plots to explore relationships',
                'command': f'create scatter plot of {numeric_cols[0]} vs {numeric_cols[1]}'
            })
            
            suggestions.append({
                'plot_type': 'correlation',
                'description': 'Correlation heatmap of numeric variables',
                'command': 'show correlation heatmap'
            })
        
        if len(categorical_cols) >= 1:
            suggestions.append({
                'plot_type': 'bar',
                'description': 'Bar plots for categorical variables',
                'command': f'create bar plot for {categorical_cols[0]}'
            })
        
        if len(numeric_cols) >= 1:
            suggestions.append({
                'plot_type': 'boxplot',
                'description': 'Box plots to identify outliers',
                'command': 'create box plots'
            })
        
        return suggestions
    
    def cleanup_old_plots(self, days_old: int = 7):
        """Clean up plot files older than specified days"""
        import time
        
        plots_dir = 'static/plots'
        if not os.path.exists(plots_dir):
            return
        
        current_time = time.time()
        cutoff_time = current_time - (days_old * 24 * 60 * 60)
        
        for filename in os.listdir(plots_dir):
            filepath = os.path.join(plots_dir, filename)
            if os.path.isfile(filepath):
                file_time = os.path.getmtime(filepath)
                if file_time < cutoff_time:
                    try:
                        os.remove(filepath)
                    except:
                        pass  # Ignore errors
    
    def get_plot_history(self) -> List[Dict]:
        """Get history of created plots"""
        return self.plot_history