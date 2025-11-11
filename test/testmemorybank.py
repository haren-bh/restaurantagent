import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import vertexai

load_dotenv()

# Load environment variables (assuming they are set in the .env file)
# These are needed for direct Vertex AI SDK calls
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
AGENT_ENGINE_ID = os.getenv("agent_engine_id") # Renamed to avoid conflict with local variable

async def fetch_all_memory(user_id: str):
    """
    Fetches all memories for a given user ID using the Vertex AI SDK.
    """
    if not all([GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, AGENT_ENGINE_ID]):
        print("Error: Google Cloud project, location, or agent engine ID not set in environment variables.")
        return

    print(f"Fetching all memories for user: {user_id}")

    try:
        vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)
        client = vertexai.Client(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)

        # Construct the agent engine resource name
        agent_engine_resource_name = f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{GOOGLE_CLOUD_LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}"
        print(agent_engine_resource_name)
        # Define the scope for retrieval
        #scope = {"user_id": user_id}
        scope={"app_name":"weather_agent","user_id":user_id}

        # Retrieve all memories for the given scope
        results_pager = client.agent_engines.memories.retrieve(
            name=agent_engine_resource_name,
            scope=scope
        )

        memory = client.agent_engines.memories.get(
                    name="projects/85469421903/locations/us-central1/reasoningEngines/1507566781122740224/memories/8448853506260992000")
        print(memory)
        

        all_memories = list(results_pager)
        print(all_memories)

        if all_memories:
            print("\nRetrieved All Memories:")
            for retrieved_memory in all_memories:
                # The structure of retrieved_memory is RetrieveMemoriesResponseRetrievedMemory
                # which contains a 'memory' attribute that is a Memory object.
                # The Memory object has a 'fact' attribute.
                print(f"- Fact: {retrieved_memory.memory.fact}")
                print(f"  Name: {retrieved_memory.memory.name}")
                # You can print other attributes of retrieved_memory.memory as needed
        else:
            print(f"\nNo memories found for user '{user_id}' with scope {scope}.")

    except Exception as e:
        print(f"\nAn error occurred while fetching all memories: {e}")





if __name__ == "__main__":
    asyncio.run(fetch_all_memory("haren"))
