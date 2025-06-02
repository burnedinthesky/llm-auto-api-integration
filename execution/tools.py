from abc import ABC, abstractmethod
from typing import Any, Dict
from .runtime import Runtime


class LLMTool(ABC):
    @abstractmethod
    def get_tool_desc(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def execute(self, **kwargs) -> str:
        pass


class ExecuteCodeTool(LLMTool):
    def __init__(self):
        self.name = "execute_code"
        self.description = "Execute Python code in a jupyter notebook. The same kernel is through all calls."
        self.parameters = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute.",
                }
            },
            "required": ["code"],
            "additionalProperties": False,
        }

        self.runtime = Runtime()

    def get_tool_desc(self):
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "strict": True,
        }

    def execute(self, code: str) -> str:
        result = self.runtime.execute_code(code)
        return "\n".join([str(r) for r in result])
