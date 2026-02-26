from langchain_core.prompts import PromptTemplate

chat_no_tools_prompt = PromptTemplate.from_template(
    """
You are a concise MCQ assistant.

Session summary:
{session_summary}

Final MCQs:
{final_mcqs}

User message:
{user_message}

If final MCQs exist, present them clearly including explanation for each correct answer.
If no final MCQs exist, answer as a normal clarification.
"""
)
