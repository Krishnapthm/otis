from langchain_core.prompts import PromptTemplate
from ollama import generate

summarize_prompt = PromptTemplate.from_template(
    "Your job is to briefly summarize the concepts of the document {document}. "
    "make sure the summaries are brief at the same time without missing out any concepts."
)

summarize_prompt2 = PromptTemplate.from_template(
    "Extract key concepts from this document. "
    "For each concept, provide:\n"
    "- Name: [concept name]\n"
    "- Summary: [one sentence, max 10 words]\n"
    "- Query: [search query, max 8 words]\n\n"
    "Be concise. Limit to 5 concepts maximum.\n\n"
    "Document: {document}"
)

search_queries = PromptTemplate.from_template(
    "Generate 1 search query for concept name: {concept_name} and summary: {concept_summary}"
)

query_generation = PromptTemplate.from_template(
    """
You are generating semantic retrieval queries for MCQ generation.

User prompt:
{user_prompt}

Concept map extracted from selected documents:
{concept_map}

Generate exactly {num_queries} concise, non-redundant semantic search queries.
Queries must target concepts, maximize coverage, and avoid surface-level phrasing.
Return only the query list.
"""
)

naive_mcq_generation = PromptTemplate.from_template(
    """
Generate 5 multiple-choice questions grounded strictly in the provided context.

User request:
{user_prompt}

Retrieved context:
{retrieved_context}

Output format:
1) Question text
   A. Option A
   B. Option B
   C. Option C
   D. Option D
   Answer: <A|B|C|D>

Do not include explanations.
"""
)

# before_agent_guardrail = PromptTemplate.from_template(
#     "Your job is to classify user intent."
#     "ALLOW only if the user is requesting quiz, test or mcq generation"
#     "BLOCK is chatting or asking general questions. "
#     "Input: {user_request}"
#     "No explanation."
# )
before_agent_guardrail = PromptTemplate.from_template(
    """
Classify the user input.

ALLOW only if the user is requesting quiz, test, or MCQ generation.

BLOCK if the user is asking questions, chatting, or asking about MCQs themselves.

If unsure, output BLOCK.

Input:
{user_request}

Output:
ALLOW or BLOCK
"""
)

generate_search_queriesv2 = PromptTemplate.from_template(
    """
Generate 2 search queries for the following 

"""
)

PROMPTS = {
    "summarize": summarize_prompt,
    "summarize2": summarize_prompt2,
    "search_queries": search_queries,
    "search_queries_v2": summarize_prompt2,
    "query_generation": query_generation,
    "naive_mcq_generation": naive_mcq_generation,
    "before_agent_guardrail": before_agent_guardrail,
}
