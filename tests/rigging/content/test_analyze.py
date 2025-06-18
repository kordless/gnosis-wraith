"""
Content Analysis Tests
"""

import pytest
import sys
import json
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.test_base import BaseAPITest


class TestAnalyzeEndpoint(BaseAPITest):
    """Test /v2/analyze endpoint for content analysis"""
    
    def test_basic_analysis(self):
        """Test basic content analysis"""
        
        llm_config = self.get_llm_config("anthropic")
        
        content = """
        Apple Inc. announced record quarterly revenue of $123.9 billion, up 2 percent year over year.
        CEO Tim Cook attributed the growth to strong iPhone 15 sales and expanding services revenue.
        The company also revealed plans to invest heavily in AI research, competing directly with
        Microsoft and Google in the enterprise AI market.
        """
        
        response = self.make_request("POST", "/analyze", json={
            "content": content,
            "analysis_type": "comprehensive",
            **llm_config
        })
        
        data = self.assert_success_response(response)
        
        # Should have analysis results
        assert "analysis" in data
        analysis = data["analysis"]
        
        # Check for expected analysis components
        assert "entities" in analysis
        assert "sentiment" in analysis
        
        # Validate entities
        entities = analysis["entities"]
        assert isinstance(entities, list)
        assert len(entities) > 0
        
        # Should identify Apple Inc.
        org_entities = [e for e in entities if e.get("type") == "ORGANIZATION"]
        assert any("Apple" in e.get("text", "") for e in org_entities)
        
        # Should identify Tim Cook
        person_entities = [e for e in entities if e.get("type") == "PERSON"]
        assert any("Tim Cook" in e.get("text", "") for e in person_entities)
        
        # Should identify money amount
        money_entities = [e for e in entities if e.get("type") == "MONEY"]
        assert any("123.9" in str(e.get("text", "")) for e in money_entities)
    
    def test_entity_extraction(self):
        """Test specific entity extraction"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        On January 15, 2025, Microsoft Corporation's CEO Satya Nadella announced a $10 billion
        investment in OpenAI. The partnership will focus on developing AGI technologies at their
        Seattle headquarters. Contact: press@microsoft.com or call +1-425-882-8080.
        """
        
        response = self.make_request("POST", "/analyze", json={
            "content": content,
            "analysis_type": "entities",
            **llm_config,
            "options": {
                "entity_types": ["PERSON", "ORGANIZATION", "DATE", "MONEY", "LOCATION", "EMAIL", "PHONE"],
                "include_metadata": True
            }
        })
        
        data = self.assert_success_response(response)
        entities = data["analysis"]["entities"]
        
        # Check each entity type
        entity_types = {e["type"] for e in entities}
        
        # Should find various entities
        assert "PERSON" in entity_types  # Satya Nadella
        assert "ORGANIZATION" in entity_types  # Microsoft, OpenAI
        assert "DATE" in entity_types  # January 15, 2025
        assert "MONEY" in entity_types  # $10 billion
        assert "LOCATION" in entity_types  # Seattle
        
        # Check confidence scores if included
        if entities and "confidence" in entities[0]:
            for entity in entities:
                assert 0 <= entity["confidence"] <= 1
    
    def test_sentiment_analysis(self):
        """Test sentiment analysis"""
        
        llm_config = self.get_llm_config("anthropic")
        
        # Positive sentiment
        positive_content = """
        This product is absolutely amazing! I love everything about it. The quality is superb,
        the customer service was fantastic, and it exceeded all my expectations. Highly recommend!
        """
        
        response = self.make_request("POST", "/analyze", json={
            "content": positive_content,
            "analysis_type": "sentiment",
            **llm_config,
            "options": {
                "granularity": "document"
            }
        })
        
        data = self.assert_success_response(response)
        sentiment = data["analysis"]["sentiment"]
        
        assert "overall" in sentiment
        assert sentiment["overall"] in ["positive", "very_positive"]
        assert "score" in sentiment
        assert sentiment["score"] > 0.5  # Positive score
        
        # Negative sentiment
        negative_content = """
        Terrible experience. The product broke after one day. Customer service was rude and unhelpful.
        Complete waste of money. Would not recommend to anyone.
        """
        
        response = self.make_request("POST", "/analyze", json={
            "content": negative_content,
            "analysis_type": "sentiment",
            **llm_config
        })
        
        data = self.assert_success_response(response)
        sentiment = data["analysis"]["sentiment"]
        
        assert sentiment["overall"] in ["negative", "very_negative"]
        assert sentiment["score"] < -0.5  # Negative score
    
    def test_aspect_sentiment(self):
        """Test aspect-based sentiment analysis"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        The laptop has excellent performance and the screen quality is outstanding.
        However, the battery life is disappointing and it runs quite hot. The keyboard
        feels cheap but the trackpad is responsive. Overall mixed feelings about this purchase.
        """
        
        response = self.make_request("POST", "/analyze", json={
            "content": content,
            "analysis_type": "sentiment",
            **llm_config,
            "options": {
                "granularity": "aspect",
                "aspects": ["performance", "battery", "build_quality", "display"]
            }
        })
        
        data = self.assert_success_response(response)
        sentiment = data["analysis"]["sentiment"]
        
        # Should have aspect sentiments
        if "aspects" in sentiment:
            aspects = sentiment["aspects"]
            
            # Performance should be positive
            if "performance" in aspects:
                assert aspects["performance"] in ["positive", "very_positive"]
            
            # Battery should be negative
            if "battery" in aspects:
                assert aspects["battery"] in ["negative", "very_negative"]
    
    def test_topic_analysis(self):
        """Test topic modeling and theme extraction"""
        
        llm_config = self.get_llm_config("anthropic")
        
        content = """
        The field of artificial intelligence has seen remarkable progress in recent years.
        Machine learning algorithms now power everything from recommendation systems to
        autonomous vehicles. Deep learning has revolutionized computer vision and natural
        language processing. However, concerns about AI ethics, bias in algorithms, and
        job displacement continue to grow. Researchers are working on explainable AI
        to address transparency issues. The future of AI likely involves a combination
        of technical advancement and careful regulation.
        """
        
        response = self.make_request("POST", "/analyze", json={
            "content": content,
            "analysis_type": "topics",
            **llm_config,
            "options": {
                "num_topics": 3,
                "include_keywords": True
            }
        })
        
        data = self.assert_success_response(response)
        
        # Should have topics/themes
        if "topics" in data["analysis"]:
            topics = data["analysis"]["topics"]
        elif "key_themes" in data["analysis"]:
            topics = data["analysis"]["key_themes"]
        else:
            topics = []
        
        assert len(topics) > 0
        
        # Check topic structure
        for topic in topics:
            assert "theme" in topic or "topic" in topic
            if "keywords" in topic:
                assert isinstance(topic["keywords"], list)
            if "relevance" in topic:
                assert 0 <= topic["relevance"] <= 1
    
    def test_classification(self):
        """Test content classification"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        The Federal Reserve announced a 0.25% interest rate cut today, marking the first
        reduction in over a year. This decision comes amid concerns about slowing economic
        growth and declining inflation. Stock markets responded positively, with the S&P 500
        gaining 1.2% in early trading.
        """
        
        response = self.make_request("POST", "/analyze", json={
            "content": content,
            "analysis_type": "comprehensive",
            **llm_config
        })
        
        data = self.assert_success_response(response)
        analysis = data["analysis"]
        
        # Should have classification
        if "classification" in analysis:
            classification = analysis["classification"]
            assert "primary" in classification
            
            # Should classify as business/finance
            primary = classification["primary"].lower()
            assert any(term in primary for term in ["business", "finance", "economic", "financial"])
            
            # May have confidence score
            if "confidence" in classification:
                assert 0 <= classification["confidence"] <= 1
    
    def test_summary_generation(self):
        """Test summary generation during analysis"""
        
        llm_config = self.get_llm_config("anthropic")
        
        long_content = """
        Climate change represents one of the most pressing challenges of our time. Global temperatures
        have risen by approximately 1.1 degrees Celsius since pre-industrial times, primarily due to
        human activities such as burning fossil fuels. The consequences are already visible: melting
        ice caps, rising sea levels, more frequent extreme weather events, and disruptions to ecosystems
        worldwide. Scientists warn that we must limit warming to 1.5 degrees Celsius to avoid the most
        catastrophic effects. This requires rapid, far-reaching changes in energy systems, transportation,
        buildings, and industry. Many countries have committed to net-zero emissions by 2050, but current
        policies fall short of these goals. Renewable energy technologies like solar and wind have become
        increasingly cost-competitive, offering hope for a clean energy transition. However, political will,
        public support, and massive investment are needed to achieve the necessary transformation.
        """
        
        response = self.make_request("POST", "/analyze", json={
            "content": long_content,
            "analysis_type": "comprehensive",
            **llm_config
        })
        
        data = self.assert_success_response(response)
        analysis = data["analysis"]
        
        # Should include a summary
        if "summary" in analysis:
            summary = analysis["summary"]
            assert isinstance(summary, str)
            assert len(summary) > 50  # Should be substantive
            assert len(summary) < len(long_content)  # Should be shorter than original
            
            # Summary should mention key points
            summary_lower = summary.lower()
            assert any(term in summary_lower for term in ["climate", "temperature", "emissions"])
    
    def test_metadata_extraction(self):
        """Test metadata extraction from content"""
        
        llm_config = self.get_llm_config("openai")
        
        content = "This is a short test. It has two sentences."
        
        response = self.make_request("POST", "/analyze", json={
            "content": content,
            "analysis_type": "comprehensive",
            **llm_config
        })
        
        data = self.assert_success_response(response)
        
        # Should have metadata
        if "metadata" in data:
            metadata = data["metadata"]
            
            # Check word count
            if "words" in metadata:
                assert metadata["words"] > 5
                assert metadata["words"] < 20
            
            # Check sentence count
            if "sentences" in metadata:
                assert metadata["sentences"] == 2
            
            # Check language
            if "language" in metadata:
                assert metadata["language"] == "en"


