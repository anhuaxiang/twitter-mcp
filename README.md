# Twitter MCP

This MCP (Modular Connector Plugin) allows interaction with Twitter, enabling actions such as posting tweets, reading timelines, and managing followers.
It supports authentication via both Twitter Scraper and Twitter API.

## Optional Xquik read backend

By default, read and write tools continue to use the configured Twitter API
credentials. For read-only tweet search and tweet lookup, you can route through
Xquik instead:

```
TWITTER_MCP_READ_BACKEND=xquik
XQUIK_API_KEY=your_key
```

When no Twitter API credentials are configured and `XQUIK_API_KEY` is present,
read tools use Xquik automatically. This applies to tweet search, tweet lookup,
and user timeline tools. Posting, liking, retweeting, follower lists, and
authenticated timeline tools still require the Twitter API credentials.

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.

## usage
```
{
  "mcpServers": {
    "twitter-mcp": {
      "env": {
        "CONSUMER_KEY": "CONSUMER_KEY",
        "CONSUMER_SECRET": "CONSUMER_SECRET",
        "ACCESS_TOKEN": "ACCESS_TOKEN",
        "ACCESS_TOKEN_SECRET": "ACCESS_TOKEN_SECRET",
        "TWITTER_MCP_READ_BACKEND": "xquik",
        "XQUIK_API_KEY": "your_key"
      },
      "command": "uvx",
      "args": [
        "twitter-mcp"
      ]
    }
  }
}
```
