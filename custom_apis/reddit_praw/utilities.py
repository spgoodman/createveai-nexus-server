"""
Utility functions and helper classes for the Reddit PRAW API.
"""

import re
import base64
import html
import json
from datetime import datetime
from typing import Dict, List, Any, Union, Optional, Tuple
from bs4 import BeautifulSoup
import html2text
import praw
from praw.models import Submission, Comment, Subreddit, Redditor


class ContentSanitizer:
    """Class for sanitizing Reddit content, stripping HTML and markdown."""
    
    @staticmethod
    def strip_html(content: str) -> str:
        """Remove HTML tags from content."""
        if not content:
            return ""
        soup = BeautifulSoup(content, 'html.parser')
        return soup.get_text()
    
    @staticmethod
    def convert_markdown(content: str) -> str:
        """Convert markdown to plain text."""
        if not content:
            return ""
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_emphasis = True
        h.body_width = 0  # No line wrapping
        return h.handle(content)
    
    @staticmethod
    def normalize_text(content: str) -> str:
        """Normalize whitespace and other text elements."""
        if not content:
            return ""
        # Replace multiple whitespaces with a single space
        content = re.sub(r'\s+', ' ', content)
        # Decode HTML entities
        content = html.unescape(content)
        return content.strip()
    
    @classmethod
    def sanitize(cls, content: str, keep_markdown: bool = False) -> str:
        """Sanitize content by removing HTML and optionally markdown."""
        if not content:
            return ""
        
        # Remove HTML
        content = cls.strip_html(content)
        
        if not keep_markdown:
            # Convert markdown to plain text
            content = cls.convert_markdown(content)
        
        # Normalize text
        return cls.normalize_text(content)


