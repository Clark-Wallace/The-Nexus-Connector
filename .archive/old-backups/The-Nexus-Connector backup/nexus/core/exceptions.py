"""Custom exceptions for Nexus."""


class NexusError(Exception):
    """Base exception for all Nexus errors."""
    pass


class ProviderError(NexusError):
    """Error related to AI provider operations."""
    pass


class ToolExecutionError(NexusError):
    """Error during tool execution."""
    pass


class ConfigurationError(NexusError):
    """Error in configuration."""
    pass


class AuthenticationError(NexusError):
    """Authentication-related error."""
    pass