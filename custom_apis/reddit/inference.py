"""
Inference utilities for analyzing subreddit requirements and rules.
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Union
import praw
from praw.models import Submission, Subreddit
from datetime import datetime, timedelta
from .content_parser import ContentParser


class SubredditAnalyzer:
    """Analyze subreddit to infer posting requirements and rules."""
    
    @classmethod
    def analyze_subreddit_requirements(cls, subreddit: Subreddit, 
                                     analysis_depth: str = "standard") -> Dict[str, Any]:
        """
        Analyze subreddit to infer posting requirements.
        
        Args:
            subreddit: Subreddit object
            analysis_depth: Analysis depth ('basic', 'standard', or 'deep')
            
        Returns:
            Dictionary with analysis results
        """
        # Initialize results
        results = {
            "subreddit": subreddit.display_name,
            "requires_approval": {"value": False, "confidence": 0.0},
            "requires_verification": {"value": False, "confidence": 0.0},
            "requires_flair": {"value": False, "confidence": 0.0},
            "karma_requirement": {"value": None, "type": "", "confidence": 0.0},
            "account_age": {"value": None, "unit": "", "confidence": 0.0},
            "posting_rate_limit": {"value": None, "period": "", "confidence": 0.0},
            "analysis_methods": []
        }
        
        # Get all rules content
        rules_content = cls._get_combined_rules_content(subreddit)
        if rules_content:
            # Analyze rules
            rule_analysis = ContentParser.analyze_subreddit_rules(rules_content)
            results.update(rule_analysis)
            results["analysis_methods"].append("rule_parsing")
        
        # Basic analysis is complete at this point
        if analysis_depth == "basic":
            return results
        
        # Standard and deep analysis includes looking at wiki and pinned posts
        if analysis_depth in ["standard", "deep"]:
            # Check wiki for posting guidelines
            try:
                wiki_content = cls._get_wiki_content(subreddit)
                if wiki_content:
                    wiki_analysis = ContentParser.analyze_subreddit_rules(wiki_content)
                    cls._merge_analysis_results(results, wiki_analysis, weight=0.7)
                    results["analysis_methods"].append("wiki_analysis")
            except Exception as e:
                print(f"Error analyzing wiki: {str(e)}")
            
            # Check pinned posts
            try:
                pinned_content = cls._get_pinned_posts_content(subreddit)
                if pinned_content:
                    pinned_analysis = ContentParser.analyze_subreddit_rules(pinned_content)
                    cls._merge_analysis_results(results, pinned_analysis, weight=0.8)
                    results["analysis_methods"].append("pinned_post_analysis")
            except Exception as e:
                print(f"Error analyzing pinned posts: {str(e)}")
        
        # Deep analysis adds more methods
        if analysis_depth == "deep":
            # Analyze recent posts for flair usage
            try:
                flair_required, flair_confidence = cls._analyze_flair_usage(subreddit)
                
                # Only update if confidence is higher
                if flair_confidence > results["requires_flair"]["confidence"]:
                    results["requires_flair"]["value"] = flair_required
                    results["requires_flair"]["confidence"] = flair_confidence
                    results["analysis_methods"].append("flair_usage_analysis")
            except Exception as e:
                print(f"Error analyzing flair usage: {str(e)}")
            
            # Analyze mod comments for requirements
            try:
                mod_requirements = cls._analyze_mod_comments(subreddit)
                if mod_requirements:
                    cls._merge_analysis_results(results, mod_requirements, weight=0.9)
                    results["analysis_methods"].append("moderator_comment_analysis")
            except Exception as e:
                print(f"Error analyzing mod comments: {str(e)}")
                
            # Analyze automod behavior
            try:
                automod_requirements = cls._analyze_automod_behavior(subreddit)
                if automod_requirements:
                    cls._merge_analysis_results(results, automod_requirements, weight=0.85)
                    results["analysis_methods"].append("automod_behavior_analysis")
            except Exception as e:
                print(f"Error analyzing automod behavior: {str(e)}")
            
            # Analyze posting frequency per user
            try:
                rate_limit, rate_period, rate_confidence = cls._analyze_posting_frequency(subreddit)
                if rate_confidence > results["posting_rate_limit"]["confidence"]:
                    results["posting_rate_limit"]["value"] = rate_limit
                    results["posting_rate_limit"]["period"] = rate_period
                    results["posting_rate_limit"]["confidence"] = rate_confidence
                    results["analysis_methods"].append("posting_frequency_analysis")
            except Exception as e:
                print(f"Error analyzing posting frequency: {str(e)}")
        
        # Update available flairs
        try:
            results["available_flairs"] = cls._get_available_flairs(subreddit)
        except Exception as e:
            results["available_flairs"] = []
            print(f"Error getting available flairs: {str(e)}")
        
        return results
    
    @staticmethod
    def _get_combined_rules_content(subreddit: Subreddit) -> str:
        """Get combined rules content from a subreddit."""
        combined_content = ""
        
        try:
            # Get rules
            for rule in subreddit.rules:
                combined_content += f"Rule: {rule.short_name}\n"
                combined_content += f"Description: {rule.description}\n"
                combined_content += f"Violation Reason: {rule.violation_reason}\n\n"
            
            # Add subreddit description
            combined_content += f"\nSubreddit Description:\n{subreddit.description}\n\n"
            
            # Add public description
            combined_content += f"\nPublic Description:\n{subreddit.public_description}\n\n"
            
        except Exception as e:
            print(f"Error getting rules content: {str(e)}")
        
        return combined_content
    
    @staticmethod
    def _get_wiki_content(subreddit: Subreddit) -> str:
        """Get content from subreddit wiki pages related to posting rules."""
        combined_content = ""
        
        try:
            # Common wiki pages with posting guidelines
            wiki_pages = ["posting", "posting_guidelines", "guidelines", "rules", "faq", "submission", "submissions"]
            
            for page_name in wiki_pages:
                try:
                    wiki_page = subreddit.wiki[page_name]
                    combined_content += f"\nWiki Page {page_name}:\n{wiki_page.content_md}\n\n"
                except:
                    # Skip pages that don't exist
                    pass
        except Exception as e:
            print(f"Error getting wiki content: {str(e)}")
        
        return combined_content
    
    @staticmethod
    def _get_pinned_posts_content(subreddit: Subreddit) -> str:
        """Get content from pinned posts that might contain rules."""
        combined_content = ""
        
        try:
            # Get stickied (pinned) posts
            for i in range(1, 3):  # Reddit allows up to 2 stickied posts
                try:
                    sticky = subreddit.sticky(number=i)
                    combined_content += f"\nPinned Post {i} Title: {sticky.title}\n"
                    if hasattr(sticky, 'selftext'):
                        combined_content += f"Content: {sticky.selftext}\n\n"
                except:
                    # No more stickies or error getting sticky
                    break
        except Exception as e:
            print(f"Error getting pinned posts: {str(e)}")
        
        return combined_content
    
    @staticmethod
    def _analyze_flair_usage(subreddit: Subreddit) -> Tuple[bool, float]:
        """
        Analyze recent posts to determine if flair is required.
        
        Returns:
            Tuple of (flair_required, confidence)
        """
        try:
            # Get recent posts
            posts_with_flair = 0
            total_posts = 0
            
            for post in subreddit.new(limit=50):
                total_posts += 1
                if post.link_flair_text:
                    posts_with_flair += 1
            
            if total_posts == 0:
                return False, 0.0
                
            flair_ratio = posts_with_flair / total_posts
            
            # Determine if flair is likely required
            if flair_ratio > 0.9:
                return True, 0.85
            elif flair_ratio > 0.75:
                return True, 0.7
            elif flair_ratio > 0.5:
                return True, 0.5
            else:
                return False, 0.6
                
        except Exception as e:
            print(f"Error analyzing flair usage: {str(e)}")
            return False, 0.0
    
    @staticmethod
    def _analyze_mod_comments(subreddit: Subreddit) -> Optional[Dict[str, Any]]:
        """Analyze moderator comments on posts for requirement patterns."""
        try:
            # Get recent posts
            all_mod_comments = ""
            
            for post in subreddit.new(limit=25):
                post.comments.replace_more(limit=0)  # Only get top-level comments
                
                for comment in post.comments:
                    if comment.distinguished == 'moderator':
                        all_mod_comments += f"{comment.body}\n\n"
            
            if not all_mod_comments:
                return None
                
            # Analyze combined mod comments
            return ContentParser.analyze_subreddit_rules(all_mod_comments)
                
        except Exception as e:
            print(f"Error analyzing mod comments: {str(e)}")
            return None
    
    @staticmethod
    def _analyze_automod_behavior(subreddit: Subreddit) -> Optional[Dict[str, Any]]:
        """Analyze AutoModerator behavior for requirement patterns."""
        try:
            # Get recent posts
            all_automod_comments = ""
            
            for post in subreddit.new(limit=25):
                post.comments.replace_more(limit=0)  # Only get top-level comments
                
                for comment in post.comments:
                    if comment.author and comment.author.name == 'AutoModerator':
                        all_automod_comments += f"{comment.body}\n\n"
            
            if not all_automod_comments:
                return None
                
            # Analyze combined automod comments
            return ContentParser.analyze_subreddit_rules(all_automod_comments)
                
        except Exception as e:
            print(f"Error analyzing automod behavior: {str(e)}")
            return None
    
    @staticmethod
    def _analyze_posting_frequency(subreddit: Subreddit) -> Tuple[Optional[int], str, float]:
        """
        Analyze posting frequency per user to estimate rate limits.
        
        Returns:
            Tuple of (posts_per_period, period, confidence)
        """
        try:
            # Get recent posts
            posts_by_author = {}
            
            for post in subreddit.new(limit=100):
                if post.author:
                    author_name = post.author.name
                    created = datetime.fromtimestamp(post.created_utc)
                    
                    if author_name not in posts_by_author:
                        posts_by_author[author_name] = []
                        
                    posts_by_author[author_name].append(created)
            
            # Analyze intervals for frequent posters
            min_intervals = []
            
            for author, timestamps in posts_by_author.items():
                if len(timestamps) < 2:
                    continue
                    
                # Sort timestamps
                timestamps.sort()
                
                # Calculate intervals in hours
                intervals = [(timestamps[i] - timestamps[i-1]).total_seconds() / 3600 
                             for i in range(1, len(timestamps))]
                
                if intervals:
                    min_intervals.append(min(intervals))
            
            if not min_intervals:
                return None, "", 0.0
                
            # Get median of minimum intervals
            min_intervals.sort()
            median_interval = min_intervals[len(min_intervals) // 2]
            
            # Convert to posts per period
            if median_interval < 1:
                # Less than an hour - probably no limit
                return None, "", 0.0
            elif median_interval < 24:
                # Less than a day - posts per day
                posts_per_day = int(24 / median_interval)
                return posts_per_day, "day", 0.6
            elif median_interval < 168:
                # Less than a week - posts per week
                posts_per_week = int(168 / median_interval)
                return posts_per_week, "week", 0.6
            else:
                # More than a week - posts per month
                posts_per_month = int(720 / median_interval)
                return posts_per_month, "month", 0.5
                
        except Exception as e:
            print(f"Error analyzing posting frequency: {str(e)}")
            return None, "", 0.0
    
    @staticmethod
    def _get_available_flairs(subreddit: Subreddit) -> List[Dict[str, Any]]:
        """Get list of available post flairs."""
        flairs = []
        try:
            for template in subreddit.flair.link_templates:
                flairs.append({
                    "id": template.get("id", ""),
                    "text": template.get("text", ""),
                    "background_color": template.get("background_color", ""),
                    "text_color": template.get("text_color", ""),
                    "type": template.get("type", ""),
                    "is_required": template.get("text_editable", False) == False
                })
        except Exception as e:
            print(f"Error getting available flairs: {str(e)}")
        
        return flairs
    
    @staticmethod
    def _merge_analysis_results(target: Dict[str, Any], source: Dict[str, Any], weight: float = 0.5) -> None:
        """Merge analysis results with weighting."""
        # Skip if source is None
        if not source:
            return
            
        # Process boolean attributes with confidence
        for key in ["requires_approval", "requires_verification", "requires_flair"]:
            if key in source and key in target:
                # If source has higher confidence * weight
                if source[key]["confidence"] * weight > target[key]["confidence"]:
                    target[key]["value"] = source[key]["value"]
                    target[key]["confidence"] = source[key]["confidence"] * weight
        
        # Process structured attributes
        for key in ["karma_requirement", "account_age", "posting_rate_limit"]:
            if key in source and key in target:
                # If source has a value and higher confidence * weight
                if source[key]["value"] is not None and source[key]["confidence"] * weight > target[key]["confidence"]:
                    target[key]["value"] = source[key]["value"]
                    
                    # Copy type/unit/period
                    if "type" in source[key]:
                        target[key]["type"] = source[key]["type"]
                    if "unit" in source[key]:
                        target[key]["unit"] = source[key]["unit"]
                    if "period" in source[key]:
                        target[key]["period"] = source[key]["period"]
                        
                    target[key]["confidence"] = source[key]["confidence"] * weight
