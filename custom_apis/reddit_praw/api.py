"""
Core API implementation for Reddit PRAW integration.
"""

import praw
from praw.models import Submission, Comment, Subreddit
from typing import Dict, List, Any, Optional, Tuple, Union
import base64
import io
from PIL import Image
from datetime import datetime, timedelta

from .utilities import RedditAPIBase, ContentSanitizer
from .content_parser import ContentParser
from .media_handler import MediaHandler
from .batch_ops import BatchOperations
from .inference import SubredditAnalyzer


class SubredditReader(RedditAPIBase):
    """Read subreddit information and posts."""
    
    CATEGORY = "reddit"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for SubredditReader."""
        return {
            "required": {
                "client_id": ("STRING", {"multiline": False}),
                "client_secret": ("STRING", {"multiline": False}),
                "user_agent": ("STRING", {"multiline": False}),
                "subreddit": ("STRING", {"multiline": False}),
            },
            "optional": {
                "username": ("STRING", {"multiline": False}),
                "password": ("STRING", {"multiline": False}),
                "sort": (["hot", "new", "top", "rising", "controversial"], {"default": "hot"}),
                "time_filter": (["hour", "day", "week", "month", "year", "all"], {"default": "all"}),
                "limit": ("INTEGER", {"default": 25, "min": 1, "max": 100}),
                "include_nsfw": ("BOOLEAN", {"default": False}),
                "include_stickied": ("BOOLEAN", {"default": False}),
                "include_subreddit_info": ("BOOLEAN", {"default": True}),
                "include_rules": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("subreddit_data",)
    FUNCTION = "get_subreddit_posts"
    
    def get_subreddit_posts(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        subreddit: str,
        username: str = "",
        password: str = "",
        sort: str = "hot",
        time_filter: str = "all",
        limit: int = 25,
        include_nsfw: bool = False,
        include_stickied: bool = False,
        include_subreddit_info: bool = True,
        include_rules: bool = True,
    ) -> Tuple[Dict[str, Any]]:
        """
        Get posts from a subreddit with various sorting options.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
            subreddit: Subreddit name
            username: Reddit username (optional)
            password: Reddit password (optional)
            sort: Sorting method for posts (hot, new, top, rising, controversial)
            time_filter: Time filter for top/controversial sorts (hour, day, week, month, year, all)
            limit: Maximum number of posts to return
            include_nsfw: Whether to include NSFW posts
            include_stickied: Whether to include stickied posts
            include_subreddit_info: Whether to include subreddit information
            include_rules: Whether to include subreddit rules
            
        Returns:
            Dictionary with subreddit information and posts
        """
        # Initialize Reddit API
        auth_params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "user_agent": user_agent,
            "username": username,
            "password": password,
        }
        reddit = self.initialize_reddit(auth_params)
        
        # Get subreddit
        subreddit_obj = reddit.subreddit(subreddit)
        
        # Prepare result dictionary
        result = {
            "subreddit": subreddit,
            "posts": []
        }
        
        # Add subreddit info if requested
        if include_subreddit_info:
            result["subreddit_info"] = self.sanitize_subreddit(subreddit_obj, include_rules=include_rules)
        
        # Get posts based on sort method
        if sort == "hot":
            posts = subreddit_obj.hot(limit=limit)
        elif sort == "new":
            posts = subreddit_obj.new(limit=limit)
        elif sort == "rising":
            posts = subreddit_obj.rising(limit=limit)
        elif sort == "top":
            posts = subreddit_obj.top(time_filter=time_filter, limit=limit)
        elif sort == "controversial":
            posts = subreddit_obj.controversial(time_filter=time_filter, limit=limit)
        else:
            posts = subreddit_obj.hot(limit=limit)
        
        # Process posts
        for post in posts:
            # Skip NSFW posts if not requested
            if not include_nsfw and post.over_18:
                continue
                
            # Skip stickied posts if not requested
            if not include_stickied and post.stickied:
                continue
                
            # Add post to results
            result["posts"].append(self.sanitize_submission(post))
        
        return (result,)


class PostViewer(RedditAPIBase):
    """View post details and comments."""
    
    CATEGORY = "reddit"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for PostViewer."""
        return {
            "required": {
                "client_id": ("STRING", {"multiline": False}),
                "client_secret": ("STRING", {"multiline": False}),
                "user_agent": ("STRING", {"multiline": False}),
                "post_id": ("STRING", {"multiline": False}),
            },
            "optional": {
                "username": ("STRING", {"multiline": False}),
                "password": ("STRING", {"multiline": False}),
                "include_comments": ("BOOLEAN", {"default": True}),
                "comment_sort": (["best", "top", "new", "controversial", "old", "qa"], {"default": "best"}),
                "comment_limit": ("INTEGER", {"default": 25, "min": 0, "max": 100}),
                "comment_depth": ("INTEGER", {"default": 3, "min": 0, "max": 10}),
                "include_media": ("BOOLEAN", {"default": False}),
                "max_image_width": ("INTEGER", {"default": 800, "min": 0, "max": 4096}),
                "max_image_height": ("INTEGER", {"default": 800, "min": 0, "max": 4096}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("post_data",)
    FUNCTION = "get_post_details"
    
    def get_post_details(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        post_id: str,
        username: str = "",
        password: str = "",
        include_comments: bool = True,
        comment_sort: str = "best",
        comment_limit: int = 25,
        comment_depth: int = 3,
        include_media: bool = False,
        max_image_width: int = 800,
        max_image_height: int = 800,
    ) -> Tuple[Dict[str, Any]]:
        """
        Get detailed information about a post including comments.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
            post_id: Reddit post ID
            username: Reddit username (optional)
            password: Reddit password (optional)
            include_comments: Whether to include comments
            comment_sort: Sorting method for comments
            comment_limit: Maximum number of top-level comments to return
            comment_depth: Maximum depth of nested comments
            include_media: Whether to include media (images) as base64
            max_image_width: Maximum width for included images
            max_image_height: Maximum height for included images
            
        Returns:
            Dictionary with post details and comments
        """
        # Initialize Reddit API
        auth_params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "user_agent": user_agent,
            "username": username,
            "password": password,
        }
        reddit = self.initialize_reddit(auth_params)
        
        # Ensure post_id doesn't have the t3_ prefix
        if post_id.startswith('t3_'):
            post_id = post_id[3:]
        
        # Get submission
        submission = reddit.submission(id=post_id)
        
        # Prepare result
        result = self.sanitize_submission(submission, include_body=True)
        
        # Include media if requested
        if include_media:
            result = MediaHandler.extract_media_from_submission(
                result, 
                include_media=True,
                max_width=max_image_width,
                max_height=max_image_height
            )
        
        # Include comments if requested
        if include_comments:
            # Set comment sort
            submission.comment_sort = comment_sort
            
            # Update 0 comment_limit to None (unlimited)
            praw_limit = None if comment_limit == 0 else comment_limit
            
            # Get comments
            submission.comments.replace_more(limit=0)  # Replace "load more comments" objects with actual comments
            comments = list(submission.comments.list())[:praw_limit]
            
            # Process comments
            result["comments"] = []
            for comment in comments:
                result["comments"].append(self.sanitize_comment(comment))
            
            result["comment_count"] = len(result["comments"])
        
        return (result,)


class UserProfileViewer(RedditAPIBase):
    """View user profile information and history."""
    
    CATEGORY = "reddit"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for UserProfileViewer."""
        return {
            "required": {
                "client_id": ("STRING", {"multiline": False}),
                "client_secret": ("STRING", {"multiline": False}),
                "user_agent": ("STRING", {"multiline": False}),
            },
            "optional": {
                "username": ("STRING", {"multiline": False}),
                "password": ("STRING", {"multiline": False}),
                "target_username": ("STRING", {"multiline": False}),
                "include_posts": ("BOOLEAN", {"default": True}),
                "include_comments": ("BOOLEAN", {"default": True}),
                "include_saved": ("BOOLEAN", {"default": False}),
                "sort": (["new", "hot", "top", "controversial"], {"default": "new"}),
                "time_filter": (["hour", "day", "week", "month", "year", "all"], {"default": "all"}),
                "limit": ("INTEGER", {"default": 25, "min": 1, "max": 100}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("user_data",)
    FUNCTION = "get_user_profile"
    
    def get_user_profile(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        username: str = "",
        password: str = "",
        target_username: str = "",
        include_posts: bool = True,
        include_comments: bool = True,
        include_saved: bool = False,
        sort: str = "new",
        time_filter: str = "all",
        limit: int = 25,
    ) -> Tuple[Dict[str, Any]]:
        """
        Get information about a user profile.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
            username: Reddit username (for authentication)
            password: Reddit password (for authentication)
            target_username: Username to get information about (if empty, uses authenticated user)
            include_posts: Whether to include user's posts
            include_comments: Whether to include user's comments
            include_saved: Whether to include user's saved posts (requires authentication)
            sort: Sorting method for posts/comments
            time_filter: Time filter for top/controversial sorts
            limit: Maximum number of posts/comments to return
            
        Returns:
            Dictionary with user profile information
        """
        # Initialize Reddit API
        auth_params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "user_agent": user_agent,
            "username": username,
            "password": password,
        }
        reddit = self.initialize_reddit(auth_params)
        
        # Determine which user to get information about
        if target_username:
            # Get info about specified user
            user = reddit.redditor(target_username)
            is_self = False
        else:
            # Get logged in user
            user = reddit.user.me()
            if not user:
                raise ValueError("No target_username provided and not authenticated")
            is_self = True
            target_username = user.name
        
        # Prepare result
        result = {
            "username": target_username,
            "is_self": is_self,
            "profile": self.sanitize_redditor(user)
        }
        
        # Include posts if requested
        if include_posts:
            result["posts"] = []
            
            # Get posts based on sort method
            if sort == "new":
                posts = user.submissions.new(limit=limit)
            elif sort == "hot":
                posts = user.submissions.hot(limit=limit)
            elif sort == "top":
                posts = user.submissions.top(time_filter=time_filter, limit=limit)
            elif sort == "controversial":
                posts = user.submissions.controversial(time_filter=time_filter, limit=limit)
            else:
                posts = user.submissions.new(limit=limit)
            
            # Process posts
            for post in posts:
                result["posts"].append(self.sanitize_submission(post))
        
        # Include comments if requested
        if include_comments:
            result["comments"] = []
            
            # Get comments based on sort method
            if sort == "new":
                comments = user.comments.new(limit=limit)
            elif sort == "hot":
                comments = user.comments.hot(limit=limit)
            elif sort == "top":
                comments = user.comments.top(time_filter=time_filter, limit=limit)
            elif sort == "controversial":
                comments = user.comments.controversial(time_filter=time_filter, limit=limit)
            else:
                comments = user.comments.new(limit=limit)
            
            # Process comments
            for comment in comments:
                result["comments"].append(self.sanitize_comment(comment))
        
        # Include saved posts if requested and authenticated as user
        if include_saved and is_self:
            result["saved"] = []
            
            # Get saved items
            saved = user.saved(limit=limit)
            
            # Process saved items
            for item in saved:
                if isinstance(item, Submission):
                    result["saved"].append({
                        "type": "submission",
                        "data": self.sanitize_submission(item)
                    })
                elif isinstance(item, Comment):
                    result["saved"].append({
                        "type": "comment",
                        "data": self.sanitize_comment(item)
                    })
        
        # Get subreddits (subscribed or contributed to)
        result["subreddits"] = []
        
        if is_self:
            # Get subscribed subreddits for authenticated user
            for sr in reddit.user.subreddits(limit=limit):
                result["subreddits"].append({
                    "name": sr.display_name,
                    "title": sr.title,
                    "subscribers": sr.subscribers,
                    "is_subscribed": True
                })
        else:
            # For other users, can only see where they post/comment
            subreddits_set = set()
            
            # Add from posts
            if "posts" in result:
                for post in result["posts"]:
                    subreddits_set.add(post["subreddit"])
            
            # Add from comments
            if "comments" in result:
                for comment in result["comments"]:
                    if "subreddit" in comment:
                        subreddits_set.add(comment["subreddit"])
            
            # Convert to list
            for sr_name in sorted(subreddits_set):
                result["subreddits"].append({
                    "name": sr_name,
                    "is_subscribed": None  # Unknown for other users
                })
        
        return (result,)


class PostCreator(RedditAPIBase):
    """Create posts on Reddit."""
    
    CATEGORY = "reddit"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for PostCreator."""
        return {
            "required": {
                "client_id": ("STRING", {"multiline": False}),
                "client_secret": ("STRING", {"multiline": False}),
                "user_agent": ("STRING", {"multiline": False}),
                "username": ("STRING", {"multiline": False}),
                "password": ("STRING", {"multiline": False}),
                "subreddit": ("STRING", {"multiline": False}),
                "title": ("STRING", {"multiline": False}),
                "post_type": (["self", "link", "image"], {"default": "self"}),
            },
            "optional": {
                "selftext": ("STRING", {"multiline": True}),
                "url": ("STRING", {"multiline": False}),
                "image_data": ("STRING", {"multiline": False}),  # Base64-encoded image
                "flair_id": ("STRING", {"multiline": False}),
                "flair_text": ("STRING", {"multiline": False}),
                "nsfw": ("BOOLEAN", {"default": False}),
                "spoiler": ("BOOLEAN", {"default": False}),
                "send_replies": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("post_result",)
    FUNCTION = "create_post"
    
    def create_post(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        username: str,
        password: str,
        subreddit: str,
        title: str,
        post_type: str = "self",
        selftext: str = "",
        url: str = "",
        image_data: str = "",
        flair_id: str = "",
        flair_text: str = "",
        nsfw: bool = False,
        spoiler: bool = False,
        send_replies: bool = True,
    ) -> Tuple[Dict[str, Any]]:
        """
        Create a post on Reddit.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
            username: Reddit username
            password: Reddit password
            subreddit: Subreddit to post to
            title: Post title
            post_type: Type of post (self, link, image)
            selftext: Text content for self posts
            url: URL for link posts
            image_data: Base64-encoded image data for image posts
            flair_id: ID of the flair to use
            flair_text: Text of the flair to use
            nsfw: Whether to mark the post as NSFW
            spoiler: Whether to mark the post as a spoiler
            send_replies: Whether to send replies to post author's inbox
            
        Returns:
            Dictionary with information about the created post
        """
        # Initialize Reddit API
        auth_params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "user_agent": user_agent,
            "username": username,
            "password": password,
        }
        reddit = self.initialize_reddit(auth_params)
        
        # Ensure user is authenticated
        if not reddit.user.me():
            raise ValueError("Authentication required to create posts")
        
        # Get subreddit
        subreddit_obj = reddit.subreddit(subreddit)
        
        # Prepare post parameters
        post_params = {
            "title": title,
            "nsfw": nsfw,
            "spoiler": spoiler,
            "send_replies": send_replies,
        }
        
        # Add flair if provided
        if flair_id:
            post_params["flair_id"] = flair_id
        if flair_text:
            post_params["flair_text"] = flair_text
        
        # Create post based on type
        if post_type == "self":
            post_params["selftext"] = selftext
            new_post = subreddit_obj.submit(**post_params)
        
        elif post_type == "link":
            if not url:
                raise ValueError("URL required for link posts")
            post_params["url"] = url
            new_post = subreddit_obj.submit(**post_params)
        
        elif post_type == "image":
            if not image_data:
                raise ValueError("Image data required for image posts")
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            
            # Create file-like object
            img_file = io.BytesIO(image_bytes)
            
            # Determine image format
            try:
                img = Image.open(img_file)
                img_format = img.format.lower()
                img.close()
                img_file.seek(0)
            except:
                img_format = "jpeg"  # Default format
            
            # Submit image
            new_post = subreddit_obj.submit_image(
                title=title,
                image_path=img_file,
                nsfw=nsfw,
                spoiler=spoiler,
                flair_id=flair_id if flair_id else None,
                flair_text=flair_text if flair_text else None,
                send_replies=send_replies
            )
        
        else:
            raise ValueError(f"Unknown post type: {post_type}")
        
        # Return information about the new post
        return (self.sanitize_submission(new_post),)


class InteractionManager(RedditAPIBase):
    """Manage interactions with Reddit posts and comments."""
    
    CATEGORY = "reddit"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for InteractionManager."""
        return {
            "required": {
                "client_id": ("STRING", {"multiline": False}),
                "client_secret": ("STRING", {"multiline": False}),
                "user_agent": ("STRING", {"multiline": False}),
                "username": ("STRING", {"multiline": False}),
                "password": ("STRING", {"multiline": False}),
                "action": (["upvote_post", "upvote_comment", "comment_on_post", "reply_to_comment"], 
                          {"default": "comment_on_post"}),
                "item_id": ("STRING", {"multiline": False}),
            },
            "optional": {
                "text": ("STRING", {"multiline": True}),
                "direction": (["up", "down", "clear"], {"default": "up"}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("result",)
    FUNCTION = "interact"
    
    def interact(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        username: str,
        password: str,
        action: str,
        item_id: str,
        text: str = "",
        direction: str = "up",
    ) -> Tuple[Dict[str, Any]]:
        """
        Interact with Reddit posts and comments.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
            username: Reddit username
            password: Reddit password
            action: Type of interaction (upvote_post, upvote_comment, comment_on_post, reply_to_comment)
            item_id: ID of the post or comment to interact with
            text: Text content for comments or replies
            direction: Voting direction (up, down, clear)
            
        Returns:
            Dictionary with result of the interaction
        """
        # Initialize Reddit API
        auth_params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "user_agent": user_agent,
            "username": username,
            "password": password,
        }
        reddit = self.initialize_reddit(auth_params)
        
        # Ensure user is authenticated
        if not reddit.user.me():
            raise ValueError("Authentication required for interactions")
        
        # Process item_id to remove prefixes if present
        if item_id.startswith('t3_'):  # Post prefix
            item_id = item_id[3:]
        elif item_id.startswith('t1_'):  # Comment prefix
            item_id = item_id[3:]
        
        # Perform action
        result = {"action": action, "success": True}
        
        if action == "upvote_post":
            submission = reddit.submission(id=item_id)
            
            if direction == "up":
                submission.upvote()
                result["message"] = "Post upvoted successfully"
            elif direction == "down":
                submission.downvote()
                result["message"] = "Post downvoted successfully"
            else:  # clear
                submission.clear_vote()
                result["message"] = "Vote cleared successfully"
                
            result["item"] = self.sanitize_submission(submission)
            
        elif action == "upvote_comment":
            comment = reddit.comment(id=item_id)
            
            if direction == "up":
                comment.upvote()
                result["message"] = "Comment upvoted successfully"
            elif direction == "down":
                comment.downvote()
                result["message"] = "Comment downvoted successfully"
            else:  # clear
                comment.clear_vote()
                result["message"] = "Vote cleared successfully"
                
            result["item"] = self.sanitize_comment(comment)
            
        elif action == "comment_on_post":
            if not text:
                raise ValueError("Text content required for commenting")
                
            submission = reddit.submission(id=item_id)
            new_comment = submission.reply(text)
            
            result["message"] = "Comment posted successfully"
            result["item"] = self.sanitize_comment(new_comment)
            
        elif action == "reply_to_comment":
            if not text:
                raise ValueError("Text content required for replying")
                
            comment = reddit.comment(id=item_id)
            new_reply = comment.reply(text)
            
            result["message"] = "Reply posted successfully"
            result["item"] = self.sanitize_comment(new_reply)
            
        else:
            raise ValueError(f"Unknown action: {action}")
        
        return (result,)


class CommentMonitor(RedditAPIBase):
    """Monitor for new comments on Reddit posts."""
    
    CATEGORY = "reddit"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for CommentMonitor."""
        return {
            "required": {
                "client_id": ("STRING", {"multiline": False}),
                "client_secret": ("STRING", {"multiline": False}),
                "user_agent": ("STRING", {"multiline": False}),
                "submission_id": ("STRING", {"multiline": False}),
            },
            "optional": {
                "username": ("STRING", {"multiline": False}),
                "password": ("STRING", {"multiline": False}),
                "known_comment_ids": ("STRING", {"multiline": True}),  # JSON array of comment IDs
                "return_content": ("BOOLEAN", {"default": True}),
                "sort": (["new", "old", "top", "controversial"], {"default": "new"}),
                "limit": ("INTEGER", {"default": 50, "min": 1, "max": 100}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("comments_data",)
    FUNCTION = "check_new_comments"
    
    def check_new_comments(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        submission_id: str,
        username: str = "",
        password: str = "",
        known_comment_ids: str = "[]",
        return_content: bool = True,
        sort: str = "new",
        limit: int = 50,
    ) -> Tuple[Dict[str, Any]]:
        """
        Check for new comments on a submission.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
            submission_id: ID of the submission to check for new comments
            username: Reddit username (optional)
            password: Reddit password (optional)
            known_comment_ids: JSON array of already known comment IDs
            return_content: Whether to return full comment content or just IDs
            sort: How to sort comments
            limit: Maximum number of comments to check
            
        Returns:
            Dictionary with new comments information
        """
        # Initialize Reddit API
        auth_params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "user_agent": user_agent,
            "username": username,
            "password": password,
        }
        reddit = self.initialize_reddit(auth_params)
        
        # Process submission_id to remove prefix if present
        if submission_id.startswith('t3_'):
            submission_id = submission_id[3:]
        
        # Get submission
        submission = reddit.submission(id=submission_id)
        
        # Parse known comment IDs
        import json
        try:
            known_ids = set(json.loads(known_comment_ids))
        except:
            known_ids = set()
        
        # Get comments
        submission.comment_sort = sort
        submission.comments.replace_more(limit=0)
        all_comments = list(submission.comments.list())[:limit]
        
        # Find new comments
        new_comments = []
        for comment in all_comments:
            if comment.id not in known_ids:
                if return_content:
                    new_comments.append(self.sanitize_comment(comment))
                else:
                    new_comments.append({"id": comment.id})
        
        # Prepare result
        result = {
            "submission_id": submission_id,
            "new_comments": new_comments,
            "has_new_comments": len(new_comments) > 0,
            "total_new_comments": len(new_comments),
            "total_comments": len(all_comments),
        }
        
        return (result,)


class SubredditManager(RedditAPIBase):
    """Manage subreddit subscriptions and favorites."""
    
    CATEGORY = "reddit"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for SubredditManager."""
        return {
            "required": {
                "client_id": ("STRING", {"multiline": False}),
                "client_secret": ("STRING", {"multiline": False}),
                "user_agent": ("STRING", {"multiline": False}),
                "username": ("STRING", {"multiline": False}),
                "password": ("STRING", {"multiline": False}),
                "action": (["subscribe", "unsubscribe", "favorite", "unfavorite", "get_subscribed", "get_favorites"], 
                          {"default": "get_subscribed"}),
            },
            "optional": {
                "subreddit": ("STRING", {"multiline": False}),
                "limit": ("INTEGER", {"default": 25, "min": 1, "max": 100}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("result",)
    FUNCTION = "manage_subreddit"
    
    def manage_subreddit(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        username: str,
        password: str,
        action: str,
        subreddit: str = "",
        limit: int = 25,
    ) -> Tuple[Dict[str, Any]]:
        """
        Manage subreddit subscriptions and favorites.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
            username: Reddit username
            password: Reddit password
            action: Action to perform (subscribe, unsubscribe, favorite, unfavorite, get_subscribed, get_favorites)
            subreddit: Subreddit to perform action on (not needed for listing actions)
            limit: Maximum number of subreddits to return for listing actions
            
        Returns:
            Dictionary with result of the action
        """
        # Initialize Reddit API
        auth_params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "user_agent": user_agent,
            "username": username,
            "password": password,
        }
        reddit = self.initialize_reddit(auth_params)
        
        # Ensure user is authenticated
        if not reddit.user.me():
            raise ValueError("Authentication required for subreddit management")
        
        # Prepare result
        result = {"action": action, "success": True}
        
        # Perform action
        if action in ["subscribe", "unsubscribe", "favorite", "unfavorite"]:
            if not subreddit:
                raise ValueError("Subreddit name required for this action")
                
            sr = reddit.subreddit(subreddit)
            
            if action == "subscribe":
                sr.subscribe()
                result["message"] = f"Successfully subscribed to r/{subreddit}"
                
            elif action == "unsubscribe":
                sr.unsubscribe()
                result["message"] = f"Successfully unsubscribed from r/{subreddit}"
                
            elif action == "favorite":
                sr.favorite()
                result["message"] = f"Successfully added r/{subreddit} to favorites"
                
            elif action == "unfavorite":
                sr.unfavorite()
                result["message"] = f"Successfully removed r/{subreddit} from favorites"
                
            result["subreddit"] = self.sanitize_subreddit(sr)
            
        elif action == "get_subscribed":
            subreddits = []
            for sr in reddit.user.subreddits(limit=limit):
                subreddits.append(self.sanitize_subreddit(sr, include_rules=False))
                
            result["subreddits"] = subreddits
            result["count"] = len(subreddits)
            result["message"] = f"Retrieved {len(subreddits)} subscribed subreddits"
            
        elif action == "get_favorites":
            # Note: PRAW doesn't have a direct way to get favorites, so this needs to be implemented with custom code
            # This is a placeholder that would need expansion with Reddit's API directly
            result["message"] = "Getting favorites not implemented in PRAW"
            result["success"] = False
            
        else:
            raise ValueError(f"Unknown action: {action}")
        
        return (result,)


class BatchSubredditManager(RedditAPIBase):
    """Batch operations for managing multiple subreddits at once."""
    
    CATEGORY = "reddit"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for BatchSubredditManager."""
        return {
            "required": {
                "client_id": ("STRING", {"multiline": False}),
                "client_secret": ("STRING", {"multiline": False}),
                "user_agent": ("STRING", {"multiline": False}),
                "username": ("STRING", {"multiline": False}),
                "password": ("STRING", {"multiline": False}),
                "action": (["subscribe", "unsubscribe", "favorite", "unfavorite"], 
                          {"default": "subscribe"}),
                "subreddits": ("STRING", {"multiline": True}),  # JSON array or newline-separated list
            },
            "optional": {
                "max_workers": ("INTEGER", {"default": 5, "min": 1, "max": 10}),
                "skip_existing": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("batch_result",)
    FUNCTION = "batch_manage_subreddits"
    
    def batch_manage_subreddits(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        username: str,
        password: str,
        action: str,
        subreddits: str,
        max_workers: int = 5,
        skip_existing: bool = True,
    ) -> Tuple[Dict[str, Any]]:
        """
        Perform batch operations on multiple subreddits.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
            username: Reddit username
            password: Reddit password
            action: Action to perform (subscribe, unsubscribe, favorite, unfavorite)
            subreddits: JSON array or newline-separated list of subreddits
            max_workers: Maximum number of concurrent operations
            skip_existing: Whether to skip already subscribed/favorited subreddits
            
        Returns:
            Dictionary with results of the batch operation
        """
        # Initialize Reddit API
        auth_params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "user_agent": user_agent,
            "username": username,
            "password": password,
        }
        reddit = self.initialize_reddit(auth_params)
        
        # Ensure user is authenticated
        if not reddit.user.me():
            raise ValueError("Authentication required for batch operations")
        
        # Parse subreddits list
        import json
        try:
            # Try to parse as JSON
            subreddit_list = json.loads(subreddits)
        except:
            # If not JSON, treat as newline-separated list
            subreddit_list = [s.strip() for s in subreddits.split('\n') if s.strip()]
        
        # Perform batch operation
        if action == "subscribe":
            result = BatchOperations.batch_subscribe_subreddits(
                reddit, subreddit_list, max_workers, skip_existing
            )
        elif action == "unsubscribe":
            result = BatchOperations.batch_unsubscribe_subreddits(
                reddit, subreddit_list, max_workers
            )
        elif action == "favorite":
            result = BatchOperations.batch_favorite_subreddits(
                reddit, subreddit_list, max_workers, skip_existing
            )
        elif action == "unfavorite":
            result = BatchOperations.batch_unfavorite_subreddits(
                reddit, subreddit_list, max_workers
            )
        else:
            raise ValueError(f"Unknown action: {action}")
        
        # Add action to result
        result["action"] = action
        
        return (result,)


class SubredditAnalyzerAPI(RedditAPIBase):
    """Analyze subreddit rules and requirements."""
    
    CATEGORY = "reddit"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for SubredditAnalyzerAPI."""
        return {
            "required": {
                "client_id": ("STRING", {"multiline": False}),
                "client_secret": ("STRING", {"multiline": False}),
                "user_agent": ("STRING", {"multiline": False}),
                "subreddit": ("STRING", {"multiline": False}),
            },
            "optional": {
                "username": ("STRING", {"multiline": False}),
                "password": ("STRING", {"multiline": False}),
                "analysis_depth": (["basic", "standard", "deep"], {"default": "standard"}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("analysis_result",)
    FUNCTION = "analyze_subreddit"
    
    def analyze_subreddit(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        subreddit: str,
        username: str = "",
        password: str = "",
        analysis_depth: str = "standard",
    ) -> Tuple[Dict[str, Any]]:
        """
        Analyze subreddit rules and requirements.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
            subreddit: Subreddit to analyze
            username: Reddit username (optional)
            password: Reddit password (optional)
            analysis_depth: Depth of analysis (basic, standard, deep)
            
        Returns:
            Dictionary with analysis results
        """
        # Initialize Reddit API
        auth_params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "user_agent": user_agent,
            "username": username,
            "password": password,
        }
        reddit = self.initialize_reddit(auth_params)
        
        # Get subreddit
        subreddit_obj = reddit.subreddit(subreddit)
        
        # Analyze subreddit
        result = SubredditAnalyzer.analyze_subreddit_requirements(subreddit_obj, analysis_depth)
        
        return (result,)


# Define mappings for the API server
NODE_CLASS_MAPPINGS = {
    "Subreddit Reader": SubredditReader,
    "Post Viewer": PostViewer,
    "User Profile Viewer": UserProfileViewer,
    "Post Creator": PostCreator,
    "Interaction Manager": InteractionManager,
    "Comment Monitor": CommentMonitor,
    "Subreddit Manager": SubredditManager,
    "Batch Subreddit Manager": BatchSubredditManager,
    "Subreddit Analyzer": SubredditAnalyzerAPI,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Subreddit Reader": "Subreddit Reader",
    "Post Viewer": "Post Viewer",
    "User Profile Viewer": "User Profile Viewer",
    "Post Creator": "Post Creator",
    "Interaction Manager": "Interaction Manager",
    "Comment Monitor": "Comment Monitor",
    "Subreddit Manager": "Subreddit Manager",
    "Batch Subreddit Manager": "Batch Subreddit Manager",
    "Subreddit Analyzer": "Subreddit Analyzer",
}

# Define which APIs run in queue mode
API_SERVER_QUEUE_MODE = {
    SubredditReader: False,  # Fast read operations
    PostViewer: False,
    UserProfileViewer: False,
    PostCreator: True,  # Content creation runs in queue mode
    InteractionManager: True,  # Interactions run in queue mode
    CommentMonitor: False,
    SubredditManager: True,  # Subscription management runs in queue mode
    BatchSubredditManager: True,  # Batch operations run in queue mode
    SubredditAnalyzerAPI: True,  # Deep analysis can be slow
}
