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

from dotenv import load_dotenv
import os


load_dotenv()

GOOGLE_CLOUD_PROJECT=os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION=os.getenv("GOOGLE_CLOUD_LOCATION")
agent_engine_id=os.getenv("agent_engine_id")

class RestaurantRunner:
    def __init__(self, agent: Agent, user_id: str = "user", session_id: Optional[str] = None):
        self.agent = agent
        self.user_id = user_id
        self._session_id = session_id
        self.session_service = VertexAiSessionService(
            project=GOOGLE_CLOUD_PROJECT,
            location=GOOGLE_CLOUD_LOCATION,
            agent_engine_id=agent_engine_id
        )
        self.memory_service = VertexAiMemoryBankService(
            project=GOOGLE_CLOUD_PROJECT,
            location=GOOGLE_CLOUD_LOCATION,
            agent_engine_id=agent_engine_id
        )
        self.runner = Runner(
            app_name=self.agent.name,
            agent=self.agent,
            session_service=self.session_service,
            memory_service=self.memory_service,
        )

    async def get_session(self):
        current_session_id = self._session_id

        if current_session_id:
            try:
                session = await self.session_service.get_session(
                    app_name=self.agent.name,
                    user_id=self.user_id,
                    session_id=current_session_id
                )
                if session:
                    # Update the instance's _session_id if a valid session was retrieved
                    self._session_id = session.id
                    return session
            except Exception as e:
                print(f"Error retrieving session {current_session_id}: {e}")
        
        # If no session_id or session not found, create a new one
        session = await self.session_service.create_session(
            app_name=self.agent.name,
            user_id=self.user_id,
        )
        self._session_id = session.id  # Store the newly created session_id
        return session

    async def call_agent(self, query: str):
        session = await self.get_session()
        content = types.Content(role="user", parts=[types.Part(text=query)])
        events = self.runner.run(
            user_id=session.user_id, session_id=session.id, new_message=content
        )

        for event in events:
            if event.is_final_response():
                final_response = event.content.parts[0].text
                print("\nAgent Response: ", final_response)
                return final_response
        return None
