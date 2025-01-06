from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

PROMPT_DIR= BASE_DIR / 'suncodes_document' / 'prompt'

PROMPT_TEXT_TRANSLATE = PROMPT_DIR / 'text_translate.md'
PROMPT_QUESTION_LEVEL = PROMPT_DIR / 'question_level.md'
