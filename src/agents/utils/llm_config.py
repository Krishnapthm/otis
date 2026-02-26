"""Centralised LLM and embedding model configuration for agent nodes."""

from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from langchain_openai import AzureChatOpenAI

load_dotenv()

embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://ollama:11434")

llm = AzureChatOpenAI(
    azure_deployment="gpt-4o-mini",
    api_version="2024-12-01-preview",
)

guardrail_llm = AzureChatOpenAI(
    azure_deployment="gpt-4.1-nano",
    api_version="2024-12-01-preview",
)
