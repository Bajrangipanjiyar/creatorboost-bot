# -*- coding: utf-8 -*-
"""
YouTube Data API v3 Async Service (API Key Only - No OAuth)
Handles channel resolution, code verification, video metadata, and public subscription checks.
Includes TTL caching to preserve YouTube API quota limits.

================================================================================
CRITICAL ARCHITECTURAL NOTE: YOUTUBE API LIMITATIONS (API KEY ONLY)
================================================================================
YouTube Data API v3 with an API key operates in a read-only server-to-server context:
1. WHAT WE CAN VERIFY:
   - Channel existence, title, subscriber counts, and description text.
   - Code presence in channel description (proving 100% channel ownership without OAuth).
   - Video metadata (validity, title, duration, author, thumbnail).
   - Public subscriptions via `subscriptions.list(channelId=..., forChannelId=...)`.

2. WHAT THE YOUTUBE API CANNOT VERIFY WITHOUT OAUTH:
   - User Likes: YouTube DOES NOT offer any endpoint to check if a specific viewer
     liked a video without that viewer logging in via Google OAuth.
   - User Comments: Checking comments by author requires searching thousands of comments
     which burns excessive quota (100 units per search).
   - Actual Watch Time: YouTube provides no telemetry to external bots about watch completion.

3. OUR PRODUCTION HYBRID VERIFICATION APPROACH:
   - Ownership: Proven by pasting dynamic verification code `CB-XXXXX` in channel description.
   - Watch Tasks: Enforced by client/server async countdown timers with confirmation locks.
   - Like / Comment Tasks: Timer delay + optional screenshot proof reviewed by admins or sampled.
   - Subscribe Tasks: Checked via public subscriptions API, or fallback to screenshot proof.
================================================================================
"""

import re
import urllib.parse
from typing import Optional, Dict, Any, Tuple
import aiohttp
from cachetools import TTLCache
from config import settings
from utils.logger import logger

# In-memory TTL caches to avoid wasting 10,000 daily API quota units
# 5 minutes TTL for channels, 10 minutes for videos
channel_cache = TTLCache(maxsize=500, ttl=300)
video_cache = TTLCache(maxsize=1000, ttl=600)

class YouTubeAPIError(Exception):
    """Base YouTube service exception."""
    pass

class YouTubeQuotaExceededError(YouTubeAPIError):
    """Raised when the 10,000 daily unit API quota has been reached."""
    pass

