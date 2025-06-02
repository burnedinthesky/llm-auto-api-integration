from abc import ABC, abstractmethod
from typing import Any, Dict
from .runtime import Runtime
import sys
from pathlib import Path


from blocks.block_generator import BlockGenerator
import glob
import importlib
import inspect


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


class ListAppTool(LLMTool):
    def __init__(self):
        self.name = "list_apps"
        self.description = "Lists all the apps that have been generated."
        self.parameters = {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        }

    def get_tool_desc(self):
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "strict": True,
        }

    def execute(self):
        apps = []
        for file in glob.glob("./blocks/*.py"):
            # Convert file path to module name
            module_name = file.replace("/", ".").replace("\\", ".").replace(".py", "")
            while module_name.startswith("."):
                module_name = module_name[1:]  # Remove leading dot
            if "block_generator" in module_name:
                continue
            try:
                module = importlib.import_module(module_name, package=None)
                class_name = ""
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj):
                        class_name = name
                        break
                app_class = getattr(module, class_name)
                apps.append(
                    {
                        "app_name": app_class.app_id,
                        "app_desc": app_class.__doc__.strip(),
                    }
                )
            except ImportError as e:
                print(f"Warning: Could not import {module_name}: {e}")
                continue
        return "\n".join([f"{app['app_name']}\n{app['app_desc']}" for app in apps])


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
