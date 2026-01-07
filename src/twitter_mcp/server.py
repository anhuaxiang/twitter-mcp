import os
import httpx
import tweepy
from typing import Optional, Annotated

from mcp.server.fastmcp import FastMCP
from .media import MediaManager

mcp = FastMCP("twitter-mcp")

access_token = os.environ["ACCESS_TOKEN"]


user_client = tweepy.Client(
    bearer_token=access_token
)
media_manager = MediaManager(bearer_token=access_token)


@mcp.tool(description="Get my X/Twitter user info")
def get_me() -> dict:
    user = user_client.get_me(user_auth=False)
    return user.data.data


@mcp.tool(description="Create new X/Twitter post")
async def post_twitter(
        post: Annotated[str, "The content of the Twitter post to be created."],
        media_url: Optional[Annotated[str, "URL of media to attach to the post."]] = None
) -> dict:
    if media_url:
        # 从URL下载媒体
        async with httpx.AsyncClient() as client:
            response = await client.get(media_url)
            response.raise_for_status()
            media_data = response.content
            content_type = response.headers.get('content-type', 'image/jpeg')

        # 使用MediaManager上传媒体
        media_id = media_manager.upload_media_from_bytes(
            media_data=media_data,
            media_type=content_type
        )
        # 创建带媒体的推文
        tweet = user_client.create_tweet(text=post, media_ids=[media_id], user_auth=False)
    else:
        # 创建纯文本推文
        tweet = user_client.create_tweet(text=post, user_auth=False)
    return tweet.data


@mcp.tool(description="Reply to an existing X/Twitter post")
async def reply_twitter(
        post: Annotated[str, "The content of the reply post."],
        tweet_id: Annotated[str, "The ID of the tweet to reply to."]
) -> dict:
    tweet = user_client.create_tweet(
        text=post,
        quote_tweet_id=tweet_id,
        in_reply_to_tweet_id=tweet_id,
        user_auth=False
    )
    return tweet.data


@mcp.tool(description="Get recent tweets from my X/Twitter timeline")
def get_timeline(
        count: Annotated[int, "Number of tweets to retrieve from timeline."] = 5,
        start_time: Optional[Annotated[str, "ISO 8601 start time for fetching tweets."]] = None,
        end_time: Optional[Annotated[str, "ISO 8601 end time for fetching tweets."]] = None
):
    tweets = user_client.get_home_timeline(
        max_results=count, start_time=start_time, end_time=end_time,
        user_auth=False
    )
    return [tweet.data for tweet in tweets.data]


@mcp.tool(description="Like a tweet on X/Twitter")
def like_tweet(
        tweet_id: Annotated[str, "The ID of the tweet to like."]
) -> dict:
    response = user_client.like(tweet_id, user_auth=False)
    return response.data


@mcp.tool(description="Unlike a tweet on X/Twitter")
def unlike_tweet(
        tweet_id: Annotated[str, "The ID of the tweet to unlike."]
) -> dict:
    response = user_client.unlike(tweet_id, user_auth=False)
    return response.data


@mcp.tool(description="Retweet a tweet on X/Twitter")
def retweet_tweet(
        tweet_id: Annotated[str, "The ID of the tweet to retweet."]
) -> dict:
    response = user_client.retweet(tweet_id, user_auth=False)
    return response.data


@mcp.tool(description="Unretweet a tweet on X/Twitter")
def unretweet_tweet(
        tweet_id: Annotated[str, "The ID of the tweet to unretweet."]
) -> dict:
    response = user_client.unretweet(tweet_id, user_auth=False)
    return response.data


@mcp.tool(description="Get user info by username on X/Twitter")
def get_user_by_username(
        username: Annotated[str, "The username of the Twitter user."]
) -> dict:
    user = user_client.get_user(username=username, user_auth=False)
    return user.data.data


@mcp.tool(description="Get user info by user ID on X/Twitter")
def get_user_by_id(
        user_id: Annotated[str, "The user ID of the Twitter user."]
) -> dict:
    user = user_client.get_user(id=user_id, user_auth=False)
    return user.data.data


@mcp.tool(description="Search recent tweets on X/Twitter")
def search_tweets(
        query: Annotated[str, "The search query string."],
        max_results: Annotated[int, "Maximum number of tweets to return."] = 10
) -> list:
    tweets = user_client.search_recent_tweets(query=query, max_results=max_results, user_auth=False)
    return [tweet.data for tweet in tweets.data]


@mcp.tool(description="Get latest tweets from a user on X/Twitter")
def get_lasest_tweets_from_user(
        user_id: Annotated[str, "The user ID of the Twitter user."],
        max_results: Annotated[int, "Maximum number of tweets to return."] = 5
) -> list:
    tweets = user_client.get_users_tweets(
        id=user_id, max_results=max_results, user_auth=False
    )
    return [tweet.data for tweet in tweets.data]


@mcp.tool(description="Delete a tweet on X/Twitter")
def delete_tweet(
        tweet_id: Annotated[str, "The ID of the tweet to delete."]
) -> dict:
    response = user_client.delete_tweet(tweet_id, user_auth=False)
    return response.data


@mcp.tool(description="Get tweet by ID on X/Twitter")
def get_tweet_by_id(
        tweet_id: Annotated[str, "The ID of the tweet to retrieve."]
) -> dict:
    tweet = user_client.get_tweet(tweet_id, user_auth=False)
    return tweet.data


@mcp.tool(description="Follow a user on X/Twitter")
def follow_user(
        user_id: Annotated[str, "The user ID of the Twitter user to follow."]
) -> dict:
    response = user_client.follow_user(user_id, user_auth=False)
    return response.data


@mcp.tool(description="Unfollow a user on X/Twitter")
def unfollow_user(
        user_id: Annotated[str, "The user ID of the Twitter user to unfollow."]
) -> dict:
    response = user_client.unfollow_user(user_id, user_auth=False)
    return response.data


@mcp.tool(description="Get followers of a user on X/Twitter")
def get_followers(
        user_id: Annotated[str, "The user ID of the Twitter user."],
        max_results: Annotated[int, "Maximum number of followers to return."] = 10,
) -> list:
    followers = user_client.get_users_followers(
        id=user_id, max_results=max_results, user_auth=False
    )
    return [follower.data for follower in followers.data]


@mcp.tool(description="Get following of a user on X/Twitter")
def get_following(
        user_id: Annotated[str, "The user ID of the Twitter user."],
        max_results: Annotated[int, "Maximum number of following to return."] = 10,
) -> list:
    following = user_client.get_users_following(
        id=user_id, max_results=max_results, user_auth=False
    )
    return [followed.data for followed in following.data]


@mcp.tool(description="Search all tweets on X/Twitter")
def search_all_twitter(
        query: Annotated[str, "The search query string."],
        max_results: Annotated[int, "Maximum number of tweets to return."] = 10,
) -> list:
    tweets = user_client.search_all_tweets(
        query=query, max_results=max_results, user_auth=False
    )
    return [tweet.data for tweet in tweets.data]



def main():
    mcp.run()


if __name__ == '__main__':
    main()