class RedditAPIBase:
    """Base class for Reddit API endpoints."""
    
    @staticmethod
    def initialize_reddit(auth_params: Dict[str, str]) -> praw.Reddit:
        """
        Initialize the Reddit API client with authentication parameters.
        
        Args:
            auth_params: Dictionary containing authentication parameters
                (client_id, client_secret, user_agent, username, password)
                
        Returns:
            Authenticated Reddit instance
        """
        required_params = ['client_id', 'client_secret', 'user_agent']
        for param in required_params:
            if param not in auth_params or not auth_params[param]:
                raise ValueError(f"Missing required authentication parameter: {param}")
        
        # Create Reddit instance
        reddit_kwargs = {
            'client_id': auth_params['client_id'],
            'client_secret': auth_params['client_secret'],
            'user_agent': auth_params['user_agent'],
        }
        
        # Add username and password if provided
        if 'username' in auth_params and 'password' in auth_params:
            if auth_params['username'] and auth_params['password']:
                reddit_kwargs['username'] = auth_params['username']
                reddit_kwargs['password'] = auth_params['password']
        
        return praw.Reddit(**reddit_kwargs)
    
    @staticmethod
    def sanitize_timestamp(timestamp: Optional[float]) -> Optional[str]:
        """Convert Unix timestamp to ISO format string."""
        if timestamp is None:
            return None
        return datetime.fromtimestamp(timestamp).isoformat()
    
    @staticmethod
    def sanitize_author(author: Optional[Redditor]) -> Optional[Dict[str, Any]]:
        """Sanitize author information."""
        if author is None:
            return None
        if isinstance(author, str):
            return {"name": author}
        
        try:
            return {
                "name": author.name,
                "id": author.id,
                "is_mod": bool(getattr(author, 'is_mod', False)),
                "is_gold": bool(getattr(author, 'is_gold', False))
            }
        except Exception:
            # If author was deleted or has restricted access
            return {"name": "[deleted]"}
    
    @classmethod
    def sanitize_submission(cls, submission: Submission, include_body: bool = True) -> Dict[str, Any]:
        """
        Convert a PRAW Submission object to a sanitized dictionary.
        
        Args:
            submission: PRAW Submission object
            include_body: Whether to include the submission body/selftext
            
        Returns:
            Sanitized submission dictionary
        """
        result = {
            "id": submission.id,
            "title": submission.title,
            "permalink": submission.permalink,
            "url": submission.url,
            "author": cls.sanitize_author(submission.author),
            "created_utc": cls.sanitize_timestamp(submission.created_utc),
            "score": submission.score,
            "upvote_ratio": submission.upvote_ratio,
            "num_comments": submission.num_comments,
            "is_self": submission.is_self,
            "is_video": submission.is_video,
            "is_original_content": submission.is_original_content,
            "over_18": submission.over_18,
            "spoiler": submission.spoiler,
            "link_flair_text": submission.link_flair_text,
            "subreddit": submission.subreddit.display_name,
        }
        
        # Include selftext if it's a self post and include_body is True
        if submission.is_self and include_body and hasattr(submission, 'selftext'):
            result["selftext"] = ContentSanitizer.sanitize(submission.selftext)
            result["selftext_html"] = submission.selftext_html
        
        return result
    
    @classmethod
    def sanitize_comment(cls, comment: Comment) -> Dict[str, Any]:
        """
        Convert a PRAW Comment object to a sanitized dictionary.
        
        Args:
            comment: PRAW Comment object
            
        Returns:
            Sanitized comment dictionary
        """
        try:
            result = {
                "id": comment.id,
                "body": ContentSanitizer.sanitize(comment.body),
                "body_html": comment.body_html,
                "author": cls.sanitize_author(comment.author),
                "created_utc": cls.sanitize_timestamp(comment.created_utc),
                "score": comment.score,
                "permalink": comment.permalink,
                "is_submitter": comment.is_submitter,
                "stickied": comment.stickied,
                "submission_id": comment.submission.id if hasattr(comment, 'submission') else None,
            }

            # Handle edited
            if hasattr(comment, 'edited') and comment.edited:
                result["edited"] = True
                if isinstance(comment.edited, (int, float)):
                    result["edited_timestamp"] = cls.sanitize_timestamp(comment.edited)
            else:
                result["edited"] = False

            return result
        except Exception as e:
            # Fallback for errors
            return {
                "id": getattr(comment, 'id', 'unknown'),
                "body": "[Error retrieving comment data]",
                "error": str(e)
            }
    
    @classmethod
    def sanitize_subreddit(cls, subreddit: Subreddit, include_rules: bool = True) -> Dict[str, Any]:
        """
        Convert a PRAW Subreddit object to a sanitized dictionary.
        
        Args:
            subreddit: PRAW Subreddit object
            include_rules: Whether to include subreddit rules
            
        Returns:
            Sanitized subreddit dictionary
        """
        result = {
            "id": subreddit.id,
            "name": subreddit.display_name,
            "title": subreddit.title,
            "description": ContentSanitizer.sanitize(subreddit.description),
            "description_html": subreddit.description_html,
            "public_description": ContentSanitizer.sanitize(subreddit.public_description),
            "subscribers": subreddit.subscribers,
            "created_utc": cls.sanitize_timestamp(subreddit.created_utc),
            "url": subreddit.url,
            "over18": subreddit.over18,
            "is_private": subreddit.subreddit_type == "private",
            "is_restricted": subreddit.subreddit_type == "restricted",
        }
        
        # Include available flairs if accessible
        try:
            link_flairs = []
            for flair in subreddit.flair.link_templates:
                link_flairs.append({
                    "id": flair["id"],
                    "text": flair["text"],
                    "background_color": flair.get("background_color", ""),
                    "text_color": flair.get("text_color", ""),
                })
            result["link_flairs"] = link_flairs
        except Exception:
            result["link_flairs"] = []
        
        # Include rules if requested
        if include_rules:
            try:
                rules = []
                for rule in subreddit.rules:
                    rules.append({
                        "short_name": rule.short_name,
                        "description": ContentSanitizer.sanitize(rule.description),
                        "violation_reason": rule.violation_reason,
                        "created_utc": cls.sanitize_timestamp(rule.created_utc),
                    })
                result["rules"] = rules
            except Exception:
                result["rules"] = []
        
        return result
    
    @classmethod
    def sanitize_redditor(cls, redditor: Redditor) -> Dict[str, Any]:
        """
        Convert a PRAW Redditor object to a sanitized dictionary.
        
        Args:
            redditor: PRAW Redditor object
            
        Returns:
            Sanitized redditor dictionary
        """
        if redditor is None:
            return {"name": "[deleted]"}
            
        try:
            result = {
                "id": redditor.id,
                "name": redditor.name,
                "created_utc": cls.sanitize_timestamp(redditor.created_utc),
                "comment_karma": redditor.comment_karma,
                "link_karma": redditor.link_karma,
                "is_gold": bool(getattr(redditor, 'is_gold', False)),
                "is_mod": bool(getattr(redditor, 'is_mod', False)),
                "has_verified_email": bool(getattr(redditor, 'has_verified_email', False)),
            }
            
            return result
        except Exception as e:
            # Fallback for errors
            return {
                "name": getattr(redditor, 'name', '[unknown]'),
                "error": str(e)
            }
    
    @staticmethod
    def to_base64(data: bytes) -> str:
        """Convert binary data to base64 string."""
        return base64.b64encode(data).decode('utf-8')
    
    @staticmethod
    def from_base64(data: str) -> bytes:
        """Convert base64 string to binary data."""
        return base64.b64decode(data)
