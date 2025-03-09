"""Sample text processing API for Createve.AI API Server."""

class TextAnalyzer:
    """Text analyzer for sentiment and statistics."""
    
    CATEGORY = "text"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for node."""
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
            },
            "optional": {
                "include_sentiment": ("BOOLEAN", {"default": True}),
                "include_statistics": ("BOOLEAN", {"default": True})
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("analysis_results",)
    FUNCTION = "analyze_text"
    
    def analyze_text(self, text, include_sentiment=True, include_statistics=True):
        """Analyze text for sentiment and statistics."""
        result = {}
        
        if include_statistics:
            # Basic statistics
            words = text.split()
            result["statistics"] = {
                "character_count": len(text),
                "word_count": len(words),
                "line_count": len(text.splitlines()),
                "average_word_length": sum(len(word) for word in words) / max(len(words), 1)
            }
        
        if include_sentiment:
            # Very basic sentiment analysis
            positive_words = ["good", "great", "excellent", "happy", "positive", "best", "love"]
            negative_words = ["bad", "awful", "terrible", "sad", "negative", "worst", "hate"]
            
            lowercase_text = text.lower()
            positive_count = sum(lowercase_text.count(word) for word in positive_words)
            negative_count = sum(lowercase_text.count(word) for word in negative_words)
            
            if positive_count > negative_count:
                sentiment = "positive"
            elif negative_count > positive_count:
                sentiment = "negative"
            else:
                sentiment = "neutral"
                
            result["sentiment"] = {
                "assessment": sentiment,
                "positive_word_count": positive_count,
                "negative_word_count": negative_count
            }
        
        return (result,)

class TextSummarizer:
    """Text summarizer using extraction-based methods."""
    
    CATEGORY = "text"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for node."""
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
                "summary_length": ("INTEGER", {"default": 3, "min": 1, "max": 10})
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("summary",)
    FUNCTION = "summarize_text"
    
    def summarize_text(self, text, summary_length=3):
        """Summarize text using extraction-based method."""
        # Simple extractive text summarization
        sentences = [s.strip() for s in text.replace('!', '.').replace('?', '.').split('.') if s.strip()]
        
        if not sentences:
            return ("No text to summarize.",)
            
        # Count word frequency
        words = text.lower().split()
        word_frequency = {}
        
        for word in words:
            if len(word) > 3:  # Ignore short words
                word_frequency[word] = word_frequency.get(word, 0) + 1
        
        # Score sentences
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            score = 0
            for word in sentence.lower().split():
                if word in word_frequency:
                    score += word_frequency[word]
            sentence_scores[i] = score
        
        # Get top sentences
        top_sentence_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:summary_length]
        top_sentence_indices.sort()  # Keep original order
        
        summary = '. '.join(sentences[i] for i in top_sentence_indices)
        if not summary.endswith('.'):
            summary += '.'
            
        return (summary,)

# Define mappings
NODE_CLASS_MAPPINGS = {
    "Text Analyzer": TextAnalyzer,
    "Text Summarizer": TextSummarizer
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Text Analyzer": "Text Analyzer",
    "Text Summarizer": "Text Summarizer"
}

API_SERVER_QUEUE_MODE = {
    TextSummarizer: True  # Only summarizer runs in queue mode as an example
}
