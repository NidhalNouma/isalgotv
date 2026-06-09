
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from typing import Any

class TokenUsageCallbackHandler(BaseCallbackHandler):
    """Callback handler for tracking token usage."""

    def __init__(self):
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Run when LLM ends running."""
        if response.llm_output and "token_usage" in response.llm_output:
            token_usage = response.llm_output["token_usage"]
            if "total_tokens" in token_usage:
                self.total_tokens += token_usage["total_tokens"]
            if "prompt_tokens" in token_usage:
                self.prompt_tokens += token_usage["prompt_tokens"]
            if "completion_tokens" in token_usage:
                self.completion_tokens += token_usage["completion_tokens"]

    def get_token_usage(self):
        return {
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
        }


