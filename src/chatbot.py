import re
import json
import pandas as pd
from datetime import datetime
from src.ml_helper import MLHelper
from src.visualization import VisualizationHelper

class DataScienceChatbot:
    """
    Main chatbot class for handling data science queries and tasks
    """
    
    def __init__(self):
        self.conversation_history = []
        self.current_dataset = None
        self.ml_helper = MLHelper()
        self.viz_helper = VisualizationHelper()
        self.trained_models = {}
        
        # Define command patterns
        self.command_patterns = {
            'load_data': r'load\s+data\s+(.+)|load\s+(.+\.(?:csv|json|xlsx))',
            'create_sample': r'create\s+sample\s+data|sample\s+data|generate\s+sample',
            'show_data': r'show\s+data|display\s+data|head|tail',
            'describe': r'describe|summary|statistics|stats',
            'analyze': r'analyze\s+(.+)|analysis\s+(.+)',
            'visualize': r'plot|chart|graph|visualize|show\s+(.+)\s+plot',
            'model': r'train\s+(.+)|model\s+(.+)|predict|machine\s+learning',
            'clean': r'clean\s+data|preprocessing|prepare\s+data',
            'correlation': r'correlation|corr',
            'help': r'help|commands|\?',
        }
    
    def process_message(self, message, data_processor):
        """Process user message and return appropriate response"""
        message = message.lower().strip()
        
        # Add to conversation history
        self.conversation_history.append({
            'user': message,
            'timestamp': datetime.now()
        })
        
        response = {
            'message': '',
            'data': None,
            'visualization': None,
            'code': None
        }
        
        try:
            # Match command patterns
            if self._match_pattern('create_sample', message):
                response = self._handle_create_sample(data_processor)
            elif self._match_pattern('load_data', message):
                response = self._handle_load_data(message, data_processor)
            elif self._match_pattern('show_data', message):
                response = self._handle_show_data()
            elif self._match_pattern('describe', message):
                response = self._handle_describe()
            elif self._match_pattern('analyze', message):
                response = self._handle_analyze(message)
            elif self._match_pattern('visualize', message):
                response = self._handle_visualize(message)
            elif self._match_pattern('model', message):
                response = self._handle_model(message)
            elif self._match_pattern('clean', message):
                response = self._handle_clean_data()
            elif self._match_pattern('correlation', message):
                response = self._handle_correlation()
            elif self._match_pattern('help', message):
                response = self._handle_help()
            else:
                response = self._handle_general_query(message)
        
        except Exception as e:
            response['message'] = f"I encountered an error: {str(e)}. Please try again or rephrase your question."
        
        # Add response to history
        self.conversation_history.append({
            'bot': response['message'],
            'timestamp': datetime.now()
        })
        
        return response
    
    def _match_pattern(self, command, message):
        """Check if message matches a command pattern"""
        pattern = self.command_patterns.get(command)
        if pattern:
            return re.search(pattern, message, re.IGNORECASE)
        return False
    
    def _handle_create_sample(self, data_processor):
        """Handle create sample data commands"""
        try:
            result = data_processor.create_sample_data()
            # Load the created sample data
            self.current_dataset = data_processor.load_data('data/sample_data.csv')
            info = data_processor.get_data_info()
            
            return {
                'message': f"{result}\n\nDataset loaded! Shape: {info['shape']}, Columns: {info['columns']}",
                'data': self.current_dataset.head().to_dict('records'),
                'visualization': None,
                'code': "# Sample data created with realistic correlations\n# Age, income, education, experience, salary, etc."
            }
        except Exception as e:
            return {
                'message': f"Failed to create sample data: {str(e)}",
                'data': None,
                'visualization': None,
                'code': None
            }
    
    def _handle_load_data(self, message, data_processor):
        """Handle data loading commands"""
        # Extract filename from message
        match = re.search(r'load\s+(?:data\s+)?(.+)', message, re.IGNORECASE)
        if match:
            filename = match.group(1).strip()
            try:
                self.current_dataset = data_processor.load_data(filename)
                info = data_processor.get_data_info()
                
                return {
                    'message': f"Dataset loaded successfully! Shape: {info['shape']}, Columns: {info['columns']}",
                    'data': info,
                    'visualization': None,
                    'code': f"df = pd.read_csv('{filename}')"
                }
            except Exception as e:
                return {
                    'message': f"Failed to load data: {str(e)}",
                    'data': None,
                    'visualization': None,
                    'code': None
                }
        else:
            return {
                'message': "Please specify a filename. Example: 'load data sample.csv'",
                'data': None,
                'visualization': None,
                'code': None
            }
    
    def _handle_show_data(self):
        """Handle data display commands"""
        if self.current_dataset is None:
            return {'message': "No dataset loaded. Please load a dataset first.", 'data': None, 'visualization': None, 'code': None}
        
        head_data = self.current_dataset.head().to_dict('records')
        return {
            'message': "Here's a preview of your dataset:",
            'data': head_data,
            'visualization': None,
            'code': "df.head()"
        }
    
    def _handle_describe(self):
        """Handle descriptive statistics commands"""
        if self.current_dataset is None:
            return {'message': "No dataset loaded. Please load a dataset first.", 'data': None, 'visualization': None, 'code': None}
        
        desc = self.current_dataset.describe()
        return {
            'message': "Here are the descriptive statistics for your dataset:",
            'data': desc.to_dict(),
            'visualization': None,
            'code': "df.describe()"
        }
    
    def _handle_analyze(self, message):
        """Handle data analysis commands"""
        if self.current_dataset is None:
            return {'message': "No dataset loaded. Please load a dataset first.", 'data': None, 'visualization': None, 'code': None}
        
        # Extract column name if specified
        match = re.search(r'analyze\s+(.+)', message, re.IGNORECASE)
        if match:
            column = match.group(1).strip()
            if column in self.current_dataset.columns:
                analysis = self._analyze_column(column)
                return {
                    'message': f"Analysis for column '{column}':",
                    'data': analysis,
                    'visualization': None,
                    'code': f"df['{column}'].describe()"
                }
            else:
                return {
                    'message': f"Column '{column}' not found. Available columns: {list(self.current_dataset.columns)}",
                    'data': None,
                    'visualization': None,
                    'code': None
                }
        else:
            # General dataset analysis
            analysis = self._analyze_dataset()
            return {
                'message': "Dataset analysis complete:",
                'data': analysis,
                'visualization': None,
                'code': "# Dataset analysis\ndf.info()\ndf.describe()"
            }
    
    def _handle_visualize(self, message):
        """Handle visualization commands"""
        if self.current_dataset is None:
            return {'message': "No dataset loaded. Please load a dataset first.", 'data': None, 'visualization': None, 'code': None}
        
        # Simple visualization for now
        plot_path = self.viz_helper.create_basic_plot(self.current_dataset)
        return {
            'message': "I've created a basic visualization of your dataset.",
            'data': None,
            'visualization': plot_path,
            'code': "import matplotlib.pyplot as plt\ndf.hist(figsize=(10, 6))\nplt.show()"
        }
    
    def _handle_model(self, message):
        """Handle machine learning commands"""
        if self.current_dataset is None:
            return {'message': "No dataset loaded. Please load a dataset first.", 'data': None, 'visualization': None, 'code': None}
        
        # Basic model training example
        result = self.ml_helper.suggest_models(self.current_dataset)
        return {
            'message': "Here are some model suggestions based on your dataset:",
            'data': result,
            'visualization': None,
            'code': "from sklearn.model_selection import train_test_split\nfrom sklearn.ensemble import RandomForestClassifier"
        }
    
    def _handle_clean_data(self):
        """Handle data cleaning commands"""
        if self.current_dataset is None:
            return {'message': "No dataset loaded. Please load a dataset first.", 'data': None, 'visualization': None, 'code': None}
        
        cleaning_suggestions = self._get_cleaning_suggestions()
        return {
            'message': "Here are some data cleaning suggestions:",
            'data': cleaning_suggestions,
            'visualization': None,
            'code': "# Data cleaning\ndf.isnull().sum()\ndf.dropna()\ndf.fillna(df.mean())"
        }
    
    def _handle_correlation(self):
        """Handle correlation analysis commands"""
        if self.current_dataset is None:
            return {'message': "No dataset loaded. Please load a dataset first.", 'data': None, 'visualization': None, 'code': None}
        
        numeric_cols = self.current_dataset.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 1:
            corr = self.current_dataset[numeric_cols].corr()
            return {
                'message': "Correlation matrix for numeric columns:",
                'data': corr.to_dict(),
                'visualization': None,
                'code': "df.corr()"
            }
        else:
            return {
                'message': "Need at least 2 numeric columns for correlation analysis.",
                'data': None,
                'visualization': None,
                'code': None
            }
    
    def _handle_help(self):
        """Handle help commands"""
        help_text = """
        Available commands:
        • create sample data - Create a test dataset
        • load data <filename> - Load a dataset
        • show data - Display first few rows
        • describe - Show descriptive statistics
        • analyze <column> - Analyze specific column
        • plot/visualize - Create visualizations
        • train model - Get ML model suggestions
        • clean data - Get data cleaning suggestions
        • correlation - Show correlation matrix
        • help - Show this help message
        
        You can also ask me general data science questions!
        """
        return {
            'message': help_text,
            'data': None,
            'visualization': None,
            'code': None
        }
    
    def _handle_general_query(self, message):
        """Handle general data science queries"""
        responses = {
            'hello': "Hello! I'm your data science assistant. How can I help you today?",
            'goodbye': "Goodbye! Feel free to come back anytime for data science help.",
            'thank': "You're welcome! Is there anything else I can help you with?",
        }
        
        for key, response in responses.items():
            if key in message:
                return {'message': response, 'data': None, 'visualization': None, 'code': None}
        
        # Default response for unrecognized queries
        return {
            'message': "I'm not sure I understand. Try asking me to load data, create visualizations, or type 'help' for available commands.",
            'data': None,
            'visualization': None,
            'code': None
        }
    
    def _analyze_column(self, column):
        """Analyze a specific column"""
        col_data = self.current_dataset[column]
        analysis = {
            'data_type': str(col_data.dtype),
            'non_null_count': col_data.count(),
            'null_count': col_data.isnull().sum(),
            'unique_values': col_data.nunique()
        }
        
        if pd.api.types.is_numeric_dtype(col_data):
            analysis.update({
                'mean': col_data.mean(),
                'median': col_data.median(),
                'std': col_data.std(),
                'min': col_data.min(),
                'max': col_data.max()
            })
        
        return analysis
    
    def _analyze_dataset(self):
        """Analyze the entire dataset"""
        return {
            'shape': self.current_dataset.shape,
            'columns': list(self.current_dataset.columns),
            'data_types': self.current_dataset.dtypes.to_dict(),
            'missing_values': self.current_dataset.isnull().sum().to_dict(),
            'memory_usage': self.current_dataset.memory_usage(deep=True).sum()
        }
    
    def _get_cleaning_suggestions(self):
        """Get data cleaning suggestions"""
        suggestions = []
        
        # Check for missing values
        missing = self.current_dataset.isnull().sum()
        if missing.any():
            suggestions.append("Handle missing values in columns: " + ", ".join(missing[missing > 0].index.tolist()))
        
        # Check for duplicates
        if self.current_dataset.duplicated().any():
            suggestions.append("Remove duplicate rows")
        
        # Check data types
        suggestions.append("Review data types for optimal memory usage")
        
        return suggestions
    
    def get_model_status(self):
        """Get current model training status"""
        return {
            'trained_models': list(self.trained_models.keys()),
            'current_dataset': self.current_dataset is not None,
            'conversation_length': len(self.conversation_history)
        }