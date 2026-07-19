import unittest
from unittest.mock import patch

from twitter_mcp import xquik


class XquikBackendTest(unittest.TestCase):
    def test_search_builds_request_and_normalizes_current_response(self) -> None:
        payload = {
            "tweets": [
                {
                    "id": "42",
                    "text": "Useful result",
                    "createdAt": "2026-07-19T12:00:00Z",
                    "author": {"id": "7", "username": "@analyst"},
                    "likeCount": 3,
                    "retweetCount": 0,
                }
            ]
        }

        with patch.object(xquik, "_request_json", return_value=payload) as request:
            result = xquik.search_xquik_tweets("release", 5)

        request.assert_called_once_with(
            "/api/v1/x/tweets/search",
            {"q": "release", "queryType": "Latest", "limit": 5},
        )
        self.assertEqual(result[0]["id"], "42")
        self.assertEqual(result[0]["author"]["username"], "analyst")
        self.assertEqual(result[0]["public_metrics"]["like_count"], 3)
        self.assertEqual(result[0]["public_metrics"]["retweet_count"], 0)
        self.assertEqual(result[0]["created_at"], "2026-07-19T12:00:00Z")
        self.assertEqual(result[0]["url"], "https://x.com/analyst/status/42")

    def test_lookup_combines_top_level_author(self) -> None:
        payload = {
            "tweet": {"id": "42", "text": "Useful result"},
            "author": {"id": "7", "username": "analyst"},
        }

        with patch.object(xquik, "_request_json", return_value=payload):
            result = xquik.get_xquik_tweet("42")

        self.assertEqual(result["author"]["id"], "7")
        self.assertEqual(result["url"], "https://x.com/analyst/status/42")

    def test_request_uses_api_key_header(self) -> None:
        response = unittest.mock.MagicMock()
        response.read.return_value = b'{"tweets": []}'
        response.__enter__.return_value = response

        with (
            patch.dict("os.environ", {"XQUIK_API_KEY": "key"}, clear=True),
            patch.object(
                xquik.urllib.request, "urlopen", return_value=response
            ) as open_url,
        ):
            xquik.search_xquik_tweets("release")

        request = open_url.call_args.args[0]
        self.assertEqual(request.get_header("X-api-key"), "key")
        self.assertNotIn("Authorization", request.headers)


if __name__ == "__main__":
    unittest.main()
