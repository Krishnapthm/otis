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

Retrieved context:
{retrieved_context}

Return JSON with keys:
- options: list[str] (length 4)
- correct_answer: one of A|B|C|D
- explanation: short explanation for why the correct option is correct
"""
)

distractor_generation_prompt = PromptTemplate.from_template(
    """
Generate 3 plausible distractors for this MCQ stem.

Plan:
{plan}

Stem:
{stem}

Retrieved context:
{retrieved_context}

Return only a JSON list of 3 strings.
"""
)
