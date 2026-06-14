cat > main.py << 'EOF'
"""
App - AgentCore Gateway + MCP + DynamoDB + Lambda
Auto Insurance Company: Apex Auto Insurance
"""

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from strands import Agent
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()
log = app.logger

# ── Paste your Gateway URL here ───────────────────────────────────────────────
GATEWAY_URL = "https://apex-mcp-gateway-xxxxxxxxxx.gateway.bedrock-agentcore.us-east-2.amazonaws.com/mcp"
REGION = "us-east-2"

_agent = None

def get_signed_headers():
    """Generate SigV4 signed headers for AgentCore Gateway auth."""
    session = boto3.session.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    request = AWSRequest(method="POST", url=GATEWAY_URL, data=b"")
    SigV4Auth(credentials, "bedrock-agentcore", REGION).add_auth(request)
    return dict(request.headers)

def get_agent():
    global _agent
    if _agent is not None:
        return _agent

    headers = get_signed_headers()
    mcp_client = MCPClient(
        lambda: streamablehttp_client(GATEWAY_URL, headers=headers)
    )

    with mcp_client:
        tools = mcp_client.list_tools_sync()
        log.info(f"Loaded {len(tools)} MCP tools: {[t.tool_name for t in tools]}")

    _agent = Agent(
        model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        tools=[mcp_client],
        system_prompt="""You are Apex, a helpful AI assistant for Apex Auto Insurance Company.

You have access to three tools via the AgentCore Gateway:

1. get-policy(policy_id)
   - Looks up an existing policy by ID (e.g. POL-001)
   - Returns: customer name, vehicle, coverage, premium, deductible, status, expiry

2. file-claim(policy_id, description, damage_type)
   - Files a new insurance claim against an existing policy
   - damage_type options: collision, theft, weather, vandalism, general

3. get-quote(vehicle, coverage, driver_age, customer_name)
   - Generates a real-time insurance quote
   - coverage options: liability, collision, comprehensive

BEHAVIOR RULES:
- Always use tools for policy lookups, claims, and quotes.
- Present tool results in a friendly, clear format — never dump raw JSON.
- If a tool returns an error, apologize and explain what information is needed.
- For topics outside auto insurance, politely redirect.

Always be professional, empathetic, and concise."""
    )
    return _agent


@app.entrypoint
async def invoke(payload, context):
    log.info(f"Received payload: {payload}")

    user_input = (
        payload.get("inputText")
        or payload.get("prompt")
        or payload.get("input")
        or payload.get("message")
        or str(payload)
    )

    agent = get_agent()

    full_response = ""
    stream = agent.stream_async(user_input)
    async for event in stream:
        if "data" in event and isinstance(event["data"], str):
            full_response += event["data"]

    yield full_response


if __name__ == "__main__":
    app.run()
EOF