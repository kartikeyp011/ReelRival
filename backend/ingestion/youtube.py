import re
import logging
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)
import yt_dlp

from backend.config import settings
from backend.models import VideoMetadata, Platform
from backend.ingestion.engagement import compute_engagement_rate

logger = logging.getLogger(__name__)


# ─── URL Parsing ──────────────────────────────────────

def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from any valid YouTube URL format.
    Supports: watch?v=, youtu.be/, shorts/, embed/
    """
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def identify_platform(url: str) -> Platform:
    if "youtube.com" in url or "youtu.be" in url:
        return Platform.youtube
    return Platform.unsupported


# ─── Metadata via YouTube Data API v3 ────────────────

def _fetch_metadata_api(video_id: str) -> Optional[dict]:
    """
    Primary metadata source: YouTube Data API v3.
    Returns raw stats dict or None on failure.
    """
    try:
        youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)
        response = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=video_id
        ).execute()

        items = response.get("items", [])
        if not items:
            logger.warning(f"YouTube API returned no items for video_id={video_id}")
            return None

        item = items[0]
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        content = item.get("contentDetails", {})

        duration_seconds = _parse_duration(content.get("duration", "PT0S"))

        return {
            "title": snippet.get("title", "Unknown Title"),
            "channel": snippet.get("channelTitle", "Unknown Channel"),
            "publish_date": snippet.get("publishedAt", "")[:10],
            "duration_seconds": duration_seconds,
            "view_count": int(stats.get("viewCount", 0)),
            "like_count": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
        }
    except HttpError as e:
        logger.warning(f"YouTube API HttpError for {video_id}: {e}. Falling back to yt-dlp.")
        return None
    except Exception as e:
        logger.warning(f"YouTube API unexpected error for {video_id}: {e}. Falling back to yt-dlp.")
        return None


def _parse_duration(iso_duration: str) -> int:
    """Convert ISO 8601 duration string (PT4M13S) to total seconds."""
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


# ─── Metadata via yt-dlp (fallback) ──────────────────

def _fetch_metadata_ytdlp(video_id: str) -> Optional[dict]:
    """
    Fallback metadata source: yt-dlp.
    Used when YouTube API fails or quota is exhausted.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", "Unknown Title"),
                "channel": info.get("uploader", "Unknown Channel"),
                "publish_date": info.get("upload_date", ""),
                "duration_seconds": info.get("duration", 0),
                "view_count": info.get("view_count", 0) or 0,
                "like_count": info.get("like_count", 0) or 0,
                "comment_count": info.get("comment_count", 0) or 0,
            }
    except Exception as e:
        logger.error(f"yt-dlp also failed for {video_id}: {e}")
        return None


# ─── Transcript via youtube-transcript-api ────────────

def fetch_transcript(video_id: str) -> Optional[list[dict]]:
    """
    Fetch timestamped transcript segments.
    Tries English first, then falls back to any available transcript.
    Returns list of {"text": str, "start": float, "duration": float}
    or None if unavailable.
    """
    # Attempt 1: direct English fetch
    try:
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["en", "en-US", "en-GB"]
        )
        return transcript
    except Exception:
        pass

    # Attempt 2: list all available transcripts and pick the first one
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        # Try manually created transcripts first, then auto-generated
        for transcript in transcript_list:
            try:
                fetched = transcript.fetch()
                # fetched is a FetchedTranscript object — convert to list of dicts
                return [
                    {"text": s.text, "start": s.start, "duration": s.duration}
                    for s in fetched
                ]
            except Exception:
                continue

        logger.warning(f"No usable transcript found for video_id={video_id}")
        return None

    except TranscriptsDisabled:
        logger.warning(f"Transcripts disabled for video_id={video_id}")
        return None
    except NoTranscriptFound:
        logger.warning(f"No transcript found for video_id={video_id}")
        return None
    except Exception as e:
        logger.warning(f"Transcript fetch failed for {video_id}: {e}")
        return None


# ─── Main Public Function ─────────────────────────────

def fetch_video_data(url: str) -> VideoMetadata:
    """
    Full ingestion entry point for one video URL.
    1. Validate URL and extract video ID
    2. Fetch metadata (API → yt-dlp fallback)
    3. Compute engagement rate
    4. Check transcript availability
    Returns a VideoMetadata object.
    Raises ValueError for unsupported URLs or complete fetch failure.
    """
    platform = identify_platform(url)
    if platform == Platform.unsupported:
        raise ValueError(f"Unsupported platform for URL: {url}")

    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")

    # Fetch metadata — try API first, then yt-dlp
    meta = _fetch_metadata_api(video_id)
    if not meta:
        logger.info(f"Falling back to yt-dlp for video_id={video_id}")
        meta = _fetch_metadata_ytdlp(video_id)

    if not meta:
        raise ValueError(f"Could not fetch metadata for video_id={video_id} from any source.")

    engagement_rate = compute_engagement_rate(
        view_count=meta["view_count"],
        like_count=meta["like_count"],
        comment_count=meta["comment_count"],
    )

    # Check transcript availability
    transcript_check = fetch_transcript(video_id)
    transcript_available = transcript_check is not None

    return VideoMetadata(
        video_id=video_id,
        url=url,
        platform=platform,
        title=meta["title"],
        channel=meta["channel"],
        publish_date=meta.get("publish_date"),
        duration_seconds=meta.get("duration_seconds"),
        view_count=meta["view_count"],
        like_count=meta["like_count"],
        comment_count=meta["comment_count"],
        engagement_rate=engagement_rate,
        transcript_available=transcript_available,
    )