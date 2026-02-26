from langchain_core.prompts import PromptTemplate

planner_prompt = PromptTemplate.from_template(
    """
Create an MCQ generation plan from the user request.

User message:
{user_message}

Session summary:
{session_summary}

Previous plan (if any):
{previous_plan}

Validation feedback (if any):
{validation_feedback}

Return a plan with:
- topic
- difficulty (EASY|MEDIUM|HARD)
- num_questions
- blooms_level (REMEMBER|UNDERSTAND|APPLY|ANALYZE|EVALUATE|CREATE)
- stem_guidance
- distractor_strategy
- retrieval_queries
- concepts
"""
)
