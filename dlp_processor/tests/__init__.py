import json
import os
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from manager import Manager


class TestManager(IsolatedAsyncioTestCase):
    def setUp(self):
        patcher = patch.dict(
            os.environ, {"RABBITMQ_USER": "user", "RABBITMQ_PASSWORD": "pass"}
        )
        self.addCleanup(patcher.stop)
        patcher.start()

        # Sample tasks with AsyncMock to simulate asynchronous behavior
        self.sample_tasks = {
            "say": AsyncMock(),
        }

    @patch("aio_pika.connect_robust")
    async def test_connect(self, mock_aio_pika_connect):
        # Arrange
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_queue = AsyncMock()

        mock_aio_pika_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_queue.return_value = mock_queue

        manager = Manager(queue_name="test_queue", tasks=self.sample_tasks)

        # Act
        await manager._connect()

        # Assert
        mock_aio_pika_connect.assert_awaited_once_with(
            host="rabbitmq",
            login="user",
            password="pass",
            loop=manager.loop,
        )
        mock_connection.channel.assert_awaited_once()
        mock_channel.set_qos.assert_awaited_once_with(prefetch_count=1)
        mock_channel.declare_queue.assert_awaited_once_with("test_queue", durable=True)

        self.assertEqual(manager.connection, mock_connection)
        self.assertEqual(manager.channel, mock_channel)
        self.assertEqual(manager.queue, mock_queue)

    @patch("aio_pika.connect_robust")
    async def test_get_messages(self, mock_aio_pika_connect):
        # Arrange
        mock_queue = AsyncMock()
        mock_message = AsyncMock()
        mock_message.body.decode.return_value = json.dumps(
            {"task": "say", "args": ["Hello"], "kwargs": {}}
        )
        mock_queue.get.return_value = mock_message

        manager = Manager(queue_name="test_queue", tasks=self.sample_tasks)
        manager.connection = AsyncMock()
        manager.connection.is_closed = False
        manager.queue = mock_queue

        # Act
        messages = await manager._get_messages()

        # Assert
        mock_queue.get.assert_awaited_once_with(fail=False, timeout=5)
        self.assertEqual(messages, [mock_message])

    @patch("aio_pika.connect_robust")
    async def test_close(self, mock_aio_pika_connect):
        # Arrange
        mock_connection = AsyncMock()
        mock_connection.is_closed = False
        manager = Manager(queue_name="test_queue", tasks=self.sample_tasks)
        manager.connection = mock_connection

        # Act
        await manager.close()

        # Assert
        mock_connection.close.assert_awaited_once()
