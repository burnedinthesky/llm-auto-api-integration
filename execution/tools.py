from abc import ABC, abstractmethod
from typing import Any, Dict
from .runtime import Runtime
from blocks.block_generator import BlockGenerator


class LLMTool(ABC):
    @abstractmethod
    def get_tool_desc(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def execute(self, **kwargs) -> str:
        pass


class GenerateAppTool(LLMTool):
    def __init__(self, api_key: str):
        self.name = "generate_app"
        self.description = "Searches the web for the API information of the given app and writes an app tool class."
        self.parameters = {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "The name of the app to generate the tool for.",
                }
            },
            "required": ["app_name"],
            "additionalProperties": False,
        }

        self.block_generator = BlockGenerator(api_key)

    def get_tool_desc(self):
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "strict": True,
        }

    def execute(self, app_name: str) -> str:
        return (
            "App created successfully: "
            + self.block_generator.generate_and_save_block(app_name)
        )


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
