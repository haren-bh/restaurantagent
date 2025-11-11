import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from tools.vertexai import call_gemini

def test_call_gemini():
    """
    Tests the call_gemini function.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Define a simple prompt
    prompt = "What is the capital of France?"

    print(f"Testing call_gemini with prompt: '{prompt}'")

    # Call the function
    response = call_gemini(prompt)

    # Print the response
    print("\nResponse from Gemini:")
    print(response)

    # A simple assertion to check if the response is not empty
    assert response, "The response from Gemini should not be empty."

    print("\nTest with image:")
    image_prompt = "what is this"
    image_url = "https://gonpachi.jp/wp-content/uploads/sites/18/2020/01/gonpachi-shibuya-atmosphere5.jpg"
    image_mimetype = "image/jpeg"

    print(f"Testing call_gemini with prompt: '{image_prompt}' and image URL: {image_url}")
    image_response = call_gemini(prompt=image_prompt, url=image_url, mimetype=image_mimetype)

    print("\nResponse from Gemini (with image):")
    print(image_response)
    assert image_response, "The response from Gemini (with image) should not be empty."


if __name__ == "__main__":
    test_call_gemini()
