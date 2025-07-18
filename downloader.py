# downloader.py
from youtube_comment_downloader import YoutubeCommentDownloader
import re

def parse_likes(votes_str):
    try:
        votes_str = votes_str.strip().lower()
        if 'rb' in votes_str:
            return int(float(votes_str.replace('rb', '').replace(',', '.')) * 1000)
        return int(votes_str)
    except:
        return 0

def get_comments_from_url(url, sort_by="top", count=300):
    downloader = YoutubeCommentDownloader()
    generator = downloader.get_comments_from_url(url, sort_by=sort_by)

    comments = []
    for comment in generator:
        try:
            like_str = comment.get("votes", "0")
            likes = parse_likes(like_str)
            comments.append({
                "username": comment.get("author", ""),
                "text": comment.get("text", ""),
                "time": comment.get("time", ""),
                "likes": likes
            })
            if len(comments) >= count:
                break
        except Exception:
            continue

    return comments
