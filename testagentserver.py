from langgraph_sdk import get_client
import asyncio

client = get_client(url="http://localhost:8132")


async def main():
    async for chunk in client.runs.stream(
        None,  # Threadless run
        "agent",  # Name of assistant. Defined in langgraph.json.
        input={
            "doc_ids": ["6d72beda-f0c5-4629-8290-80075ba7bf7e"],
            "collection_name": "project_1f4f78e8-ba1c-4db4-804e-7495f54d2d4d_v1",
        },
    ):
        print(f"Receiving new event of type: {chunk.event}...")
        print(chunk.data)
        print("\n\n")


asyncio.run(main())
