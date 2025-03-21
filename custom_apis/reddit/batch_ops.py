"""
Batch operations for Reddit API functionality.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import praw
from praw.models import Subreddit
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utilities import RedditAPIBase


class BatchOperations(RedditAPIBase):
    """Handle batch operations for Reddit actions like subscribing to multiple subreddits."""
    
    @classmethod
    def batch_subscribe_subreddits(cls, reddit: praw.Reddit, 
                                 subreddit_names: List[str], 
                                 max_workers: int = 5,
                                 skip_existing: bool = True) -> Dict[str, List[Any]]:
        """
        Subscribe to multiple subreddits in batch.
        
        Args:
            reddit: Authenticated Reddit instance
            subreddit_names: List of subreddit names to subscribe to
            max_workers: Maximum number of concurrent workers
            skip_existing: Whether to skip already subscribed subreddits
            
        Returns:
            Dictionary with results categorized by status
        """
        if not reddit or not subreddit_names:
            return {
                "successful": [],
                "already_subscribed": [],
                "failed": []
            }
        
        # De-duplicate subreddit names and convert to lowercase
        subreddit_names = list(set([name.lower() for name in subreddit_names if name]))
        
        # Check if the user is authenticated
        if not reddit.user.me():
            return {
                "successful": [],
                "already_subscribed": [],
                "failed": [{"subreddit": name, "reason": "Not authenticated"} for name in subreddit_names]
            }
        
        # Get current subscriptions if needed
        current_subscriptions = set()
        if skip_existing:
            try:
                for subreddit in reddit.user.subreddits(limit=None):
                    current_subscriptions.add(subreddit.display_name.lower())
            except Exception as e:
                print(f"Error getting current subscriptions: {str(e)}")
        
        # Results container
        results = {
            "successful": [],
            "already_subscribed": [],
            "failed": []
        }
        
        # Function to process a single subreddit
        def process_subreddit(name: str) -> Tuple[str, str, Optional[str]]:
            """Process a single subreddit subscription. Returns (name, status, error_reason)"""
            try:
                # Skip if already subscribed and skip_existing is True
                if skip_existing and name.lower() in current_subscriptions:
                    return (name, "already_subscribed", None)
                
                # Get the subreddit
                subreddit = reddit.subreddit(name)
                
                # Check if subreddit exists
                # This will raise an exception if the subreddit doesn't exist
                display_name = subreddit.display_name
                
                # Subscribe
                subreddit.subscribe()
                
                return (name, "successful", None)
            except Exception as e:
                return (name, "failed", str(e))
        
        # Process subreddits in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_subreddit, name): name for name in subreddit_names}
            
            for future in as_completed(futures):
                name, status, error = future.result()
                if status == "successful":
                    results["successful"].append(name)
                elif status == "already_subscribed":
                    results["already_subscribed"].append(name)
                else:
                    results["failed"].append({"subreddit": name, "reason": error})
        
        # Add summary
        results["summary"] = f"{len(results['successful'])} subscribed, " \
                            f"{len(results['already_subscribed'])} already subscribed, " \
                            f"{len(results['failed'])} failed"
        
        return results
    
    @classmethod
    def batch_unsubscribe_subreddits(cls, reddit: praw.Reddit, 
                                   subreddit_names: List[str], 
                                   max_workers: int = 5) -> Dict[str, List[Any]]:
        """
        Unsubscribe from multiple subreddits in batch.
        
        Args:
            reddit: Authenticated Reddit instance
            subreddit_names: List of subreddit names to unsubscribe from
            max_workers: Maximum number of concurrent workers
            
        Returns:
            Dictionary with results categorized by status
        """
        if not reddit or not subreddit_names:
            return {
                "successful": [],
                "not_subscribed": [],
                "failed": []
            }
        
        # De-duplicate subreddit names and convert to lowercase
        subreddit_names = list(set([name.lower() for name in subreddit_names if name]))
        
        # Check if the user is authenticated
        if not reddit.user.me():
            return {
                "successful": [],
                "not_subscribed": [],
                "failed": [{"subreddit": name, "reason": "Not authenticated"} for name in subreddit_names]
            }
        
        # Get current subscriptions
        current_subscriptions = {}
        try:
            for subreddit in reddit.user.subreddits(limit=None):
                current_subscriptions[subreddit.display_name.lower()] = subreddit
        except Exception as e:
            print(f"Error getting current subscriptions: {str(e)}")
        
        # Results container
        results = {
            "successful": [],
            "not_subscribed": [],
            "failed": []
        }
        
        # Function to process a single subreddit
        def process_subreddit(name: str) -> Tuple[str, str, Optional[str]]:
            """Process a single subreddit unsubscription. Returns (name, status, error_reason)"""
            try:
                # Skip if not subscribed
                if name.lower() not in current_subscriptions:
                    return (name, "not_subscribed", None)
                
                # Get the subreddit
                subreddit = current_subscriptions[name.lower()]
                
                # Unsubscribe
                subreddit.unsubscribe()
                
                return (name, "successful", None)
            except Exception as e:
                return (name, "failed", str(e))
        
        # Process subreddits in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_subreddit, name): name for name in subreddit_names}
            
            for future in as_completed(futures):
                name, status, error = future.result()
                if status == "successful":
                    results["successful"].append(name)
                elif status == "not_subscribed":
                    results["not_subscribed"].append(name)
                else:
                    results["failed"].append({"subreddit": name, "reason": error})
        
        # Add summary
        results["summary"] = f"{len(results['successful'])} unsubscribed, " \
                            f"{len(results['not_subscribed'])} not subscribed, " \
                            f"{len(results['failed'])} failed"
        
        return results
    
    @classmethod
    def batch_favorite_subreddits(cls, reddit: praw.Reddit, 
                                subreddit_names: List[str], 
                                max_workers: int = 5,
                                skip_existing: bool = True) -> Dict[str, List[Any]]:
        """
        Favorite multiple subreddits in batch.
        
        Args:
            reddit: Authenticated Reddit instance
            subreddit_names: List of subreddit names to favorite
            max_workers: Maximum number of concurrent workers
            skip_existing: Whether to skip already favorited subreddits
            
        Returns:
            Dictionary with results categorized by status
        """
        if not reddit or not subreddit_names:
            return {
                "successful": [],
                "already_favorited": [],
                "failed": []
            }
        
        # De-duplicate subreddit names and convert to lowercase
        subreddit_names = list(set([name.lower() for name in subreddit_names if name]))
        
        # Check if the user is authenticated
        if not reddit.user.me():
            return {
                "successful": [],
                "already_favorited": [],
                "failed": [{"subreddit": name, "reason": "Not authenticated"} for name in subreddit_names]
            }
        
        # Results container
        results = {
            "successful": [],
            "already_favorited": [],
            "failed": []
        }
        
        # Function to process a single subreddit
        def process_subreddit(name: str) -> Tuple[str, str, Optional[str]]:
            """Process a single subreddit favorite. Returns (name, status, error_reason)"""
            try:
                # Get the subreddit
                subreddit = reddit.subreddit(name)
                
                # Check if subreddit exists
                # This will raise an exception if the subreddit doesn't exist
                display_name = subreddit.display_name
                
                # Favorite
                try:
                    subreddit.favorite()
                    return (name, "successful", None)
                except Exception as e:
                    if "SUBREDDIT_ALREADY_FAVORITED" in str(e):
                        return (name, "already_favorited", None)
                    else:
                        raise e
                
            except Exception as e:
                return (name, "failed", str(e))
        
        # Process subreddits in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_subreddit, name): name for name in subreddit_names}
            
            for future in as_completed(futures):
                name, status, error = future.result()
                if status == "successful":
                    results["successful"].append(name)
                elif status == "already_favorited":
                    results["already_favorited"].append(name)
                else:
                    results["failed"].append({"subreddit": name, "reason": error})
        
        # Add summary
        results["summary"] = f"{len(results['successful'])} favorited, " \
                            f"{len(results['already_favorited'])} already favorited, " \
                            f"{len(results['failed'])} failed"
        
        return results
    
    @classmethod
    def batch_unfavorite_subreddits(cls, reddit: praw.Reddit, 
                                  subreddit_names: List[str], 
                                  max_workers: int = 5) -> Dict[str, List[Any]]:
        """
        Unfavorite multiple subreddits in batch.
        
        Args:
            reddit: Authenticated Reddit instance
            subreddit_names: List of subreddit names to unfavorite
            max_workers: Maximum number of concurrent workers
            
        Returns:
            Dictionary with results categorized by status
        """
        if not reddit or not subreddit_names:
            return {
                "successful": [],
                "not_favorited": [],
                "failed": []
            }
        
        # De-duplicate subreddit names and convert to lowercase
        subreddit_names = list(set([name.lower() for name in subreddit_names if name]))
        
        # Check if the user is authenticated
        if not reddit.user.me():
            return {
                "successful": [],
                "not_favorited": [],
                "failed": [{"subreddit": name, "reason": "Not authenticated"} for name in subreddit_names]
            }
        
        # Results container
        results = {
            "successful": [],
            "not_favorited": [],
            "failed": []
        }
        
        # Function to process a single subreddit
        def process_subreddit(name: str) -> Tuple[str, str, Optional[str]]:
            """Process a single subreddit unfavorite. Returns (name, status, error_reason)"""
            try:
                # Get the subreddit
                subreddit = reddit.subreddit(name)
                
                # Check if subreddit exists
                # This will raise an exception if the subreddit doesn't exist
                display_name = subreddit.display_name
                
                # Unfavorite
                try:
                    subreddit.unfavorite()
                    return (name, "successful", None)
                except Exception as e:
                    if "SUBREDDIT_NOT_FAVORITED" in str(e):
                        return (name, "not_favorited", None)
                    else:
                        raise e
                
            except Exception as e:
                return (name, "failed", str(e))
        
        # Process subreddits in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_subreddit, name): name for name in subreddit_names}
            
            for future in as_completed(futures):
                name, status, error = future.result()
                if status == "successful":
                    results["successful"].append(name)
                elif status == "not_favorited":
                    results["not_favorited"].append(name)
                else:
                    results["failed"].append({"subreddit": name, "reason": error})
        
        # Add summary
        results["summary"] = f"{len(results['successful'])} unfavorited, " \
                            f"{len(results['not_favorited'])} not favorited, " \
                            f"{len(results['failed'])} failed"
        
        return results
