import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentmain.runner import RestaurantRunner
from agent import root_agent


async def main():
    """
    This is the main function that runs the agent in an interactive loop.
    """
    # Create a runner for the agent. The runner will maintain the session.
    runner = RestaurantRunner(agent=root_agent, user_id="haren")

    print("Agent is ready. Type your query, or 'exit'/'quit' to end the session.")

    while True:
        try:
            query = input("\nUser: ")
            if query.lower() in ["exit", "quit"]:
                print("Ending chat session.")
                break
            
            if not query:
                continue

            # Call the agent with the user's query
            await runner.call_agent(query)

        except (KeyboardInterrupt, EOFError):
            print("\nEnding chat session.")
            break


if __name__ == "__main__":
    asyncio.run(main())
