def compute_engagement_rate(
    view_count: int,
    like_count: int,
    comment_count: int
) -> float:
    """
    Engagement rate = (likes + comments) / views * 100
    Returns 0.0 if views are zero to avoid division errors.
    """
    if view_count == 0:
        return 0.0
    rate = (like_count + comment_count) / view_count * 100
    return round(rate, 4)