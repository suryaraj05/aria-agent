from typing import Any


def format_markdown(content: str) -> str:
    """Format text as markdown."""
    return content.strip() + "\n"


def parse_results(raw: Any) -> Any:
    """Helper for parsing raw data into structured output."""
    return raw
