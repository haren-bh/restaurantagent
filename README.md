# Restaurant Agent

This document provides instructions for setting up and running the Restaurant Agent locally.

## Local Development

To run this project locally, you need to configure several environment variables. You can do this by creating a `.env` file in the root of the project or by exporting these variables in your shell.

### Required Environment Variables

```bash
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT="YOUR GOOGLE CLOUD PROJECT ID"
GOOGLE_CLOUD_LOCATION="CLOUD LOCATION eg. us-central1"
AGENT_ENGINE_ID="AGENT ENGINE ID"
GOOGLE_MAPS_API_KEY="YOUR GOOGLE MAPS API KEY"
```

**Variable Descriptions:**

*   `GOOGLE_GENAI_USE_VERTEXAI`: Set to `1` to use Vertex AI.
*   `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID.
*   `GOOGLE_CLOUD_LOCATION`: The Google Cloud location, for example, `us-central1`.
*   `AGENT_ENGINE_ID`: The ID of your agent engine. This is the last number in the agent engine URL.
*   `GOOGLE_MAPS_API_KEY`: Your Google Maps API key. You can obtain this from the Google Cloud Console.

## Additional Resources

For a detailed setup guide, please refer to the following blog post:
[Manage your user sessions with ADK and Vertex AI Memory Engine](https://medium.com/google-cloud/manage-your-user-sessions-with-adk-and-vertex-ai-memory-engine-447c53b189df)

## Cloud Run Deployment

You can also run this application in Google Cloud Run. Here is an example of this code deployed to Cloud Run:
[Restaurant Finder Demo](https://restaurantfinder-85469421903.us-central1.run.app/)