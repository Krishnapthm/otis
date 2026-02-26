from langchain_core.prompts import PromptTemplate

validator_prompt = PromptTemplate.from_template(
    """
Validate this MCQ draft.

Plan:
{plan}

Draft:
{draft}

Check only:
- stem clarity
- distractor plausibility
- single correct answer
- bloom alignment

Do not evaluate explanation quality.

Return JSON with keys:
- validation_passed: bool
- validation_score: float
- validation_feedback: string
"""
)
