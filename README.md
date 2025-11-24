# Twitter MCP

This MCP (Modular Connector Plugin) allows interaction with Twitter, enabling actions such as posting tweets, reading timelines, and managing followers.
It supports authentication via both Twitter Scraper and Twitter API.

## usage
```
{
  "mcpServers": {
    "twitter-mcp": {
      "env": {
        "CONSUMER_KEY": "CONSUMER_KEY",
        "CONSUMER_SECRET": "CONSUMER_SECRET",
        "ACCESS_TOKEN": "ACCESS_TOKEN",
        "ACCESS_TOKEN_SECRET": ACCESS_TOKEN_SECRET
      },
      "command": "uvx",
      "args": [
        "twitter-mc"
      ]
    }
  }
}
```