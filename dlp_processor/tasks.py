import logging
import re

from enums import SourceType
from utils import create_caught_message, fetch_patterns, process_file

logger = logging.getLogger(__name__)


async def scan_message_task(message_text: str, additional_info: dict):
    patterns = await fetch_patterns()
    message_text = message_text or ""
    print(f"Scanning message: {message_text}")
    print(f"Additional info: {additional_info}")

    # Scan the message text
    for pattern in patterns:
        regex = re.compile(pattern["regex_pattern"])
        if regex.search(message_text):
            additional_info["source_type"] = SourceType.MESSAGE
            await create_caught_message(pattern["id"], message_text, additional_info)

    # Process attached files
    files = additional_info.get("files", [])

    for file_info in files:
        file_text = await process_file(file_info)
        file_text = file_text or ""

        for pattern in patterns:
            regex = re.compile(pattern["regex_pattern"])
            if regex.search(file_text):

                additional_info["file_name"] = file_info.get("name")
                additional_info["file_id"] = file_info.get("id")
                additional_info["source_type"] = SourceType.FILE

                await create_caught_message(pattern["id"], file_text, additional_info)


# async def scan_file_task(file_info: dict, additional_info: dict):
#     patterns = await fetch_patterns()
#     content = await process_file(file_info)
#     content = content or ""

#     for pattern in patterns:
#         regex = re.compile(pattern["regex_pattern"])
#         if regex.search(content):
#             await create_caught_message(pattern["id"], content, additional_info)
