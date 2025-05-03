class BaseLLMError(Exception):
    """Base class for all exceptions related to LLM"""

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message


class InvalidLLMResponse(BaseLLMError):
    """Exception raised when the LLM response is invalid"""

    def __init__(self, message: str) -> None:
        super().__init__(f"Invalid LLM response: {message}")


class LLMRequestError(BaseLLMError):
    """Exception raised when there is an error in the LLM request"""

    def __init__(self, message: str) -> None:
        super().__init__(f"LLM request error: {message}")
