
import logging
from google.adk.agents import LlmAgent
from restaurantagent.agents.agents import create_restaurant_finder_agent,create_generic_search_agent
from google.adk.sessions import InMemorySessionService, Session
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from typing import Optional

temp_service = InMemorySessionService()

# Configure logging to show detailed output from all modules
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

restaurant_finder_agent = create_restaurant_finder_agent()
generic_search_agent=create_generic_search_agent()

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

def create_root_agent() -> LlmAgent:
    """Creates and configures the Root agent."""

    # A delegating LlmAgent uses its own LLM to route user requests to the
    # appropriate sub-agent based on their descriptions.
    agent = LlmAgent(
        name="root_agent",
        model="gemini-2.5-pro",
        description="Top level agent that acts as controller",
        instruction=(
            "You are a master controller agent that delegates tasks to specialized sub-agents. "
            "Analyze the user's request and route it to the correct agent based on the following rules:\n"
            "1. For finding restaurants: If the user asks to find restaurants, eateries, or food places "
            "(e.g., 'find me some restaurants', 'any good pizza places nearby?'), you MUST use the `restaurant_agent`.\n"
            "2. For finding menus: If the user asks for the menu of a specific restaurant, you MUST use the `restaurant_menu_agent`. If you cannot find the url for menu use generic_search_agent to get the url. If the user asks menu for all the restaurants, find the menu of all the restaurants one at a time and show the menu\n"
            "3. For general questions: For any other topic, question, or request that is not about finding restaurants or their menus, "
            "you MUST use the `generic_search_agent`.\n"
            "4. For combined requests: If the user asks to find restaurants AND their menus, first use `restaurant_agent` to find the list of restaurants, "
            "and then use `restaurant_menu_agent` to get the menus for the results."
        
            ),
        sub_agents=[restaurant_finder_agent,generic_search_agent],
        tools=[PreloadMemoryTool()],
        output_key="searched_restaurant_info",
        after_agent_callback=add_session_to_memory,
    )
    return agent

root_agent=create_root_agent()
