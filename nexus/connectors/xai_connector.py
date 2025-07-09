"""
xAI (Grok) connector implementation.

Grok uses an OpenAI-compatible API, so we inherit from OpenAIConnector.
"""

from typing import Optional

from .openai_connector import OpenAIConnector


class XAIConnector(OpenAIConnector):
    """
    Connector for xAI's Grok API.
    
    Since Grok uses an OpenAI-compatible API, we inherit most functionality
    and just override the defaults.
    """
    
    def __init__(self, api_key: str, model: Optional[str] = None, **kwargs):
        """Initialize xAI connector with Grok-specific defaults."""
        # Set xAI base URL
        kwargs["base_url"] = kwargs.get("base_url", "https://api.x.ai/v1")
        
        # Initialize parent with xAI settings
        super().__init__(api_key, model, **kwargs)
    
    def get_default_model(self) -> str:
        """Get default model for xAI."""
        return "grok-3"
    
    def validate_model(self, model: str) -> bool:
        """Validate if model is supported by xAI."""
        supported_models = [
            "grok-3",
            "grok-beta",
        ]
        return model in supported_models
    
    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on xAI pricing."""
        # Grok pricing (estimated as of 2024)
        pricing = {
            "grok-3": {"input": 0.002, "output": 0.006},
            "grok-beta": {"input": 0.001, "output": 0.003}
        }
        
        # Get pricing for model
        model_pricing = pricing.get(self.model, pricing["grok-3"])
        
        # Calculate cost
        input_cost = (input_tokens / 1000) * model_pricing["input"]
        output_cost = (output_tokens / 1000) * model_pricing["output"]
        
        return input_cost + output_cost