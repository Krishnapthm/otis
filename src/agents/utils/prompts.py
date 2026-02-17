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

PROMPTS = {
    "summarize": summarize_prompt,
    "summarize2": summarize_prompt2,
    "search_queries": search_queries,
}
