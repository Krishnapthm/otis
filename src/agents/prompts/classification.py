from langchain_core.prompts import PromptTemplate

scope_classifier_prompt = PromptTemplate.from_template(
    """
Classify the user input.

ALLOW only if the user is requesting quiz, test, or MCQ generation.
BLOCK if user is chatting generally, asking unrelated questions, or requesting disallowed content.
If unsure, output BLOCK.

Input:
{user_request}

Output: ALLOW or BLOCK
"""
)

intent_classifier_prompt = PromptTemplate.from_template(
    """
You are an intent classifier for an MCQ assistant.

Classify the user input into exactly one of:
- mcq_request
- followup
- utility_task
- clarification

Use the provided session summary for context.

Session summary:
{session_summary}

User message:
{user_message}

Return only the class label.
"""
)
