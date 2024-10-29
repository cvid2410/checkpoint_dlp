import asyncio
import json
import os
import re

import aio_pika
import aiohttp


class Manager:

    def __init__(self, queue_name: str, tasks: dict):
        self.loop = asyncio.get_event_loop()
        self.queue_name = queue_name
        self.tasks = tasks

        self.connection = None
        self.channel = None
        self.queue = None

    async def _connect(self):
        """Establish a connection to RabbitMQ."""

        rabbitmq_user = os.getenv("RABBITMQ_USER")
        rabbitmq_password = os.getenv("RABBITMQ_PASSWORD")

        self.connection = await aio_pika.connect_robust(
            host="rabbitmq",
            login=str(rabbitmq_user),
            password=str(rabbitmq_password),
            loop=self.loop,
        )

        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)
        self.queue = await self.channel.declare_queue(self.queue_name, durable=True)

    async def close(self):
        """Close the connection to RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def _get_messages(self):
        """Read and pop messages from SQS queue"""
        if self.connection is None or self.connection.is_closed:
            await self._connect()

        messages = []

        try:
            message = await self.queue.get(fail=False, timeout=5)
            if message:
                messages.append(message)
            else:
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Error fetching messages: {e}")
        return messages

    async def main(self) -> None:
        """For a given task:
        >>> async def say(something):
                pass

        Messages from queue are expected to have the format:
        >>> message = dict(task='say', args=('something',), kwargs={})
        >>> message = dict(task='say', args=(), kwargs={'something': 'something else'})
        """

        while True:
            messages = await self._get_messages()

            print(f"Received {len(messages)} messages")

            for message in messages:
                body = json.loads(message.body.decode())

                task_name = body.get("task")
                args = body.get("args", ())
                kwargs = body.get("kwargs", {})

                task = self.tasks.get(task_name)
                if task:
                    await task(*args, **kwargs)
                    await message.ack()
            await asyncio.sleep(1)


async def fetch_patterns():
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


async def scan_message_task(content: str, additional_info: dict):
    patterns = await fetch_patterns()
    matches = []

    for pattern in patterns:
        regex = re.compile(pattern["regex_pattern"])
        if regex.search(content):
            matches.append(pattern["name"])

    # Handle matches
    if matches:
        print(f"Leaks found: {matches}")

    else:
        print("No leaks found.")


tasks = {
    "scan_message": scan_message_task,
}

if __name__ == "__main__":
    manager = Manager(queue_name="slack_messages", tasks=tasks)
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(manager.main())
    except KeyboardInterrupt:
        print("Manager interrupted by user.")
    finally:
        loop.run_until_complete(manager.close())
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()
