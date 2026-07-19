import unittest
from types import SimpleNamespace
from unittest.mock import patch

from twitter_mcp import server


class FakeTweetClient:
    def __init__(self) -> None:
        self.create_tweet_calls: list[dict[str, str]] = []

    def create_tweet(self, **kwargs: str) -> SimpleNamespace:
        self.create_tweet_calls.append(kwargs)
        return SimpleNamespace(data={"id": "reply-id"})


class ReplyTwitterTest(unittest.IsolatedAsyncioTestCase):
    async def test_reply_does_not_quote_the_target_tweet(self) -> None:
        client = FakeTweetClient()

        with patch.object(server, "_twitter_clients", return_value=(None, client)):
            result = await server.reply_twitter("Thanks", "target-id")

        self.assertEqual(result, {"id": "reply-id"})
        self.assertEqual(
            client.create_tweet_calls,
            [{"text": "Thanks", "in_reply_to_tweet_id": "target-id"}],
        )


if __name__ == "__main__":
    unittest.main()
