from typing import Optional

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types


from google.adk.memory import VertexAiMemoryBankService
from google.adk.sessions import VertexAiSessionService
#from agent import root_agent  # type: ignore
from google.adk.runners import Runner
from google.genai import types
import vertexai
from google.adk.memory import VertexAiMemoryBankService

def createVertexAIMemoryBank(PROJECT,LOCATION):
    client = vertexai.Client(project=PROJECT, location=LOCATION)

    agent_engine = client.agent_engines.create(
        config={
            "context_spec": {
                "memory_bank_config": {
                    "generation_config": {
                        "model": f"projects/{PROJECT}/locations/{LOCATION}/publishers/google/models/gemini-2.5-flash"
                    }
                }
            }
        }
    )
    print(agent_engine.api_resource.name.split("/")[-1])


def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": (
                "The weather in New York is sunny with a temperature of 25 degrees"
                " Celsius (77 degrees Fahrenheit)."
            ),
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }



async def add_session_to_memory(
        callback_context: CallbackContext
) -> Optional[types.Content]:
    """Automatically save completed sessions to memory bank """
    if hasattr(callback_context, "_invocation_context"):
        invocation_context = callback_context._invocation_context
        if invocation_context.memory_service:
            await invocation_context.memory_service.add_session_to_memory(
                invocation_context.session
            )


root_agent = Agent(
    name="weather_agent",
    model="gemini-2.5-flash",
    description=(
        "Agent to answer questions about weather in a city."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about weather in a city."
    ),
    tools=[
        get_weather,
        PreloadMemoryTool() # This tool will be automatically executed by ADK
    ],
    after_agent_callback=add_session_to_memory
)


agent_engine_id = "projects/85469421903/locations/us-central1/reasoningEngines/1988888991297961984"
agent_engine_id="1507566781122740224" #only the last bit
PROJECT_ID="datapipeline-372305"
LOCATION="us-central1"
session_service = VertexAiSessionService(
    project=PROJECT_ID, location=LOCATION, agent_engine_id=agent_engine_id
)
memory_service = VertexAiMemoryBankService(
    project=PROJECT_ID, location=LOCATION, agent_engine_id=agent_engine_id
)

print(f"Agent Engine Id: {agent_engine_id}")

USER_ID = "user"
#USER_ID = "haren"

runner = Runner(
    app_name=root_agent.name,  # type: ignore
    agent=root_agent,
    session_service=session_service,
    memory_service=memory_service,
)


async def call_agent(query, runner):
    session = await session_service.create_session(
        app_name=root_agent.name,  # type: ignore
        user_id=USER_ID,
    )
    content = types.Content(role="user", parts=[types.Part(text=query)])
    events = runner.run(
        user_id=session.user_id, session_id=session.id, new_message=content
    )

    for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("\nAgent Response: ", final_response)


import asyncio


async def runagent():
    await call_agent("Where do I live?", runner)


if __name__ == "__main__":
    asyncio.run(runagent())
    #createVertexAIMemoryBank(PROJECT_ID,LOCATION)



