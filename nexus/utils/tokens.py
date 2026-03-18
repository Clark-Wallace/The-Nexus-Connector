"""
Token counting utilities for Nexus.

Provides consistent token counting across all providers using tiktoken
with appropriate fallbacks for non-OpenAI models.
"""

from functools import lru_cache
from typing import Optional

# Try to import tiktoken, but make it optional
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    tiktoken = None


# Model-to-encoding mapping for known models
MODEL_ENCODINGS = {
    # OpenAI models
    "gpt-4": "cl100k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-4o": "o200k_base",
    "gpt-4o-mini": "o200k_base",
    "gpt-3.5-turbo": "cl100k_base",
    # Claude models (use cl100k_base as approximation - similar to GPT-4)
    "claude-3-opus": "cl100k_base",
    "claude-3-5-sonnet": "cl100k_base",
    "claude-sonnet-4": "cl100k_base",
    "claude-opus-4": "cl100k_base",
    "claude-3-sonnet": "cl100k_base",
    "claude-3-haiku": "cl100k_base",
    # Default for most modern models
    "default": "cl100k_base",
}


@lru_cache(maxsize=16)
def get_encoding(model: Optional[str] = None) -> Optional["tiktoken.Encoding"]:
    """
    Get tiktoken encoding for a model.

    Args:
        model: Model name (e.g., "gpt-4", "claude-3-opus")

    Returns:
        tiktoken Encoding object, or None if tiktoken unavailable
    """
    if not TIKTOKEN_AVAILABLE:
        return None

    # Try to get encoding for the model
    if model:
        try:
            return tiktoken.encoding_for_model(model)
        except KeyError:
            pass

        # Try to find a matching encoding from our mapping
        for pattern, encoding_name in MODEL_ENCODINGS.items():
            if pattern in (model or "").lower():
                try:
                    return tiktoken.get_encoding(encoding_name)
                except Exception:
                    pass

    # Fall back to cl100k_base (GPT-4 encoding) as default
    try:
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None


def count_tokens(text: str, model: Optional[str] = None) -> int:
    """
    Count tokens in text using tiktoken with fallback to approximation.

    This provides consistent token counting across all providers:
    - Uses tiktoken when available (accurate for OpenAI, good approximation for others)
    - Falls back to character-based approximation when tiktoken unavailable

    Args:
        text: Text to count tokens for
        model: Optional model name for model-specific encoding

    Returns:
        Estimated number of tokens

    Note:
        For non-OpenAI models, this is an approximation. Actual token counts
        may vary by 5-15% depending on the provider's tokenizer.
    """
    if not text:
        return 0

    encoding = get_encoding(model)

    if encoding:
        try:
            return len(encoding.encode(text))
        except Exception:
            pass

    # Fallback: estimate based on character count
    # Average is roughly 4 characters per token for English text
    # This varies by language and content type
    return len(text) // 4


def count_tokens_for_messages(
    messages: list,
    model: Optional[str] = None
) -> int:
    """
    Count tokens for a list of chat messages.

    Accounts for message structure overhead (role prefixes, separators).

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        model: Optional model name

    Returns:
        Estimated total tokens for the messages
    """
    total = 0

    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            # Count content tokens
            total += count_tokens(content, model)
            # Add overhead for message structure (role, separators)
            # This is approximately 4 tokens per message for OpenAI format
            total += 4
        elif isinstance(content, list):
            # Handle multi-part content (e.g., vision messages)
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    total += count_tokens(part["text"], model)
                    total += 4

    # Add overhead for conversation structure
    total += 3  # Every conversation has ~3 tokens of overhead

    return total


class TokenCounter:
    """
    A reusable token counter for a specific model.

    Usage:
        counter = TokenCounter("gpt-4o")
        tokens = counter.count("Hello world")
    """

    def __init__(self, model: Optional[str] = None):
        """Initialize counter for a specific model."""
        self.model = model
        self._encoding = get_encoding(model)

    def count(self, text: str) -> int:
        """Count tokens in text."""
        if not text:
            return 0

        if self._encoding:
            try:
                return len(self._encoding.encode(text))
            except Exception:
                pass

        return len(text) // 4

    def count_messages(self, messages: list) -> int:
        """Count tokens for a list of messages."""
        return count_tokens_for_messages(messages, self.model)

    @property
    def is_accurate(self) -> bool:
        """Whether counting uses tiktoken (accurate) or approximation."""
        return self._encoding is not None


# Provide info about token counting accuracy
def get_token_counting_info() -> dict:
    """
    Get information about token counting capabilities.

    Returns:
        Dict with info about tiktoken availability and accuracy.
    """
    return {
        "tiktoken_available": TIKTOKEN_AVAILABLE,
        "method": "tiktoken" if TIKTOKEN_AVAILABLE else "approximation",
        "accuracy_note": (
            "Using tiktoken for accurate token counting"
            if TIKTOKEN_AVAILABLE
            else "Using character-based approximation (~4 chars/token). "
            "Install tiktoken for more accurate counting: pip install tiktoken"
        )
    }
