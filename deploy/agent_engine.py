import vertexai

def create_agent_engine(project,location):
    client = vertexai.Client(
        project=project,
        location=location,
    )

    agent_engine = client.agent_engines.create(
        config={"display_name":"memory-engine-agent-engine"},
    )
    print(agent_engine.api_resource.name)


project="datapipeline-372305"
location="us-central1"
create_agent_engine(project,location)

#projects/85469421903/locations/us-central1/reasoningEngines/1988888991297961984





