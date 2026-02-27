"""Centralised LLM and embedding model configuration for agent nodes."""

from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from langchain_openai import AzureChatOpenAI

load_dotenv()

embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://ollama:11434")

llm = AzureChatOpenAI(
    azure_deployment="gpt-4o-mini",
    api_version="2024-12-01-preview",
    streaming=True,
)

guardrail_llm = AzureChatOpenAI(
    azure_deployment="gpt-4.1-nano",
    api_version="2024-12-01-preview",
)

# --- Placeholder model aliases for modular MCQ pipeline nodes ---
# Replace any alias below with a different deployment name when needed.
planner_llm = AzureChatOpenAI(
    azure_deployment="gpt-4.1-nano",
    api_version="2024-12-01-preview",
)

intent_llm = AzureChatOpenAI(
    azure_deployment="gpt-4.1-nano",
    api_version="2024-12-01-preview",
)

retrieval_llm = AzureChatOpenAI(
    azure_deployment="gpt-4.1-nano",
    api_version="2024-12-01-preview",
)

stem_llm = AzureChatOpenAI(
    azure_deployment="gpt-4.1-nano",
    api_version="2024-12-01-preview",
)

options_llm = AzureChatOpenAI(
    azure_deployment="gpt-4.1-nano",
    api_version="2024-12-01-preview",
)

validator_llm = AzureChatOpenAI(
    azure_deployment="gpt-4.1-nano",
    api_version="2024-12-01-preview",
)

chat_no_tools_llm = AzureChatOpenAI(
    azure_deployment="gpt-4.1-nano",
    api_version="2024-12-01-preview",
    streaming=True,
)
