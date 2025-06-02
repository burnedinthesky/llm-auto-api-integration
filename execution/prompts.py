PLANNING_USER = "Generate a plan for: {task_description}. In your plan, you may include planning the usage of tools 'ListApps', 'GenerateApp' for third party integrations. Directly output the plan."


REVISE_PLAN_USER = (
    "Plan: {plan}\nFeedback: {feedback}. Directly output the revised plan."
)


EXECUTION_USER = "Execute this plan using all available tools. If something fails, fix it and try again. Keep going until it's done. Once it's done, output only one single token 'done'.\nPlan: {plan}"
