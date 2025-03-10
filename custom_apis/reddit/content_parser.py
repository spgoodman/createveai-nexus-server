"""
Content parsing and sanitization utilities for Reddit content.
"""

import re
import html
from typing import Dict, List, Any, Optional, Union, Tuple
from bs4 import BeautifulSoup
import html2text
import markdown
from markdown_it import MarkdownIt


class ContentParser:
    """Advanced content parsing for Reddit posts, comments, and subreddit descriptions."""
    
    # Patterns for common Reddit content
    SUBREDDIT_PATTERN = r'/?r/([a-zA-Z0-9_]+)'
    USER_PATTERN = r'/?u/([a-zA-Z0-9_-]+)'
    URL_PATTERN = r'https?://(?:www\.)?([^\s/$.?#].[^\s]*)'
    
    # Patterns for rule detection
    APPROVAL_PATTERNS = [
        r'(?i)require(?:s|d)?\s+(?:mod(?:erator)?)?\s*approval',
        r'(?i)(?:mod(?:erator)?)?\s*approval\s+(?:is\s+)?require(?:s|d)?',
        r'(?i)await(?:ing)?\s+approval',
        r'(?i)need\s+to\s+be\s+approved'
    ]
    
    VERIFICATION_PATTERNS = [
        r'(?i)verify|verification|verified',
        r'(?i)must\s+be\s+verified',
        r'(?i)verification\s+(?:is\s+)?required',
        r'(?i)verified\s+(?:users|members|accounts)\s+only'
    ]
    
    FLAIR_PATTERNS = [
        r'(?i)flair\s+(?:is\s+)?required',
        r'(?i)must\s+(?:have|include|add)\s+(?:a\s+)?flair',
        r'(?i)posts?\s+(?:must|should|need\s+to)\s+be\s+flaired'
    ]
    
    KARMA_PATTERNS = [
        r'(?i)(\d+)\s+(?:comment|post|combined)?\s*karma',
        r'(?i)karma\s+(?:requirement|minimum|threshold)\s*(?::|of)?\s*(\d+)',
        r'(?i)at\s+least\s+(\d+)\s+karma'
    ]
    
    AGE_PATTERNS = [
        r'(?i)account\s+(?:must\s+be\s+|at\s+least\s+|older\s+than\s+)(\d+)\s+(day|days|week|weeks|month|months|year|years)',
        r'(?i)(\d+)\s+(day|days|week|weeks|month|months|year|years)\s+old\s+account',
        r'(?i)minimum\s+account\s+age\s*(?::|of)?\s*(\d+)\s+(day|days|week|weeks|month|months)'
    ]
    
    RATE_LIMIT_PATTERNS = [
        r'(?i)(\d+)\s+posts?\s+(?:per|every|each|a)\s+(day|days|week|weeks|month|months)',
        r'(?i)limit\s+(?:of\s+)?(\d+)\s+posts?\s+(?:per|every|each|a)\s+(day|days|week|weeks|month|months)',
        r'(?i)(?:maximum|max|up\s+to)\s+(\d+)\s+posts?\s+(?:per|every|each|a)\s+(day|days|week|weeks|month|months)'
    ]
    
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
    def markdown_to_html(content: str) -> str:
        """Convert markdown to HTML."""
        if not content:
            return ""
        try:
            # First try with markdown-it for better Reddit compatibility
            md = MarkdownIt()
            return md.render(content)
        except Exception:
            # Fall back to regular markdown
            return markdown.markdown(content)
    
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
    def sanitize_content(cls, content: str, keep_markdown: bool = False, 
                        keep_links: bool = False, keep_subreddits: bool = False,
                        keep_users: bool = False) -> str:
        """
        Sanitize content with configurable options.
        
        Args:
            content: Text content to sanitize
            keep_markdown: Whether to retain markdown formatting
            keep_links: Whether to retain URLs
            keep_subreddits: Whether to retain r/subreddit references
            keep_users: Whether to retain u/user references
            
        Returns:
            Sanitized text
        """
        if not content:
            return ""
        
        # Remove HTML
        content = cls.strip_html(content)
        
        # Process based on flags
        if not keep_markdown:
            content = cls.convert_markdown(content)
            
        if not keep_links:
            # Replace URLs with simple markers
            content = re.sub(cls.URL_PATTERN, '[link]', content)
            
        if not keep_subreddits:
            # Replace subreddit references
            content = re.sub(cls.SUBREDDIT_PATTERN, '[subreddit]', content)
            
        if not keep_users:
            # Replace user references
            content = re.sub(cls.USER_PATTERN, '[user]', content)
        
        # Normalize text
        return cls.normalize_text(content)
    
    @classmethod
    def extract_subreddits(cls, content: str) -> List[str]:
        """Extract all subreddit references from content."""
        if not content:
            return []
        matches = re.findall(cls.SUBREDDIT_PATTERN, content)
        return list(set(matches))  # Remove duplicates
    
    @classmethod
    def extract_users(cls, content: str) -> List[str]:
        """Extract all user references from content."""
        if not content:
            return []
        matches = re.findall(cls.USER_PATTERN, content)
        return list(set(matches))  # Remove duplicates
    
    @classmethod
    def extract_urls(cls, content: str) -> List[str]:
        """Extract all URLs from content."""
        if not content:
            return []
        matches = re.findall(cls.URL_PATTERN, content)
        return list(set(matches))  # Remove duplicates
    
    @classmethod
    def check_requires_approval(cls, content: str) -> Tuple[bool, float]:
        """
        Check if subreddit rules suggest posts require approval.
        
        Returns:
            Tuple of (requires_approval, confidence_score 0-1)
        """
        if not content:
            return False, 0.0
            
        normalized_content = content.lower()
        matches = 0
        
        for pattern in cls.APPROVAL_PATTERNS:
            if re.search(pattern, normalized_content):
                matches += 1
                
        confidence = min(matches / len(cls.APPROVAL_PATTERNS), 1.0)
        requires_approval = confidence > 0.3
        
        return requires_approval, confidence
    
    @classmethod
    def check_requires_verification(cls, content: str) -> Tuple[bool, float]:
        """
        Check if subreddit rules suggest verification is required.
        
        Returns:
            Tuple of (requires_verification, confidence_score 0-1)
        """
        if not content:
            return False, 0.0
            
        normalized_content = content.lower()
        matches = 0
        
        for pattern in cls.VERIFICATION_PATTERNS:
            if re.search(pattern, normalized_content):
                matches += 1
                
        confidence = min(matches / len(cls.VERIFICATION_PATTERNS), 1.0)
        requires_verification = confidence > 0.3
        
        return requires_verification, confidence
    
    @classmethod
    def check_requires_flair(cls, content: str) -> Tuple[bool, float]:
        """
        Check if subreddit rules suggest posts require flair.
        
        Returns:
            Tuple of (requires_flair, confidence_score 0-1)
        """
        if not content:
            return False, 0.0
            
        normalized_content = content.lower()
        matches = 0
        
        for pattern in cls.FLAIR_PATTERNS:
            if re.search(pattern, normalized_content):
                matches += 1
                
        confidence = min(matches / len(cls.FLAIR_PATTERNS), 1.0)
        requires_flair = confidence > 0.3
        
        return requires_flair, confidence
    
    @classmethod
    def extract_karma_requirement(cls, content: str) -> Tuple[Optional[int], str, float]:
        """
        Extract karma requirement from rules.
        
        Returns:
            Tuple of (karma_amount, karma_type, confidence_score 0-1)
        """
        if not content:
            return None, "", 0.0
            
        normalized_content = content.lower()
        karma_amount = None
        karma_type = "combined"  # Default
        highest_confidence = 0.0
        
        for pattern in cls.KARMA_PATTERNS:
            matches = re.finditer(pattern, normalized_content)
            for match in matches:
                try:
                    amount = int(match.group(1))
                    # Look for karma type in surrounding text
                    surrounding = normalized_content[max(0, match.start() - 20):min(len(normalized_content), match.end() + 20)]
                    
                    if "comment" in surrounding and "post" not in surrounding:
                        k_type = "comment"
                    elif "post" in surrounding and "comment" not in surrounding:
                        k_type = "post"
                    else:
                        k_type = "combined"
                        
                    # Confidence based on clarity of the match
                    conf = 0.6 if amount > 0 else 0.3
                    if conf > highest_confidence:
                        karma_amount = amount
                        karma_type = k_type
                        highest_confidence = conf
                except:
                    pass
                    
        return karma_amount, karma_type, highest_confidence
    
    @classmethod
    def extract_account_age_requirement(cls, content: str) -> Tuple[Optional[int], str, float]:
        """
        Extract account age requirement from rules.
        
        Returns:
            Tuple of (age_amount, age_unit, confidence_score 0-1)
        """
        if not content:
            return None, "", 0.0
            
        normalized_content = content.lower()
        age_amount = None
        age_unit = "days"  # Default
        highest_confidence = 0.0
        
        for pattern in cls.AGE_PATTERNS:
            matches = re.finditer(pattern, normalized_content)
            for match in matches:
                try:
                    amount = int(match.group(1))
                    unit = match.group(2)
                    
                    # Standardize unit
                    if unit in ["day", "days"]:
                        std_unit = "days"
                    elif unit in ["week", "weeks"]:
                        std_unit = "weeks"
                    elif unit in ["month", "months"]:
                        std_unit = "months"
                    else:
                        std_unit = "days"
                        
                    # Confidence based on clarity of the match
                    conf = 0.7 if amount > 0 else 0.3
                    if conf > highest_confidence:
                        age_amount = amount
                        age_unit = std_unit
                        highest_confidence = conf
                except:
                    pass
                    
        return age_amount, age_unit, highest_confidence
    
    @classmethod
    def extract_posting_rate_limit(cls, content: str) -> Tuple[Optional[int], str, float]:
        """
        Extract posting rate limit from rules.
        
        Returns:
            Tuple of (posts_count, time_period, confidence_score 0-1)
        """
        if not content:
            return None, "", 0.0
            
        normalized_content = content.lower()
        posts_count = None
        time_period = "day"  # Default
        highest_confidence = 0.0
        
        for pattern in cls.RATE_LIMIT_PATTERNS:
            matches = re.finditer(pattern, normalized_content)
            for match in matches:
                try:
                    count = int(match.group(1))
                    period = match.group(2)
                    
                    # Standardize period
                    if period in ["day", "days"]:
                        std_period = "day"
                    elif period in ["week", "weeks"]:
                        std_period = "week"
                    elif period in ["month", "months"]:
                        std_period = "month"
                    else:
                        std_period = "day"
                        
                    # Confidence based on clarity of the match
                    conf = 0.7 if count > 0 else 0.3
                    if conf > highest_confidence:
                        posts_count = count
                        time_period = std_period
                        highest_confidence = conf
                except:
                    pass
                    
        return posts_count, time_period, highest_confidence
    
    @classmethod
    def analyze_subreddit_rules(cls, rules_content: str) -> Dict[str, Any]:
        """
        Analyze subreddit rules to extract posting requirements.
        
        Args:
            rules_content: Combined rules text content
            
        Returns:
            Dictionary with analysis results
        """
        if not rules_content:
            return {
                "requires_approval": {"value": False, "confidence": 0.0},
                "requires_verification": {"value": False, "confidence": 0.0},
                "requires_flair": {"value": False, "confidence": 0.0},
                "karma_requirement": {"value": None, "type": "", "confidence": 0.0},
                "account_age": {"value": None, "unit": "", "confidence": 0.0},
                "posting_rate_limit": {"value": None, "period": "", "confidence": 0.0}
            }
        
        # Analyze for approval requirement
        requires_approval, approval_confidence = cls.check_requires_approval(rules_content)
        
        # Analyze for verification requirement
        requires_verification, verification_confidence = cls.check_requires_verification(rules_content)
        
        # Analyze for flair requirement
        requires_flair, flair_confidence = cls.check_requires_flair(rules_content)
        
        # Extract karma requirement
        karma_amount, karma_type, karma_confidence = cls.extract_karma_requirement(rules_content)
        
        # Extract account age requirement
        age_amount, age_unit, age_confidence = cls.extract_account_age_requirement(rules_content)
        
        # Extract posting rate limit
        posts_count, time_period, rate_confidence = cls.extract_posting_rate_limit(rules_content)
        
        return {
            "requires_approval": {
                "value": requires_approval,
                "confidence": approval_confidence
            },
            "requires_verification": {
                "value": requires_verification,
                "confidence": verification_confidence
            },
            "requires_flair": {
                "value": requires_flair,
                "confidence": flair_confidence
            },
            "karma_requirement": {
                "value": karma_amount,
                "type": karma_type,
                "confidence": karma_confidence
            },
            "account_age": {
                "value": age_amount,
                "unit": age_unit,
                "confidence": age_confidence
            },
            "posting_rate_limit": {
                "value": posts_count,
                "period": time_period,
                "confidence": rate_confidence
            }
        }
