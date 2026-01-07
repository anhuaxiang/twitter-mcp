import os
import httpx
import tweepy
from typing import Optional, Annotated

from mcp.server.fastmcp import FastMCP
from twitter_mcp.media import MediaManager

mcp = FastMCP("twitter-mcp")

access_token = os.environ["ACCESS_TOKEN"]


user_client = tweepy.Client(
    bearer_token=access_token
)
media_manager = MediaManager(bearer_token=access_token)


@mcp.tool(description="Get my X/Twitter user info")
def get_me() -> dict:
    user = user_client.get_me(user_auth=False)
    return user.data if hasattr(user, 'data') else user

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
    return tweet.data if hasattr(tweet, 'data') else tweet


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
    return tweet.data if hasattr(tweet, 'data') else tweet


@mcp.tool(description="Get home timeline tweets from X/Twitter with pagination support")
def get_home_timeline(
        max_results: Annotated[int, "Number of tweets to retrieve from timeline."] = 5,
        start_time: Optional[Annotated[str, "ISO 8601 start time for fetching tweets."]] = None,
        end_time: Optional[Annotated[str, "ISO 8601 end time for fetching tweets."]] = None,
        next_token: Optional[Annotated[str, "Token for pagination to get the next page of results."]] = None
) -> dict:
    tweets = user_client.get_home_timeline(
        max_results=max_results, start_time=start_time, end_time=end_time,
        user_auth=False, pagination_token=next_token,
        expansions=["author_id"],
        tweet_fields=["created_at", "reply_settings", "lang", "author_id"],
        user_fields=["username", "name", "id"]
    )

    # 构建结果，确保数据是字典格式
    result = {}

    # 处理推文数据
    if hasattr(tweets, 'data') and tweets.data:
        result["data"] = [tweet.data for tweet in tweets.data]

    # 处理 includes
    if hasattr(tweets, 'includes') and tweets.includes:
        includes = {}
        if "users" in tweets.includes:
            includes["users"] = [user.data if hasattr(user, 'data') else user for user in tweets.includes["users"]]
        if "media" in tweets.includes:
            includes["media"] = [media.data if hasattr(media, 'data') else media for media in tweets.includes["media"]]
        if "tweets" in tweets.includes:
            includes["tweets"] = [t.data if hasattr(t, 'data') else t for t in tweets.includes["tweets"]]
        if "polls" in tweets.includes:
            includes["polls"] = [poll.data if hasattr(poll, 'data') else poll for poll in tweets.includes["polls"]]
        result["includes"] = includes

    # 处理 meta
    if hasattr(tweets, 'meta') and tweets.meta:
        result["meta"] = tweets.meta

    return result


@mcp.tool(description="Like a tweet on X/Twitter")
def like_tweet(
        tweet_id: Annotated[str, "The ID of the tweet to like."]
) -> dict:
    response = user_client.like(tweet_id, user_auth=False)
    return response.data if hasattr(response, 'data') else response


@mcp.tool(description="Unlike a tweet on X/Twitter")
def unlike_tweet(
        tweet_id: Annotated[str, "The ID of the tweet to unlike."]
) -> dict:
    response = user_client.unlike(tweet_id, user_auth=False)
    return response.data if hasattr(response, 'data') else response


@mcp.tool(description="Retweet a tweet on X/Twitter")
def retweet_tweet(
        tweet_id: Annotated[str, "The ID of the tweet to retweet."]
) -> dict:
    response = user_client.retweet(tweet_id, user_auth=False)
    return response.data if hasattr(response, 'data') else response


@mcp.tool(description="Unretweet a tweet on X/Twitter")
def unretweet_tweet(
        tweet_id: Annotated[str, "The ID of the tweet to unretweet."]
) -> dict:
    response = user_client.unretweet(tweet_id, user_auth=False)
    return response.data if hasattr(response, 'data') else response


@mcp.tool(description="Get user info by username on X/Twitter")
def get_user_by_username(
        username: Annotated[str, "The username of the Twitter user."]
) -> dict:
    user = user_client.get_user(username=username, user_auth=False)
    return user.data if hasattr(user, 'data') else user


