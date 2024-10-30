import asyncio
import logging

from manager import Manager
from tasks import scan_message_task

logger = logging.getLogger(__name__)

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
