import io
import logging
import os
from typing import Optional

import aiohttp
from enums import SourceType
from pdfminer.high_level import extract_text

logger = logging.getLogger(__name__)


def extract_text_from_pdf(content) -> str:
    with io.BytesIO(content) as f:
        text = extract_text(f)
    return text


async def fetch_patterns() -> list[dict]:
    """
    Retrieve the list of patterns from the webserver.
    """

    auth_token = os.getenv("WEBSERVER_API_KEY")
    webserver_base_url = os.getenv("WEBSERVER_BASE_URL")
    api_url = f"{webserver_base_url}/api/patterns/"

    headers = {
        "Authorization": f"Api-Key {auth_token}",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                print(f"Failed to fetch patterns: {response.status}")
                return []


async def create_caught_message(
    match_id: str, content: str, additional_info: dict
) -> None:
    """
    Send a POST request to create a caught message.
    """
    auth_token = os.getenv("WEBSERVER_API_KEY")
    webserver_base_url = os.getenv("WEBSERVER_BASE_URL")
    api_url = f"{webserver_base_url}/api/caught_messages/"

    headers = {
        "Authorization": f"Api-Key {auth_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "user_id": additional_info.get("user"),
        "channel": additional_info.get("channel"),
        "timestamp": additional_info.get("ts"),
        "pattern_matched": match_id,
        "message_content": content,
        "file_name": (
            additional_info.get("file_name")
            if additional_info.get("source_type") == SourceType.FILE
            else None
        ),
        "file_id": (
            additional_info.get("file_id")
            if additional_info.get("source_type") == SourceType.FILE
            else None
        ),
        "source_type": additional_info.get("source_type"),
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, headers=headers, json=payload) as response:
            if response.status == 201:
                print(f"Caught message created: {payload}")
            else:
                logger.error(f"Failed to create caught message: {response.status}")
                error_data = await response.text()
                logger.error(f"Error details: {error_data}")


async def download_file(url: str, token: str) -> Optional[bytes]:
    """
    Downloads a file from a given URL using an authorization token.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, headers={"Authorization": f"Bearer {token}"}
        ) as response:
            if response.status == 200:
                return await response.read()

            else:
                logger.error(f"Failed to download file: {response.status}")
                return None


async def process_file(file_info: dict) -> Optional[str]:
    """
    Download the file and process it based on its type.
    """
    token = os.getenv("SLACK_BOT_TOKEN")
    url = file_info.get("url_private") or ""
    filetype = file_info.get("filetype")

    content = await download_file(url, str(token))
    if not content:
        return None

    if filetype == "pdf":
        return extract_text_from_pdf(content)
    else:
        logger.error(f"Unsupported file type: {filetype}")
        return None
