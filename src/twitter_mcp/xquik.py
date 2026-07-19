import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


XQUIK_BASE_URL = "https://xquik.com"
XQUIK_TIMEOUT_SECONDS = 30


def has_twitter_credentials() -> bool:
    return all(
        os.getenv(name)
        for name in (
            "CONSUMER_KEY",
            "CONSUMER_SECRET",
            "ACCESS_TOKEN",
            "ACCESS_TOKEN_SECRET",
        )
    )


def xquik_enabled() -> bool:
    backend = os.getenv("TWITTER_MCP_READ_BACKEND", "").lower()
    return backend == "xquik" or bool(
        os.getenv("XQUIK_API_KEY") and not has_twitter_credentials()
    )


def _timeout_seconds() -> float:
    raw_timeout = os.getenv("XQUIK_TIMEOUT_SECONDS")
    if not raw_timeout:
        return XQUIK_TIMEOUT_SECONDS
    try:
        return max(float(raw_timeout), 1.0)
    except ValueError:
        return XQUIK_TIMEOUT_SECONDS


def _request_json(path: str, query: dict[str, str | int] | None = None) -> Any:
    api_key = os.getenv("XQUIK_API_KEY")
    if not api_key:
        raise RuntimeError("XQUIK_API_KEY is required for the Xquik read backend")

    encoded_query = urllib.parse.urlencode(query or {})
    suffix = f"?{encoded_query}" if encoded_query else ""
    base_url = os.getenv("XQUIK_BASE_URL", XQUIK_BASE_URL).rstrip("/")
    request = urllib.request.Request(
        f"{base_url}{path}{suffix}",
        headers={"Accept": "application/json", "x-api-key": api_key},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=_timeout_seconds()) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read(500).decode("utf-8", errors="replace")
        raise RuntimeError(f"Xquik request failed: HTTP {exc.code} {details}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Xquik request failed: {exc.reason}") from exc


def _items(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("tweets", "data", "results", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def _first_text(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value:
            return value
        if isinstance(value, (int, float)):
            return str(value)
    return None


def _first_value(*values: Any) -> Any:
    return next((value for value in values if value is not None), None)


def _author(tweet: dict[str, Any]) -> dict[str, Any]:
    for key in ("author", "user", "account"):
        value = tweet.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _metrics(tweet: dict[str, Any]) -> dict[str, Any]:
    public_metrics = tweet.get("public_metrics")
    if isinstance(public_metrics, dict):
        return public_metrics
    return {
        "retweet_count": _first_value(
            tweet.get("retweetCount"), tweet.get("retweet_count"), tweet.get("retweets")
        ),
        "reply_count": _first_value(
            tweet.get("replyCount"), tweet.get("reply_count"), tweet.get("replies")
        ),
        "like_count": _first_value(
            tweet.get("likeCount"), tweet.get("like_count"), tweet.get("likes")
        ),
        "quote_count": _first_value(
            tweet.get("quoteCount"), tweet.get("quote_count"), tweet.get("quotes")
        ),
    }


def normalize_tweet(tweet: Any) -> dict[str, Any]:
    if not isinstance(tweet, dict):
        return {"text": str(tweet)}

    author = _author(tweet)
    tweet_id = _first_text(tweet.get("id"), tweet.get("tweet_id"))
    username = _first_text(
        author.get("username"),
        author.get("screen_name"),
        tweet.get("username"),
        tweet.get("handle"),
    )
    url = _first_text(tweet.get("url"), tweet.get("tweetUrl"))
    if not url and tweet_id and username:
        url = f"https://x.com/{username.lstrip('@')}/status/{tweet_id}"

    result: dict[str, Any] = {
        "id": tweet_id,
        "text": _first_text(tweet.get("text"), tweet.get("full_text")),
        "created_at": _first_text(tweet.get("createdAt"), tweet.get("created_at")),
        "url": url,
        "public_metrics": _metrics(tweet),
    }
    if username:
        result["author"] = {
            "username": username.lstrip("@"),
            "name": _first_text(author.get("name"), author.get("display_name")),
            "id": _first_text(author.get("id"), author.get("user_id")),
        }
    return {key: value for key, value in result.items() if value is not None}


def search_xquik_tweets(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    payload = _request_json(
        "/api/v1/x/tweets/search",
        {"q": query, "queryType": "Latest", "limit": max_results},
    )
    return [normalize_tweet(tweet) for tweet in _items(payload)[:max_results]]


def get_xquik_tweet(tweet_id: str) -> dict[str, Any]:
    payload = _request_json(f"/api/v1/x/tweets/{urllib.parse.quote(tweet_id, safe='')}")
    if not isinstance(payload, dict):
        return normalize_tweet(payload)
    tweet = payload.get("tweet") or payload.get("data") or payload
    if isinstance(tweet, dict) and isinstance(payload.get("author"), dict):
        tweet = {**tweet, "author": payload["author"]}
    return normalize_tweet(tweet)


def get_xquik_user_tweets(username: str, max_results: int = 5) -> list[dict[str, Any]]:
    handle = username.lstrip("@")
    return search_xquik_tweets(f"from:{handle}", max_results)
