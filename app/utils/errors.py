class PipelineError(Exception):
    """Base exception for pipeline errors."""


class JiraError(PipelineError):
    """Raised when Jira operations fail."""


class SeldonError(PipelineError):
    """Raised when MLServer operations fail."""


class PromptError(PipelineError):
    """Raised when prompt creation fails."""
