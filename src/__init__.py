"""
Data Science Chatbot Package

This package provides a comprehensive chatbot interface for data science tasks
including data analysis, visualization, and machine learning.

Modules:
- chatbot: Main chatbot logic and conversation handling
- data_processor: Data loading, cleaning, and processing utilities
- ml_helper: Machine learning model training and evaluation
- visualization: Chart and plot generation utilities
"""

__version__ = "1.0.0"
__author__ = "Data Science Chatbot Team"
__email__ = "support@datascience-chatbot.com"

from .chatbot import DataScienceChatbot
from .data_processor import DataProcessor
from .ml_helper import MLHelper
from .visualization import VisualizationHelper

__all__ = [
    'DataScienceChatbot',
    'DataProcessor', 
    'MLHelper',
    'VisualizationHelper'
]