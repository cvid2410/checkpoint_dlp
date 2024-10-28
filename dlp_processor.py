import asyncio
import json


class Manager:

    def __init__(self, queue_name: str, tasks: dict):
        self.loop = asyncio.get_event_loop()
        self.queue = queue_name
        self.tasks = tasks

    async def _get_messages(self):
        """Read and pop messages from SQS queue"""
        raise NotImplementedError

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
            for message in messages:
                body = json.loads(message["Body"])

                task_name = body.get("task")
                args = body.get("args", ())
                kwargs = body.get("kwargs", {})

                task = self.tasks.get(task_name)
                self.loop.create_task(task(*args, **kwargs))
            await asyncio.sleep(1)
