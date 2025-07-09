"""
DeepSeek connector implementation.

DeepSeek uses an OpenAI-compatible API, so we inherit from OpenAIConnector.
"""

from typing import Optional
import os

from .openai_connector import OpenAIConnector


class DeepSeekConnector(OpenAIConnector):
    """
    Connector for DeepSeek's API.
    
    Since DeepSeek uses an OpenAI-compatible API, we inherit most functionality
    and just override the defaults and pricing.
    """
    
    def __init__(self, api_key: str, model: Optional[str] = None, **kwargs):
        """Initialize DeepSeek connector with DeepSeek-specific defaults."""
        # Set DeepSeek base URL
        kwargs["base_url"] = kwargs.get("base_url", "https://api.deepseek.com/v1")
        
        # Initialize parent with DeepSeek settings
        super().__init__(api_key, model, **kwargs)
    
    def get_default_model(self) -> str:
        """Get default model for DeepSeek."""
        return "deepseek-chat"
    
    def validate_model(self, model: str) -> bool:
        """Validate if model is supported by DeepSeek."""
        supported_models = [
            "deepseek-chat",
            "deepseek-coder",
        ]
        return model in supported_models
    
    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on DeepSeek pricing."""
        # DeepSeek pricing (as of 2024)
        # DeepSeek is known for very competitive pricing
        pricing = {
            "deepseek-chat": {
                "input": 0.00014,    # $0.14 per 1M tokens
                "output": 0.00028    # $0.28 per 1M tokens
            },
            "deepseek-coder": {
                "input": 0.00014,
                "output": 0.00028
            }
        }
        
        # Get pricing for model
        model_pricing = pricing.get(self.model, pricing["deepseek-chat"])
        
        # Calculate cost (pricing is per 1M tokens for DeepSeek)
        input_cost = (input_tokens / 1_000_000) * model_pricing["input"] * 1000  # Convert to per 1K
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"] * 1000
        
        return input_cost + output_cost