@mcp.tool(description="Get user info by user ID on X/Twitter")
def get_user_by_id(
        user_id: Annotated[str, "The user ID of the Twitter user."]
) -> dict:
    user = user_client.get_user(id=user_id, user_auth=False)
    return user.data if hasattr(user, 'data') else user


@mcp.tool(description="Search recent tweets on X/Twitter with pagination support")
def search_tweets(
        query: Annotated[str, "The search query string."],
        start_time: Optional[Annotated[str, "ISO 8601 start time for fetching tweets."]] = None,
        end_time: Optional[Annotated[str, "ISO 8601 end time for fetching tweets."]] = None,
        max_results: Annotated[int, "Maximum number of tweets to return."] = 10,
        next_token: Optional[Annotated[str, "Token for pagination to get the next page of results."]] = None
) -> dict:
    tweets = user_client.search_recent_tweets(
        query=query,
        max_results=max_results,
        user_auth=False,
        start_time=start_time,
        end_time=end_time,
        next_token=next_token,
        expansions=["author_id"],
        tweet_fields=["created_at", "reply_settings", "lang", "author_id"],
        user_fields=["username", "name", "id"]
    )

    # 构建结果，确保数据是字典格式
    result = {}

    # 处理推文数据
    if hasattr(tweets, 'data') and tweets.data:
        result["data"] = [tweet.data for tweet in tweets.data]

    # 处理 includes
    if hasattr(tweets, 'includes') and tweets.includes:
        includes = {}
        if "users" in tweets.includes:
            includes["users"] = [user.data if hasattr(user, 'data') else user for user in tweets.includes["users"]]
        if "media" in tweets.includes:
            includes["media"] = [media.data if hasattr(media, 'data') else media for media in tweets.includes["media"]]
        if "tweets" in tweets.includes:
            includes["tweets"] = [t.data if hasattr(t, 'data') else t for t in tweets.includes["tweets"]]
        if "polls" in tweets.includes:
            includes["polls"] = [poll.data if hasattr(poll, 'data') else poll for poll in tweets.includes["polls"]]
        result["includes"] = includes

    # 处理 meta
    if hasattr(tweets, 'meta') and tweets.meta:
        result["meta"] = tweets.meta

    return result


@mcp.tool(description="Get latest tweets from a user on X/Twitter with pagination support")
def get_lasest_tweets_from_user(
        user_id: Annotated[str, "The user ID of the Twitter user."],
        max_results: Annotated[int, "Maximum number of tweets to return."] = 5,
        next_token: Optional[Annotated[str, "Token for pagination to get the next page of results."]] = None
) -> dict:
    tweets = user_client.get_users_tweets(
        id=user_id, max_results=max_results, user_auth=False,
        pagination_token=next_token,
        expansions=["author_id"],
        tweet_fields=["created_at", "reply_settings", "lang", "author_id"],
        user_fields=["username", "name", "id"]
    )

    # 构建结果，确保数据是字典格式
    result = {}

    # 处理推文数据
    if hasattr(tweets, 'data') and tweets.data:
        result["data"] = [tweet.data for tweet in tweets.data]

    # 处理 includes
    if hasattr(tweets, 'includes') and tweets.includes:
        includes = {}
        if "users" in tweets.includes:
            includes["users"] = [user.data if hasattr(user, 'data') else user for user in tweets.includes["users"]]
        if "media" in tweets.includes:
            includes["media"] = [media.data if hasattr(media, 'data') else media for media in tweets.includes["media"]]
        if "tweets" in tweets.includes:
            includes["tweets"] = [t.data if hasattr(t, 'data') else t for t in tweets.includes["tweets"]]
        if "polls" in tweets.includes:
            includes["polls"] = [poll.data if hasattr(poll, 'data') else poll for poll in tweets.includes["polls"]]
        result["includes"] = includes

    # 处理 meta
    if hasattr(tweets, 'meta') and tweets.meta:
        result["meta"] = tweets.meta

    return result


@mcp.tool(description="Delete a tweet on X/Twitter")
def delete_tweet(
        tweet_id: Annotated[str, "The ID of the tweet to delete."]
) -> dict:
    response = user_client.delete_tweet(tweet_id, user_auth=False)
    return response.data if hasattr(response, 'data') else response


