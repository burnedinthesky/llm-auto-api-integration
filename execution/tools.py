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
        # Get the absolute path to the blocks directory
        project_root = Path(__file__).resolve().parent.parent
        blocks_dir = project_root / "blocks"

        apps = []
        for file_path in blocks_dir.glob("*.py"):
            if "block_generator" in file_path.name:
                continue

            # Convert file path to module name
            module_name = f"blocks.{file_path.stem}"

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
    def __init__(self, runtime: Runtime = None):
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

        self.runtime = runtime if runtime else Runtime()

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


class ImportAppTool(LLMTool):
    def __init__(self, runtime: Runtime = None):
        self.name = "import_app"
        self.description = "Import a generated app tool into the jupyter runtime to make it available for use in code execution."
        self.parameters = {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "The name of the app to import (as shown by list_apps).",
                }
            },
            "required": ["app_name"],
            "additionalProperties": False,
        }

        self.runtime = runtime if runtime else Runtime()

    def get_tool_desc(self):
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "strict": True,
        }

    def execute(self, app_name: str) -> str:
        # Get the absolute path to the blocks directory
        project_root = Path(__file__).resolve().parent.parent
        blocks_dir = project_root / "blocks"

        # Find the module file for the app
        for file_path in blocks_dir.glob("*.py"):
            if "block_generator" in file_path.name:
                continue

            # Convert file path to module name
            module_name = f"blocks.{file_path.stem}"

            try:
                # Import temporarily to check the app_id
                module = importlib.import_module(module_name, package=None)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and hasattr(obj, "app_id"):
                        if obj.app_id == app_name:
                            # Found the right app, now import it into the runtime
                            import_code = f"""
import sys
# Add project root to sys.path if not already there
project_root = '{project_root}'
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from {module_name} import {name}

# Make the class available in the runtime
globals()['{name}'] = {name}
print(f"Successfully imported {name} class for app '{app_name}'")
print(f"To use it, create an instance: {app_name.replace('.', '_')} = {name}(api_key='your_key')")
"""
                            result = self.runtime.execute_code(import_code)
                            return "\n".join([str(r) for r in result])
            except Exception as e:
                continue

        return f"Error: Could not find app with name '{app_name}'. Use list_apps to see available apps."
