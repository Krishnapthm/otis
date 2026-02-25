from langchain_core.prompts import PromptTemplate

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
PROMPTS = {
    "summarize": summarize_prompt,
    "summarize2": summarize_prompt2,
    "search_queries": search_queries,
    "search_queries_v2": summarize_prompt2,
    "before_agent_guardrail": before_agent_guardrail,
}
