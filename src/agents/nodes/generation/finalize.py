from src.agents.utils.state import MCQDraft, QuestionSubgraphState


def finalize_draft_node(state: QuestionSubgraphState) -> dict:
    draft = MCQDraft(
        question_index=state.get("question_index") or 0,
        stem=state.get("stem"),
        options=state.get("options"),
        distractors=state.get("distractors"),
        answer=state.get("correct_answer"),
        explanation=state.get("explanation") or "",
        validation_feedback=state.get("validation_feedback", ""),
    )
    return {
        "draft": draft,
    }