class YouTubeService:
    BASE_URL = "https://www.googleapis.com/youtube/v3"

    @classmethod
    async def _make_request(cls, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executes an async GET request to YouTube API with strict error and quota inspection."""
        params["key"] = settings.YOUTUBE_API_KEY
        url = f"{cls.BASE_URL}/{endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as resp:
                    data = await resp.json()
                    
                    if resp.status == 200:
                        return data

                    # Handle Quota and Permission Errors
                    error_info = data.get("error", {})
                    errors = error_info.get("errors", [])
                    reason = errors[0].get("reason") if errors else ""
                    message = error_info.get("message", "Unknown YouTube API error")

                    if resp.status == 403 and reason in ("quotaExceeded", "rateLimitExceeded"):
                        logger.error(f"YouTube API Quota Exceeded: {message}")
                        raise YouTubeQuotaExceededError(
                            "YouTube API daily quota is currently exhausted. Please try again tomorrow or contact admin."
                        )

                    logger.warning(f"YouTube API Error [{resp.status}]: {message}")
                    raise YouTubeAPIError(f"YouTube Error: {message}")

        except aiohttp.ClientError as e:
            logger.error(f"Network error connecting to YouTube API: {e}")
            raise YouTubeAPIError("Could not connect to YouTube. Please check network connection.")

    @classmethod
    def extract_channel_identifier(cls, user_input: str) -> Tuple[str, str]:
        """
        Parses various YouTube channel input formats.
        Returns tuple: (type, clean_value) where type is 'id', 'handle', or 'search'.
        """
        user_input = user_input.strip()

        # Handle format: @handle or https://youtube.com/@handle
        handle_match = re.search(r"@([a-zA-Z0-9_\-\.]{3,30})", user_input)
        if handle_match:
            return "handle", handle_match.group(1)

        # Handle channel ID format: UC...
        id_match = re.search(r"(UC[a-zA-Z0-9_\-]{22})", user_input)
        if id_match:
            return "id", id_match.group(1)

        # Fallback to search term if user pasted just a name
        clean_name = re.sub(r"https?://(www\.)?youtube\.com/", "", user_input).strip("/")
        return "search", clean_name

    @classmethod
    async def resolve_channel(cls, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Resolves any channel link or handle to full channel details.
        Returns dictionary with id, title, description, custom_url, subscribers, videos.
        """
        id_type, value = cls.extract_channel_identifier(user_input)

        cache_key = f"ch_{id_type}_{value}"
        if cache_key in channel_cache:
            return channel_cache[cache_key]

        data = None
        if id_type == "id":
            params = {"part": "snippet,statistics", "id": value}
            data = await cls._make_request("channels", params)

        elif id_type == "handle":
            # YouTube API v3 supports forHandle query
            params = {"part": "snippet,statistics", "forHandle": value}
            try:
                data = await cls._make_request("channels", params)
            except YouTubeAPIError:
                # Fallback to search query if forHandle fails on older handles
                data = None

        if not data or not data.get("items"):
            # Fallback to search API (costs 100 units, used only when direct lookup fails)
            search_params = {"part": "snippet", "q": value, "type": "channel", "maxResults": 1}
            search_data = await cls._make_request("search", search_params)
            items = search_data.get("items", [])
            if not items:
                return None
            
            resolved_id = items[0]["id"].get("channelId")
            if not resolved_id:
                return None
            # Retrieve full stats for the resolved channel
            data = await cls._make_request("channels", {"part": "snippet,statistics", "id": resolved_id})

        items = data.get("items", [])
        if not items:
            return None

        item = items[0]
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})

        result = {
            "channel_id": item.get("id"),
            "title": snippet.get("title", "Untitled Channel"),
            "description": snippet.get("description", ""),
            "custom_url": snippet.get("customUrl", f"@{value}" if id_type == "handle" else None),
            "subscribers": int(statistics.get("subscriberCount", 0)),
            "video_count": int(statistics.get("videoCount", 0)),
            "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url")
        }

        channel_cache[cache_key] = result
        return result

    @classmethod
    async def verify_channel_code(cls, channel_id: str, code: str) -> bool:
        """
        Directly checks if the unique verification code exists in the channel's About/Description.
        Bypasses cache to guarantee real-time evaluation.
        """
        params = {"part": "snippet", "id": channel_id}
        data = await cls._make_request("channels", params)
        items = data.get("items", [])
        if not items:
            return False

        description = items[0].get("snippet", {}).get("description", "")
        # Case-insensitive substring search for code like CB-48291
        return code.strip().upper() in description.upper()

    @classmethod
    def extract_video_id(cls, video_url: str) -> Optional[str]:
        """Extracts 11-character YouTube video ID from any format."""
        patterns = [
            r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
            r"youtu\.be\/([0-9A-Za-z_-]{11})",
            r"youtube\.com\/shorts\/([0-9A-Za-z_-]{11})"
        ]
        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                return match.group(1)
        return None

    @classmethod
    async def get_video_details(cls, video_url_or_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves video title, thumbnail, and channel info."""
        video_id = cls.extract_video_id(video_url_or_id) or video_url_or_id.strip()
        if len(video_id) != 11:
            return None

        if video_id in video_cache:
            return video_cache[video_id]

        params = {"part": "snippet,contentDetails", "id": video_id}
        data = await cls._make_request("videos", params)
        items = data.get("items", [])
        if not items:
            return None

        item = items[0]
        snippet = item.get("snippet", {})

        result = {
            "video_id": video_id,
            "title": snippet.get("title", "YouTube Video"),
            "channel_title": snippet.get("channelTitle", ""),
            "channel_id": snippet.get("channelId", ""),
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url") or 
                         snippet.get("thumbnails", {}).get("default", {}).get("url"),
            "url": f"https://www.youtube.com/watch?v=/{video_id}"
        }
        video_cache[video_id] = result
        return result

    @classmethod
    async def verify_public_subscription(cls, user_channel_id: str, target_channel_id: str) -> Optional[bool]:
        """
        Attempts to check public subscription status via subscriptions.list.
        Returns:
          True: Confirmed subscribed
          False: Not subscribed
          None: User's subscriptions are private or API restricted
        """
        params = {
            "part": "snippet",
            "channelId": user_channel_id,
            "forChannelId": target_channel_id
        }
        try:
            data = await cls._make_request("subscriptions", params)
            items = data.get("items", [])
            return len(items) > 0
        except YouTubeAPIError:
            # Subscriptions are set to private or inaccessible
            return None