class TestAnalyzeWithDifferentProviders(BaseAPITest):
    """Test analysis with different LLM providers"""
    
    def test_provider_consistency(self):
        """Test that different providers give similar results"""
        
        content = """
        Tesla announced a 15% increase in vehicle deliveries for Q4 2024. 
        CEO Elon Musk credited strong demand in China and Europe.
        """
        
        providers = []
        if self.anthropic_token:
            providers.append(("anthropic", self.anthropic_token))
        if self.openai_token:
            providers.append(("openai", self.openai_token))
        
        if len(providers) < 2:
            pytest.skip("Need at least 2 LLM providers configured")
        
        results = {}
        
        for provider, token in providers:
            response = self.make_request("POST", "/analyze", json={
                "content": content,
                "analysis_type": "entities",
                "llm_provider": provider,
                "llm_token": token
            })
            
            data = self.assert_success_response(response)
            results[provider] = data["analysis"]["entities"]
        
        # Compare entity extraction
        # All providers should find Tesla and Elon Musk
        for provider, entities in results.items():
            entity_texts = [e.get("text", "").lower() for e in entities]
            assert any("tesla" in text for text in entity_texts)
            assert any("elon" in text or "musk" in text for text in entity_texts)


class TestAnalyzeErrorHandling(BaseAPITest):
    """Test error handling for analyze endpoint"""
    
    def test_missing_content(self):
        """Test analysis without content"""
        
        llm_config = self.get_llm_config("anthropic")
        
        response = self.make_request("POST", "/analyze", json={
            "analysis_type": "comprehensive",
            **llm_config
        })
        
        assert response.status_code == 400
    
    def test_empty_content(self):
        """Test analysis with empty content"""
        
        llm_config = self.get_llm_config("openai")
        
        response = self.make_request("POST", "/analyze", json={
            "content": "",
            "analysis_type": "entities",
            **llm_config
        })
        
        assert response.status_code == 400
    
    def test_content_too_large(self):
        """Test analysis with content exceeding limits"""
        
        llm_config = self.get_llm_config("anthropic")
        
        # Create very large content (over 5MB)
        huge_content = "This is a test sentence. " * 300000
        
        response = self.make_request("POST", "/analyze", json={
            "content": huge_content,
            "analysis_type": "sentiment",
            **llm_config
        })
        
        # Should reject
        assert response.status_code in [400, 413]
        
        if response.status_code == 413:
            self.assert_error_response(response, "CONTENT_TOO_LARGE")
    
    def test_invalid_analysis_type(self):
        """Test with invalid analysis type"""
        
        llm_config = self.get_llm_config("openai")
        
        response = self.make_request("POST", "/analyze", json={
            "content": "Test content",
            "analysis_type": "invalid_type",
            **llm_config
        })
        
        # Should either default to comprehensive or error
        assert response.status_code in [200, 400]
    
    def test_unsupported_language(self):
        """Test analysis with unsupported language"""
        
        llm_config = self.get_llm_config("anthropic")
        
        response = self.make_request("POST", "/analyze", json={
            "content": "This is English content",
            "analysis_type": "comprehensive",
            **llm_config,
            "options": {
                "language": "xyz"  # Invalid language code
            }
        })
        
        # Should either ignore or error
        assert response.status_code in [200, 400]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])