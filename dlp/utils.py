import logging
import re
from typing import Optional

from .models import CaughtMessage, Pattern

logger = logging.getLogger(__name__)


def scan_message(content: str, additional_info: Optional[dict] = None) -> None:
    """
    Scans the given content against all active patterns.
    Saves any matches found.
    """
    patterns = Pattern.objects.all()

    for pattern in patterns:
        try:
            regex = re.compile(pattern.regex_pattern)
            if regex.search(content):

                CaughtMessage.objects.create(
                    message_content=content,
                    pattern_matched=pattern,
                    additional_info=additional_info,
                )

        except re.error:
            logger.error(f"Invalid regex pattern: {pattern.regex_pattern}")
            continue
