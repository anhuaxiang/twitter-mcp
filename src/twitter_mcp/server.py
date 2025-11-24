import os
import io
import httpx
import tweepy
from typing import Optional, Annotated
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("twitter-mcp")


CONSUMER_KEY = os.environ["CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["CONSUMER_SECRET"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = os.environ["ACCESS_TOKEN_SECRET"]


auth = tweepy.OAuth1UserHandler(
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)
v1_api = tweepy.API(auth)


tweet_client = tweepy.Client(
    consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET,
    access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET
)


@mcp.tool(description="Get my X/Twitter user info")
def get_me() -> dict:
    user = tweet_client.get_me()
    return user.data.data


@mcp.tool(description="Create new X/Twitter post")
async def post_twitter(
        post: Annotated[str, "The content of the Twitter post to be created."],
        media_url: Optional[Annotated[str, "URL of media to attach to the post."]] = None
) -> dict:
    if media_url:
        async with httpx.AsyncClient() as client:
            response = await client.get(media_url)
            response.raise_for_status()
            media_data = io.BytesIO(response.content)
        media = v1_api.media_upload(filename="media", file=media_data)
        tweet = tweet_client.create_tweet(text=post, media_ids=[media.media_id_string])
    else:
        tweet = tweet_client.create_tweet(text=post)
    return tweet.data


@mcp.tool(description="Reply to an existing X/Twitter post")
async def reply_twitter(
        post: Annotated[str, "The content of the reply post."],
        tweet_id: Annotated[str, "The ID of the tweet to reply to."]
) -> dict:
    tweet = tweet_client.create_tweet(
        text=post,
        quote_tweet_id=tweet_id,
        in_reply_to_tweet_id=tweet_id
    )
    return tweet.data


@mcp.tool(description="Get recent tweets from my X/Twitter timeline")
def get_timeline(
        count: Annotated[int, "Number of tweets to retrieve from timeline."] = 5,
        start_time: Optional[Annotated[str, "ISO 8601 start time for fetching tweets."]] = None,
        end_time: Optional[Annotated[str, "ISO 8601 end time for fetching tweets."]] = None
):
    tweets = tweet_client.get_home_timeline(
        max_results=count, start_time=start_time, end_time=end_time
    )
    return [tweet.data for tweet in tweets.data]


@mcp.tool(description="Like a tweet on X/Twitter")
def like_tweet(
        tweet_id: Annotated[str, "The ID of the tweet to like."]
) -> dict:
    response = tweet_client.like(tweet_id)
    return response.data


@mcp.tool(description="Unlike a tweet on X/Twitter")
def unlike_tweet(
        tweet_id: Annotated[str, "The ID of the tweet to unlike."]
) -> dict:
    response = tweet_client.unlike(tweet_id)
    return response.data


@mcp.tool(description="Retweet a tweet on X/Twitter")
def retweet_tweet(
        tweet_id: Annotated[str, "The ID of the tweet to retweet."]
) -> dict:
    response = tweet_client.retweet(tweet_id)
    return response.data


@mcp.tool(description="Unretweet a tweet on X/Twitter")
def unretweet_tweet(
        tweet_id: Annotated[str, "The ID of the tweet to unretweet."]
) -> dict:
    response = tweet_client.unretweet(tweet_id)
    return response.data


@mcp.tool(description="Get user info by username on X/Twitter")
def get_user_by_username(
        username: Annotated[str, "The username of the Twitter user."]
) -> dict:
    user = tweet_client.get_user(username=username)
    return user.data.data


@mcp.tool(description="Get user info by user ID on X/Twitter")
def get_user_by_id(
        user_id: Annotated[str, "The user ID of the Twitter user."]
) -> dict:
    user = tweet_client.get_user(id=user_id)
    return user.data.data


@mcp.tool(description="Search recent tweets on X/Twitter")
def search_tweets(
        query: Annotated[str, "The search query string."],
        max_results: Annotated[int, "Maximum number of tweets to return."] = 10
) -> list:
    tweets = tweet_client.search_recent_tweets(query=query, max_results=max_results)
    return [tweet.data for tweet in tweets.data]


@mcp.tool(description="Get latest tweets from a user on X/Twitter")
def get_lasest_tweets_from_user(
        username: Annotated[str, "The username of the Twitter user."],
        max_results: Annotated[int, "Maximum number of tweets to return."] = 5
) -> list:
    user = tweet_client.get_user(username=username)
    tweets = tweet_client.get_users_tweets(
        id=user.data.id, max_results=max_results
    )
    return [tweet.data for tweet in tweets.data]


def main():
    mcp.run()


if __name__ == '__main__':
    main()
