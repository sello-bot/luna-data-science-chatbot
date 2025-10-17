"""
AI-Powered Data Science Chatbot with OpenAI Function Calling
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataScienceChatbot:
    """Intelligent chatbot with LLM and function calling capabilities"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.model = "gpt-4o-mini"  # Cost-effective, smart model
        self.conversation_history = []
        self.current_dataset = None
        self.dataset_context = {}
        self.max_history = 10
        
        # System prompt for the AI
        self.system_prompt = """You are an expert data science assistant. You help users analyze data, create visualizations, build ML models, and understand their datasets.

You have access to tools that can:
- Analyze datasets (summary statistics, correlations, distributions)
- Create visualizations (scatter plots, bar charts, histograms, heatmaps)
- Build ML models (regression, classification, clustering)
- Clean and preprocess data
- Generate insights and recommendations

Always:
1. Ask clarifying questions if the request is ambiguous
2. Explain what you're doing in simple terms
3. Provide actionable insights from the data
4. Suggest next steps for analysis
5. Be conversational and helpful

When a dataset is loaded, refer to it naturally and use the tools to analyze it.
"""
    
    def process_message(self, user_message: str, data_processor) -> Dict[str, Any]:
        """
        Process user message with LLM and function calling
        
        Args:
            user_message: User's input message
            data_processor: DataProcessor instance with loaded data
            
        Returns:
            Dict with response, data, visualization, and code
        """
        try:
            # Update current dataset reference
            self.current_dataset = data_processor.data
            self.dataset_context = data_processor.get_data_info() if self.current_dataset is not None else {}
            
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # If no OpenAI API key, use fallback
            if not self.client:
                return self._fallback_response(user_message, data_processor)
            
            # Build messages for OpenAI
            messages = self._build_messages()
            
            # Get available tools based on current state
            tools = self._get_available_tools()
            
            # Call OpenAI with function calling
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=2000
            )
            
            assistant_message = response.choices[0].message
            
            # Check if AI wants to call functions
            if assistant_message.tool_calls:
                return self._handle_function_calls(
                    assistant_message, 
                    data_processor,
                    messages
                )
            else:
                # Direct text response
                response_text = assistant_message.content
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response_text
                })
                
                return {
                    "message": response_text,
                    "data": None,
                    "visualization": None,
                    "code": None
                }
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                "message": f"I encountered an error: {str(e)}. Please try rephrasing your question.",
                "data": None,
                "visualization": None,
                "code": None
            }
    
    def _build_messages(self) -> List[Dict[str, str]]:
        """Build message list for OpenAI API"""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add dataset context if available
        if self.dataset_context:
            context_msg = f"""Current dataset loaded:
- Shape: {self.dataset_context.get('shape', 'N/A')}
- Columns: {', '.join(self.dataset_context.get('columns', [])[:10])}
- Data types: Available
- Missing values: Check with analyze_data tool

The user has data loaded and ready for analysis."""
            messages.append({"role": "system", "content": context_msg})
        
        # Add conversation history (keep last N messages)
        messages.extend(self.conversation_history[-self.max_history:])
        
        return messages
    
    def _get_available_tools(self) -> List[Dict]:
        """Get available function calling tools"""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "analyze_data",
                    "description": "Analyze the current dataset: summary statistics, missing values, correlations, data types",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis_type": {
                                "type": "string",
                                "enum": ["summary", "missing_values", "correlations", "describe", "info"],
                                "description": "Type of analysis to perform"
                            },
                            "columns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific columns to analyze (optional)"
                            }
                        },
                        "required": ["analysis_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_visualization",
                    "description": "Create a visualization from the dataset",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "plot_type": {
                                "type": "string",
                                "enum": ["scatter", "line", "bar", "histogram", "box", "heatmap", "pairplot"],
                                "description": "Type of plot to create"
                            },
                            "x_column": {
                                "type": "string",
                                "description": "Column for x-axis"
                            },
                            "y_column": {
                                "type": "string",
                                "description": "Column for y-axis (optional for some plots)"
                            },
                            "title": {
                                "type": "string",
                                "description": "Title for the plot"
                            },
                            "color_column": {
                                "type": "string",
                                "description": "Column to use for color coding (optional)"
                            }
                        },
                        "required": ["plot_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "train_model",
                    "description": "Train a machine learning model on the dataset",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "model_type": {
                                "type": "string",
                                "enum": ["linear_regression", "logistic_regression", "random_forest", "decision_tree", "kmeans"],
                                "description": "Type of ML model to train"
                            },
                            "target_column": {
                                "type": "string",
                                "description": "Target variable (y) for supervised learning"
                            },
                            "feature_columns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Feature columns (X) to use for training"
                            },
                            "test_size": {
                                "type": "number",
                                "description": "Proportion of data for testing (0-1)",
                                "default": 0.2
                            }
                        },
                        "required": ["model_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "filter_data",
                    "description": "Filter the dataset based on conditions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "column": {
                                "type": "string",
                                "description": "Column to filter on"
                            },
                            "condition": {
                                "type": "string",
                                "enum": [">", "<", ">=", "<=", "==", "!=", "contains"],
                                "description": "Comparison operator"
                            },
                            "value": {
                                "type": "string",
                                "description": "Value to compare against"
                            }
                        },
                        "required": ["column", "condition", "value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_data_sample",
                    "description": "Get a sample of rows from the dataset",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "n_rows": {
                                "type": "integer",
                                "description": "Number of rows to return",
                                "default": 10
                            },
                            "sample_type": {
                                "type": "string",
                                "enum": ["head", "tail", "random"],
                                "description": "Type of sample to get",
                                "default": "head"
                            }
                        }
                    }
                }
            }
        ]
        
        return tools
    
    def _handle_function_calls(self, assistant_message, data_processor, messages) -> Dict[str, Any]:
        """Execute function calls and get final response"""
        function_results = []
        visualization = None
        code_used = []
        
        # Execute each function call
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            logger.info(f"Calling function: {function_name} with args: {function_args}")
            
            # Execute the function
            result = self._execute_function(function_name, function_args, data_processor)
            
            function_results.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps(result.get("result", {}))
            })
            
            # Collect visualization and code
            if result.get("visualization"):
                visualization = result["visualization"]
            if result.get("code"):
                code_used.append(result["code"])
        
        # Add function results to messages and get final response
        messages.append(assistant_message.model_dump())
        messages.extend(function_results)
        
        # Get final response from AI
        final_response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )
        
        final_text = final_response.choices[0].message.content
        
        # Update conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": final_text
        })
        
        return {
            "message": final_text,
            "data": function_results[0].get("content") if function_results else None,
            "visualization": visualization,
            "code": "\n\n".join(code_used) if code_used else None
        }
    
    def _execute_function(self, function_name: str, args: Dict, data_processor) -> Dict[str, Any]:
        """Execute a function call"""
        try:
            if function_name == "analyze_data":
                return self._analyze_data(args, data_processor)
            elif function_name == "create_visualization":
                return self._create_visualization(args, data_processor)
            elif function_name == "train_model":
                return self._train_model(args, data_processor)
            elif function_name == "filter_data":
                return self._filter_data(args, data_processor)
            elif function_name == "get_data_sample":
                return self._get_data_sample(args, data_processor)
            else:
                return {"result": {"error": f"Unknown function: {function_name}"}}
        except Exception as e:
            logger.error(f"Error executing {function_name}: {str(e)}", exc_info=True)
            return {"result": {"error": str(e)}}
    
    def _analyze_data(self, args: Dict, data_processor) -> Dict[str, Any]:
        """Analyze dataset"""
        from src.tools import analyze_dataset
        result = analyze_dataset(data_processor.data, args.get("analysis_type"), args.get("columns"))
        return {"result": result, "code": result.get("code")}
    
    def _create_visualization(self, args: Dict, data_processor) -> Dict[str, Any]:
        """Create visualization"""
        from src.tools import create_plot
        result = create_plot(data_processor.data, args)
        return {
            "result": {"status": "success", "plot_created": True},
            "visualization": result.get("plot_url"),
            "code": result.get("code")
        }
    
    def _train_model(self, args: Dict, data_processor) -> Dict[str, Any]:
        """Train ML model"""
        from src.tools import train_ml_model
        result = train_ml_model(data_processor.data, args)
        return {"result": result, "code": result.get("code")}
    
    def _filter_data(self, args: Dict, data_processor) -> Dict[str, Any]:
        """Filter dataset"""
        from src.tools import filter_dataframe
        result = filter_dataframe(data_processor.data, args)
        data_processor.data = result["filtered_data"]  # Update the data
        return {"result": result, "code": result.get("code")}
    
    def _get_data_sample(self, args: Dict, data_processor) -> Dict[str, Any]:
        """Get data sample"""
        df = data_processor.data
        n_rows = args.get("n_rows", 10)
        sample_type = args.get("sample_type", "head")
        
        if sample_type == "head":
            sample = df.head(n_rows)
        elif sample_type == "tail":
            sample = df.tail(n_rows)
        else:
            sample = df.sample(min(n_rows, len(df)))
        
        return {
            "result": {
                "sample": sample.to_dict(orient="records"),
                "shape": sample.shape
            }
        }
    
    def _fallback_response(self, user_message: str, data_processor) -> Dict[str, Any]:
        """Fallback response when no OpenAI API key"""
        message_lower = user_message.lower()
        
        if 'help' in message_lower:
            return {
                "message": """I can help you with:
                
🔍 **Data Analysis**
- "Show me summary statistics"
- "What columns have missing values?"
- "Show correlations between variables"

📊 **Visualizations**
- "Create a scatter plot of X vs Y"
- "Show a histogram of column Z"
- "Make a heatmap of correlations"

🤖 **Machine Learning**
- "Train a regression model to predict Y"
- "Classify data using random forest"
- "Cluster the data"

💡 **Tips**
- Upload a dataset first
- Be specific about column names
- Ask follow-up questions!

⚠️ **Note**: For full AI capabilities, add your OpenAI API key to .env file""",
                "data": None,
                "visualization": None,
                "code": None
            }
        
        elif 'summary' in message_lower or 'describe' in message_lower:
            if self.current_dataset is not None:
                from src.tools import analyze_dataset
                result = analyze_dataset(self.current_dataset, "describe")
                return {
                    "message": "Here's a summary of your dataset:",
                    "data": result,
                    "visualization": None,
                    "code": result.get("code")
                }
        
        return {
            "message": "⚠️ OpenAI API key not configured. Add OPENAI_API_KEY to your .env file for full AI capabilities. Type 'help' to see what I can do!",
            "data": None,
            "visualization": None,
            "code": None
        }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []