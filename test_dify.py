
from services.dify_client import extract_capabilities

agent_name = "SearchAgent"

tool_description = (
    "This agent can search academic papers "
    "using a web search API."
)

try:
    capabilities = extract_capabilities(
        agent_name,
        tool_description,
    )

    print("Agent:", agent_name)
    print("Dify 识别的候选能力:", capabilities)

except Exception as e:
    print("调用失败:", e)
