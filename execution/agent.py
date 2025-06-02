import os
import openai
from typing import Any, Dict
import json

from execution.tools import (
    GenerateAppTool,
    LLMTool,
    ExecuteCodeTool,
    ListAppTool,
    ImportAppTool,
)
from execution.runtime import Runtime

from .prompts import (
    EXECUTION_USER,
    PLANNING_USER,
    REVISE_PLAN_USER,
)


class Agent:
    def __init__(
        self,
        openai_api_key: str,
        model: str = "gpt-4.1",
    ):
        """
        Initializes the Agent with a runtime environment and OpenAI client.

        Args:
            runtime: The execution runtime environment.
            openai_api_key: Optional OpenAI API key. If not provided, it will
                            try to use the OPENAI_API_KEY environment variable.
            model: OpenAI model name. Defaults to "gpt-4o".
        """
        self.llm = openai.OpenAI(api_key=openai_api_key)
        self.model: str = model
        self.plan: str = ""

        # Create a shared runtime instance
        self.runtime = Runtime()

        self.tools: Dict[str, LLMTool] = {
            "execute_code": ExecuteCodeTool(self.runtime),
            "generate_app": GenerateAppTool(openai_api_key),
            "list_apps": ListAppTool(),
            "import_app": ImportAppTool(self.runtime),
        }
        self.tool_descs: list[dict[str, Any]] = [
            tool.get_tool_desc() for tool in self.tools.values()
        ]

        self.plan_generation_messages: list[dict[str, str]] = []
        self.execution_messages: list[dict[str, str]] = []

    def _generate_plan(self, task_description: str) -> str:
        """
        Generates an initial execution plan based on the task description.
        This plan can include steps to execute code using the runtime.
        """
        self.plan_generation_messages = [
            {
                "role": "user",
                "content": PLANNING_USER.format(task_description=task_description),
            }
        ]

        response = self.llm.responses.create(
            model=self.model,
            input=self.plan_generation_messages,
        )
        self.plan = response.output_text
        self.plan_generation_messages.append(
            {
                "role": "assistant",
                "content": self.plan,
            }
        )
        return self.plan

    def _revise_plan(self, feedback: str) -> str:
        """
        Revises the plan based on user feedback.
        """
        self.plan_generation_messages.append(
            {
                "role": "user",
                "content": REVISE_PLAN_USER.format(plan=self.plan, feedback=feedback),
            }
        )
        response = self.llm.responses.create(
            model=self.model,
            input=self.plan_generation_messages,
        )
        self.plan = response.output_text
        self.plan_generation_messages.append(
            {
                "role": "assistant",
                "content": self.plan,
            }
        )
        return self.plan

    def _execute_plan(self) -> None:
        """
        Executes the approved plan.
        """
        self.execution_messages = [
            {
                "role": "developer",
                "content": EXECUTION_USER.format(plan=self.plan),
            }
        ]
        while True:
            try:
                response = self.llm.responses.create(
                    model=self.model,
                    input=self.execution_messages,
                    tools=self.tool_descs,
                )

                print(self.execution_messages)
                print(response.output_text)

                if response.output_text == "done":
                    break

                if response.output[0].type == "function_call":
                    function_call = response.output[0]
                    function_name = function_call.name
                    function_args = json.loads(function_call.arguments)

                    tool = self.tools.get(function_name)
                    if not tool:
                        self.execution_messages.append(
                            {
                                "role": "user",
                                "content": f"Unknown tool Error: {function_name}",
                            }
                        )
                        continue

                    self.execution_messages.append(response.output[0])

                    result: str = tool.execute(**function_args)
                    self.execution_messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": function_call.call_id,
                            "output": result,
                        }
                    )
                    continue

                self.execution_messages.append(
                    {
                        "role": "assistant",
                        "content": response.output_text,
                    }
                )
            except Exception as e:
                print(e)
                self.execution_messages.append(
                    {
                        "role": "user",
                        "content": "An error occurred, please revise your function call and try again. "
                        + str(e),
                    }
                )

    def run(self, task_description: str) -> None:
        """
        Runs the agent's three-step process: Generate, Revise, Execute.
        """

        # self._generate_plan(task_description)
        # print("AI: Initial plan generated:")
        # print(self.plan)

        # while True:
        #     user_input = input(
        #         "USER: Review the plan. Type 'go' to approve, or provide feedback to revise: "
        #     )
        #     if user_input.lower() == "go":
        #         print("AI: Plan approved by user.")
        #         break
        #     elif user_input.lower() == "exit":
        #         print("AI: Exiting without execution.")
        #         return
        #     else:
        #         self._revise_plan(user_input)
        #         print("AI: Plan revised:")
        #         print(self.plan)

        try:
            self.plan = "List all apps and import Notion into the runtime"
            self._execute_plan()
        except Exception as e:
            print(
                f"AI_ERROR: An unexpected error occurred during the agent's run cycle: {e}"
            )


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    print("AI: Initializing agent...")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    agent = Agent(openai_api_key=api_key)

    # task = input("What's your task? ")
    task = ""
    agent.run(task)
