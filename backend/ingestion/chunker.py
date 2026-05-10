import uuid
from typing import Optional
from backend.models import TranscriptChunk, ChunkType, VideoMetadata


def _seconds_to_label(seconds: float) -> str:
    """Convert float seconds to readable MM:SS or H:MM:SS label."""
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def build_summary_chunk(meta: VideoMetadata, transcript_segments: Optional[list[dict]]) -> TranscriptChunk:
    """
    Create one metadata summary chunk per video.
    This chunk answers high-level comparison questions directly
    without needing transcript retrieval.
    """
    intro_text = ""
    if transcript_segments:
        # Take first ~30 seconds of transcript as context
        intro_parts = []
        for seg in transcript_segments:
            if seg["start"] > 30:
                break
            intro_parts.append(seg["text"])
        intro_text = " ".join(intro_parts).strip()

    duration_label = "Unknown"
    if meta.duration_seconds:
        duration_label = _seconds_to_label(meta.duration_seconds)

    summary_text = (
        f"Video: \"{meta.title}\" by {meta.channel}. "
        f"Published: {meta.publish_date or 'Unknown'}. "
        f"Duration: {duration_label}. "
        f"Views: {meta.view_count:,}. "
        f"Likes: {meta.like_count:,}. "
        f"Comments: {meta.comment_count:,}. "
        f"Engagement rate: {meta.engagement_rate}%. "
        f"Opening: {intro_text}"
    ).strip()

    return TranscriptChunk(
        chunk_id=f"{meta.video_id}_summary",
        video_id=meta.video_id,
        video_title=meta.title,
        chunk_index=0,
        chunk_type=ChunkType.summary,
        start_time=None,
        end_time=None,
        start_label=None,
        end_label=None,
        text=summary_text,
    )


def chunk_transcript(
    meta: VideoMetadata,
    transcript_segments: list[dict],
    window_seconds: int = 60,
    overlap_seconds: int = 15,
) -> list[TranscriptChunk]:
    """
    Split transcript into timestamp-based chunks.

    Strategy:
    - Group transcript segments into windows of `window_seconds`
    - Carry `overlap_seconds` from end of previous chunk into start of next
    - Each chunk stores start/end timestamps for citations
    - Returns list of TranscriptChunk (excluding summary chunk)
    """
    if not transcript_segments:
        return []

    chunks: list[TranscriptChunk] = []
    chunk_index = 1  # 0 is reserved for summary chunk
    i = 0
    total = len(transcript_segments)

    while i < total:
        window_start = transcript_segments[i]["start"]
        window_end = window_start + window_seconds

        # Collect all segments within this window
        window_segs = []
        j = i
        while j < total and transcript_segments[j]["start"] < window_end:
            window_segs.append(transcript_segments[j])
            j += 1

        if not window_segs:
            break

        chunk_text = " ".join(seg["text"] for seg in window_segs).strip()
        actual_start = window_segs[0]["start"]
        actual_end = window_segs[-1]["start"] + window_segs[-1].get("duration", 0)

        chunk = TranscriptChunk(
            chunk_id=f"{meta.video_id}_chunk_{chunk_index}",
            video_id=meta.video_id,
            video_title=meta.title,
            chunk_index=chunk_index,
            chunk_type=ChunkType.transcript,
            start_time=actual_start,
            end_time=actual_end,
            start_label=_seconds_to_label(actual_start),
            end_label=_seconds_to_label(actual_end),
            text=chunk_text,
        )
        chunks.append(chunk)
        chunk_index += 1

        # Move pointer forward, backing up by overlap_seconds
        # Find the first segment that starts AFTER (window_end - overlap_seconds)
        overlap_start = window_end - overlap_seconds
        next_i = j
        for k in range(j - 1, i, -1):
            if transcript_segments[k]["start"] >= overlap_start:
                next_i = k
            else:
                break

        # Safety: always advance at least one segment to prevent infinite loop
        if next_i <= i:
            next_i = i + 1

        i = next_i

    return chunks


def build_all_chunks(
    meta: VideoMetadata,
    transcript_segments: Optional[list[dict]],
) -> list[TranscriptChunk]:
    """
    Master function: builds summary chunk + all transcript chunks.
    Returns them in order: [summary, chunk_1, chunk_2, ...]
    """
    summary = build_summary_chunk(meta, transcript_segments)
    if not transcript_segments:
        return [summary]

    transcript_chunks = chunk_transcript(meta, transcript_segments)
    return [summary] + transcript_chunks