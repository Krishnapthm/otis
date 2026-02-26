from src.agents.prompts.classification import (
    intent_classifier_prompt,
    scope_classifier_prompt,
)
from src.agents.prompts.planner import planner_prompt
from src.agents.prompts.generation import (
    distractor_generation_prompt,
    options_generation_prompt,
    stem_generation_prompt,
)
from src.agents.prompts.validator import validator_prompt
from src.agents.prompts.chat import chat_no_tools_prompt

PROMPT_REGISTRY = {
    "scope_classifier": scope_classifier_prompt,
    "intent_classifier": intent_classifier_prompt,
    "planner": planner_prompt,
    "stem_generation": stem_generation_prompt,
    "options_generation": options_generation_prompt,
    "distractor_generation": distractor_generation_prompt,
    "validator": validator_prompt,
    "chat_no_tools": chat_no_tools_prompt,
}
