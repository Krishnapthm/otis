from langchain_core.prompts import PromptTemplate

stem_generation_prompt = PromptTemplate.from_template(
    """
Generate one MCQ question stem for question index {question_index}.

Plan:
{plan}

Retrieved context:
{retrieved_context}

Return only the question stem text.
"""
)

options_generation_prompt = PromptTemplate.from_template(
    """
Generate four options for this MCQ stem and mark exactly one correct answer.

Plan:
{plan}

Stem:
{stem}

Distractor strategy:
{distractor_strategy}

Requirements:
- exactly one option must be fully correct
- the other three options must be plausible but clearly incorrect
- avoid overlap/near-duplicates across options
- keep option lengths balanced

Return JSON with keys:
- options: list[object] (length 4), each object must include:
    - key: one of A|B|C|D
    - text: option text only (do not prefix with "A.", "B)", etc.)
- correct_answer: one of A|B|C|D
- explanation: short explanation for why the correct option is correct
"""
)