@mcp.tool(description="Get tweet by ID on X/Twitter with full details")
def get_tweet_by_id(
        tweet_id: Annotated[str, "The ID of the tweet to retrieve."]
) -> dict:
    tweet = user_client.get_tweet(
        tweet_id,
        user_auth=False,
        expansions=[
            "author_id",
            "referenced_tweets.id",
            "attachments.media_keys",
            "in_reply_to_user_id",
            "edit_history_tweet_ids"
        ],
        tweet_fields=[
            "created_at",
            "public_metrics",
            "source",
            "reply_settings",
            "lang",
            "entities",
            "author_id",
            "text",
            "conversation_id",
            "geo"
        ],
        user_fields=["username", "name", "id", "verified", "public_metrics"],
        media_fields=["type", "url", "preview_image_url", "duration_ms", "height", "width"],
        poll_fields=["voting_status", "end_datetime", "duration_minutes"]
    )

    # 构建结果，确保数据是字典格式
    result = {}

    # 处理推文数据
    if hasattr(tweet, 'data') and tweet.data:
        result["data"] = tweet.data

    # 处理 includes
    if hasattr(tweet, 'includes') and tweet.includes:
        includes = {}
        if "users" in tweet.includes:
            includes["users"] = [user.data if hasattr(user, 'data') else user for user in tweet.includes["users"]]
        if "media" in tweet.includes:
            includes["media"] = [media.data if hasattr(media, 'data') else media for media in tweet.includes["media"]]
        if "tweets" in tweet.includes:
            includes["tweets"] = [t.data if hasattr(t, 'data') else t for t in tweet.includes["tweets"]]
        if "polls" in tweet.includes:
            includes["polls"] = [poll.data if hasattr(poll, 'data') else poll for poll in tweet.includes["polls"]]
        result["includes"] = includes

    # 处理 meta
    if hasattr(tweet, 'meta') and tweet.meta:
        result["meta"] = tweet.meta

    return result



@mcp.tool(description="Follow a user on X/Twitter")
def follow_user(
        user_id: Annotated[str, "The user ID of the Twitter user to follow."]
) -> dict:
    response = user_client.follow_user(user_id, user_auth=False)
    return response.data if hasattr(response, 'data') else response


@mcp.tool(description="Unfollow a user on X/Twitter")
def unfollow_user(
        user_id: Annotated[str, "The user ID of the Twitter user to unfollow."]
) -> dict:
    response = user_client.unfollow_user(user_id, user_auth=False)
    return response.data if hasattr(response, 'data') else response


@mcp.tool(description="Get followers of a user on X/Twitter")
def get_followers(
        user_id: Annotated[str, "The user ID of the Twitter user."],
        max_results: Annotated[int, "Maximum number of followers to return."] = 10,
) -> dict:
    followers = user_client.get_users_followers(
        id=user_id, max_results=max_results, user_auth=False
    )
    # 构建结果，确保数据是字典格式
    result = {}
    if hasattr(followers, 'data') and followers.data:
        result["data"] = [user.data for user in followers.data]
    if hasattr(followers, 'meta') and followers.meta:
        result["meta"] = followers.meta
    return result


@mcp.tool(description="Get following of a user on X/Twitter")
def get_following(
        user_id: Annotated[str, "The user ID of the Twitter user."],
        max_results: Annotated[int, "Maximum number of following to return."] = 10,
) -> dict:
    following = user_client.get_users_following(
        id=user_id, max_results=max_results, user_auth=False
    )
    # 构建结果，确保数据是字典格式
    result = {}
    if hasattr(following, 'data') and following.data:
        result["data"] = [user.data for user in following.data]
    if hasattr(following, 'meta') and following.meta:
        result["meta"] = following.meta
    return result


@mcp.tool(description="Search all tweets on X/Twitter")
def search_all_twitter(
        query: Annotated[str, "The search query string."],
        max_results: Annotated[int, "Maximum number of tweets to return."] = 10,
) -> dict:
    tweets = user_client.search_all_tweets(
        query=query, max_results=max_results, user_auth=False
    )
    # 构建结果，确保数据是字典格式
    result = {}
    if hasattr(tweets, 'data') and tweets.data:
        result["data"] = [tweet.data for tweet in tweets.data]
    if hasattr(tweets, 'meta') and tweets.meta:
        result["meta"] = tweets.meta
    return result



def main():
    mcp.run()


if __name__ == '__main__':
    main()
