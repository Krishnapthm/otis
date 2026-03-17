# Re-exports removed to avoid circular import:
# src.api.crud → docs.py → src.services.file_handling
# → __init__.py → mcq_service → src.api.crud (circular)
#
# Consumers should import directly, e.g.:
#   from src.services.mcq_service import persist_generated_mcq_test_from_state
