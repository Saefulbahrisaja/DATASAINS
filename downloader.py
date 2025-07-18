import requests
import dateparser
import re
import json
from typing import Generator

YOUTUBE_COMMENT_URL = 'https://www.youtube.com/all_comments?v='
YOUTUBE_VIDEO_URL = 'https://www.youtube.com/watch?v='

def extract_video_id(url: str) -> str:
    """Extract the video ID from a YouTube URL."""
    if 'watch?v=' in url:
        return url.split('watch?v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    else:
        raise ValueError("Invalid YouTube URL format.")

def get_comments_from_url(video_url: str, sort_by='top', count=100):
    import yt_dlp
    from youtube_comment_downloader import YoutubeCommentDownloader

    video_id = extract_video_id(video_url)
    downloader = YoutubeCommentDownloader()
    generator = downloader.get_comments_from_url(YOUTUBE_VIDEO_URL + video_id, sort_by=sort_by)

    comments = []
    for comment in generator:
        comments.append({
            'username': comment['author'],
            'comment': comment['text'],
            'time': comment['time'],
            'likes': comment['votes']
        })
        if len(comments) >= count:
            break
    return comments
