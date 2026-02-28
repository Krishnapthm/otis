from src.agents.utils.state import FinalMCQ, MCQOption, State


def assemble_final_mcqs_node(state: State) -> dict:
    ordered_drafts = sorted(
        state.get("mcq_drafts") or [], key=lambda draft: draft.question_index
    )

    final_mcqs = []
    for draft in ordered_drafts:
        options = draft.options or []
        options_by_key = {option.key: option.text for option in options}
        normalized_options = [
            MCQOption(key=key, text=options_by_key.get(key, ""))
            for key in ["A", "B", "C", "D"]
        ]
        final_mcqs.append(
            FinalMCQ(
                question_index=draft.question_index,
                question=draft.stem or "",
                options=normalized_options,
                right_answer=draft.answer or "A",
                explanation=draft.explanation,
            )
        )

    return {"final_mcqs": final_mcqs}


def finalize_metadata_node(state: State) -> dict:
    should_bump = bool(state.get("mcq_drafts")) or bool(state.get("artifact_bump"))
    if not should_bump:
        return {}

    current = state.get("artifact_version") or 0
    return {
        "artifact_version": current + 1,
    }
