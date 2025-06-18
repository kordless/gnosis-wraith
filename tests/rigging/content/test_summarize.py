"""
Content Summarization Tests
"""

import pytest
import sys
from pathlib import Path
from typing import Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.test_base import BaseAPITest


class TestSummarizeEndpoint(BaseAPITest):
    """Test /v2/summarize endpoint for content summarization"""
    
    def test_basic_summarization(self):
        """Test basic content summarization"""
        
        llm_config = self.get_llm_config("anthropic")
        
        content = """
        Artificial intelligence has made tremendous strides in recent years, transforming industries
        and reshaping how we interact with technology. Machine learning algorithms now power
        recommendation systems on streaming platforms, helping billions of users discover content
        tailored to their preferences. In healthcare, AI assists doctors in diagnosing diseases
        from medical images with accuracy that rivals human specialists. The automotive industry
        has invested heavily in self-driving technology, with companies like Tesla, Waymo, and
        Cruise testing autonomous vehicles on public roads. Natural language processing has
        enabled chatbots and virtual assistants to understand and respond to human queries with
        increasing sophistication. However, these advances come with challenges. Concerns about
        job displacement, algorithmic bias, and privacy have prompted calls for regulation and
        ethical guidelines. The concentration of AI capabilities in a few large tech companies
        raises questions about market competition and access to these powerful tools. As AI
        continues to evolve, society must balance innovation with responsibility, ensuring that
        these technologies benefit humanity while minimizing potential harms.
        """
        
        response = self.make_request("POST", "/summarize", json={
            "content": content,
            "summary_type": "medium",
            "summary_length": "medium",
            **llm_config
        })
        
        data = self.assert_success_response(response)
        
        # Should have summary
        assert "summary" in data
        summary = data["summary"]
        
        # Validate summary properties
        assert isinstance(summary, str)
        assert len(summary) > 50  # Not too short
        assert len(summary) < len(content)  # Shorter than original
        
        # Should mention key concepts
        summary_lower = summary.lower()
        key_concepts = ["ai", "artificial intelligence", "machine learning", "challenges", "technology"]
        assert any(concept in summary_lower for concept in key_concepts)
        
        # Check metadata
        if "metadata" in data:
            metadata = data["metadata"]
            assert "original_words" in metadata
            assert "summary_words" in metadata
            assert metadata["summary_words"] < metadata["original_words"]
            
            if "compression_ratio" in metadata:
                assert 0 < metadata["compression_ratio"] < 100
    
    def test_summary_lengths(self):
        """Test different summary lengths"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        Climate change is one of the most pressing challenges facing humanity. Global temperatures
        have risen by approximately 1.1 degrees Celsius since the pre-industrial era, primarily
        due to human activities such as burning fossil fuels, deforestation, and industrial
        processes. The consequences are already evident: melting ice caps, rising sea levels,
        more frequent and severe weather events, disruptions to ecosystems, and threats to food
        security. Scientists warn that limiting warming to 1.5 degrees Celsius is crucial to
        avoid catastrophic impacts. Achieving this goal requires rapid, unprecedented changes
        in energy systems, transportation, agriculture, and urban planning. Many countries have
        pledged to achieve net-zero emissions by 2050, but current policies fall short of these
        commitments. Renewable energy technologies like solar and wind have become increasingly
        cost-competitive, offering hope for a clean energy transition. Individual actions, such
        as reducing energy consumption and supporting sustainable practices, also play a role.
        """
        
        lengths = ["brief", "short", "medium", "long"]
        summaries = {}
        
        for length in lengths:
            response = self.make_request("POST", "/summarize", json={
                "content": content,
                "summary_length": length,
                **llm_config
            })
            
            data = self.assert_success_response(response)
            summaries[length] = data["summary"]
        
        # Verify length progression
        assert len(summaries["brief"]) < len(summaries["short"])
        assert len(summaries["short"]) < len(summaries["medium"])
        assert len(summaries["medium"]) < len(summaries["long"])
        
        # Brief should be 1-2 sentences
        assert summaries["brief"].count('.') <= 3
        
        # All should mention climate change
        for summary in summaries.values():
            assert "climate" in summary.lower() or "warming" in summary.lower()
    
    def test_summary_types(self):
        """Test different summary types"""
        
        llm_config = self.get_llm_config("anthropic")
        
        content = """
        The research study examined the effects of a new drug treatment on patients with
        type 2 diabetes. The randomized controlled trial included 500 participants aged
        40-65 with diagnosed diabetes for at least 2 years. Participants were randomly
        assigned to receive either the new drug or a placebo for 12 weeks. The primary
        outcome measure was reduction in HbA1c levels. Secondary outcomes included
        changes in fasting glucose, body weight, and reported side effects. Results
        showed that the treatment group experienced a mean reduction of 0.8% in HbA1c
        compared to 0.2% in the placebo group (p<0.001). Fasting glucose decreased by
        an average of 25 mg/dL in the treatment group versus 5 mg/dL in placebo.
        No serious adverse events were reported. The study concludes that the new drug
        shows promise for improving glycemic control in type 2 diabetes patients.
        """
        
        # Executive summary
        exec_response = self.make_request("POST", "/summarize", json={
            "content": content,
            "summary_type": "executive",
            **llm_config,
            "options": {
                "focus": ["key_findings", "implications"],
                "tone": "professional"
            }
        })
        
        exec_data = self.assert_success_response(exec_response)
        exec_summary = exec_data["summary"]
        
        # Technical summary
        tech_response = self.make_request("POST", "/summarize", json={
            "content": content,
            "summary_type": "technical",
            **llm_config,
            "options": {
                "preserve_technical_terms": True,
                "include_specifications": True
            }
        })
        
        tech_data = self.assert_success_response(tech_response)
        tech_summary = tech_data["summary"]
        
        # Bullet points
        bullet_response = self.make_request("POST", "/summarize", json={
            "content": content,
            "summary_type": "bullets",
            **llm_config,
            "options": {
                "max_bullets": 5
            }
        })
        
        bullet_data = self.assert_success_response(bullet_response)
        bullet_summary = bullet_data["summary"]
        
        # Validate different formats
        assert "•" in bullet_summary or "-" in bullet_summary or "*" in bullet_summary
        assert "HbA1c" in tech_summary  # Technical terms preserved
        assert len(exec_summary) > 50  # Executive summary substantial
    
    def test_abstract_summary(self):
        """Test abstract-style summary"""
        
        llm_config = self.get_llm_config("openai")
        
        research_content = """
        This study investigates the impact of remote work on employee productivity and well-being
        during the COVID-19 pandemic. We surveyed 2,000 employees across various industries who
        transitioned to remote work in March 2020. Data was collected through online questionnaires
        at three time points: initial transition (March 2020), six months later (September 2020),
        and one year later (March 2021). We measured productivity using self-reported metrics and
        manager evaluations, while well-being was assessed using validated psychological scales.
        
        Our findings reveal a complex picture. Initially, 65% of employees reported decreased
        productivity, citing challenges with home workspace setup, technology issues, and blurred
        work-life boundaries. However, by the one-year mark, 78% reported equal or higher
        productivity compared to pre-pandemic levels. Employees who received adequate technological
        support and had dedicated home office spaces showed the greatest improvements.
        
        Well-being outcomes varied significantly. While 45% reported improved work-life balance
        and reduced commute stress, 38% experienced increased feelings of isolation and difficulty
        disconnecting from work. Mental health support and regular virtual team interactions were
        identified as key factors in maintaining employee well-being.
        
        The study concludes that successful remote work implementation requires intentional
        organizational support, clear boundaries, and investment in both technology and employee
        well-being programs. These findings have important implications for the future of work
        as many organizations consider permanent flexible work arrangements.
        """
        
        response = self.make_request("POST", "/summarize", json={
            "content": research_content,
            "summary_type": "abstract",
            **llm_config,
            "options": {
                "structure": ["objective", "methods", "results", "conclusion"],
                "max_words": 250
            }
        })
        
        data = self.assert_success_response(response)
        abstract = data["summary"]
        
        # Should have abstract structure
        abstract_lower = abstract.lower()
        assert any(term in abstract_lower for term in ["objective", "study", "investigate", "research"])
        assert any(term in abstract_lower for term in ["method", "survey", "data", "collected"])
        assert any(term in abstract_lower for term in ["result", "finding", "showed", "revealed"])
        assert any(term in abstract_lower for term in ["conclusion", "conclude", "implication"])
        
        # Should be concise
        word_count = len(abstract.split())
        assert word_count <= 300  # Allow some flexibility
    
    def test_key_points_extraction(self):
        """Test extraction of key points during summarization"""
        
        llm_config = self.get_llm_config("anthropic")
        
        content = """
        The new software update brings several important features:
        
        1. Enhanced Security: Implementation of two-factor authentication and end-to-end
        encryption for all user communications.
        
        2. Performance Improvements: 40% faster load times and reduced memory usage by
        optimizing the codebase and implementing lazy loading.
        
        3. User Interface Redesign: A modern, intuitive interface with dark mode support
        and customizable themes.
        
        4. Integration Capabilities: New APIs allowing seamless integration with popular
        third-party services including Slack, Teams, and Google Workspace.
        
        5. Accessibility Features: Improved screen reader support, keyboard navigation,
        and compliance with WCAG 2.1 guidelines.
        
        The update is available immediately for all users and includes comprehensive
        documentation and migration guides.
        """
        
        response = self.make_request("POST", "/summarize", json={
            "content": content,
            "summary_type": "medium",
            **llm_config,
            "options": {
                "preserve_key_points": True
            }
        })
        
        data = self.assert_success_response(response)
        
        # Check if key points are preserved
        if "metadata" in data and "key_points" in data["metadata"]:
            key_points = data["metadata"]["key_points"]
            assert isinstance(key_points, list)
            assert len(key_points) >= 3  # Should extract main features
            
            # Check if main features are mentioned
            points_text = " ".join(key_points).lower()
            assert any(term in points_text for term in ["security", "authentication", "encryption"])
            assert any(term in points_text for term in ["performance", "faster", "40%"])
            assert any(term in points_text for term in ["interface", "ui", "dark mode"])
    
    def test_style_options(self):
        """Test different summary styles"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        Our company has achieved remarkable growth this quarter. Revenue increased by 25%
        year-over-year, reaching $50 million. Customer acquisition costs decreased by 15%
        while retention rates improved to 95%. The product team launched three major features
        that directly addressed customer feedback. Our engineering team reduced system downtime
        by 40% through infrastructure improvements. The sales team exceeded targets in all
        regions, with particularly strong performance in the Asian market. Looking ahead,
        we plan to expand our team by 30% and enter two new markets in Q3.
        """
        
        # Professional style
        prof_response = self.make_request("POST", "/summarize", json={
            "content": content,
            "summary_type": "executive",
            **llm_config,
            "options": {
                "style": "professional",
                "tone": "formal"
            }
        })
        
        # Conversational style
        conv_response = self.make_request("POST", "/summarize", json={
            "content": content,
            "summary_type": "medium",
            **llm_config,
            "options": {
                "style": "conversational",
                "tone": "friendly"
            }
        })
        
        prof_data = self.assert_success_response(prof_response)
        conv_data = self.assert_success_response(conv_response)
        
        # Both should capture key information
        for summary in [prof_data["summary"], conv_data["summary"]]:
            summary_lower = summary.lower()
            assert any(term in summary_lower for term in ["growth", "revenue", "25%", "increase"])
            assert any(term in summary_lower for term in ["customer", "retention", "95%"])
    
    def test_readability_score(self):
        """Test readability scoring of summaries"""
        
        llm_config = self.get_llm_config("anthropic")
        
        technical_content = """
        The implementation utilizes a microservices architecture with containerized applications
        orchestrated by Kubernetes. Each service communicates via gRPC with Protocol Buffers
        for serialization. The data layer employs a combination of PostgreSQL for transactional
        data and Cassandra for time-series metrics. Redis provides caching capabilities with
        a TTL-based eviction policy. The API gateway implements rate limiting using token
        bucket algorithms and handles authentication through JWT tokens with RSA-256 signing.
        Monitoring is achieved through Prometheus metrics exported to Grafana dashboards,
        with distributed tracing via OpenTelemetry. The CI/CD pipeline uses GitLab with
        automated testing including unit tests, integration tests, and performance benchmarks.
        """
        
        response = self.make_request("POST", "/summarize", json={
            "content": technical_content,
            "summary_type": "technical",
            **llm_config,
            "options": {
                "target_audience": "technical",
                "preserve_technical_terms": True
            }
        })
        
        data = self.assert_success_response(response)
        
        # Check readability metadata
        if "metadata" in data and "readability_score" in data["metadata"]:
            score = data["metadata"]["readability_score"]
            assert isinstance(score, (int, float))
            assert score > 0  # Should have some complexity due to technical terms


class TestSummarizeErrorHandling(BaseAPITest):
    """Test error handling for summarize endpoint"""
    
    def test_missing_content(self):
        """Test summarization without content"""
        
        llm_config = self.get_llm_config("anthropic")
        
        response = self.make_request("POST", "/summarize", json={
            "summary_type": "medium",
            **llm_config
        })
        
        assert response.status_code == 400
    
    def test_empty_content(self):
        """Test summarization of empty content"""
        
        llm_config = self.get_llm_config("openai")
        
        response = self.make_request("POST", "/summarize", json={
            "content": "",
            "summary_type": "brief",
            **llm_config
        })
        
        assert response.status_code == 400
    
    def test_content_too_short(self):
        """Test summarization of very short content"""
        
        llm_config = self.get_llm_config("anthropic")
        
        response = self.make_request("POST", "/summarize", json={
            "content": "This is a short sentence.",
            "summary_type": "long",  # Requesting long summary of short content
            **llm_config
        })
        
        # Should handle gracefully
        if response.status_code == 200:
            data = response.json()
            # Summary might be same as original or slightly modified
            assert len(data["summary"]) > 0
    
    def test_invalid_summary_type(self):
        """Test with invalid summary type"""
        
        llm_config = self.get_llm_config("openai")
        
        response = self.make_request("POST", "/summarize", json={
            "content": "Test content for summarization.",
            "summary_type": "invalid_type",
            **llm_config
        })
        
        # Should either use default or error
        assert response.status_code in [200, 400]
    
    def test_contradictory_options(self):
        """Test with contradictory options"""
        
        llm_config = self.get_llm_config("anthropic")
        
        response = self.make_request("POST", "/summarize", json={
            "content": "A paragraph of text that needs summarization for testing purposes.",
            "summary_type": "bullets",
            "summary_length": "brief",  # Brief bullets might be contradictory
            **llm_config,
            "options": {
                "max_bullets": 10,  # But asking for 10 bullets
                "style": "technical",
                "tone": "casual"  # Technical but casual
            }
        })
        
        # Should handle gracefully
        if response.status_code == 200:
            data = response.json()
            assert "summary" in data


class TestSummarizeEdgeCases(BaseAPITest):
    """Test edge cases for summarize endpoint"""
    
    def test_code_heavy_content(self):
        """Test summarization of code-heavy content"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        Here's how to implement a binary search tree in Python:
        
        ```python
        class Node:
            def __init__(self, value):
                self.value = value
                self.left = None
                self.right = None
        
        class BinarySearchTree:
            def __init__(self):
                self.root = None
            
            def insert(self, value):
                if not self.root:
                    self.root = Node(value)
                else:
                    self._insert_recursive(self.root, value)
            
            def _insert_recursive(self, node, value):
                if value < node.value:
                    if node.left is None:
                        node.left = Node(value)
                    else:
                        self._insert_recursive(node.left, value)
                else:
                    if node.right is None:
                        node.right = Node(value)
                    else:
                        self._insert_recursive(node.right, value)
        ```
        
        This implementation provides O(log n) average case for insertion and search operations.
        """
        
        response = self.make_request("POST", "/summarize", json={
            "content": content,
            "summary_type": "technical",
            **llm_config,
            "options": {
                "preserve_code": True
            }
        })
        
        data = self.assert_success_response(response)
        summary = data["summary"]
        
        # Should mention key concepts
        summary_lower = summary.lower()
        assert any(term in summary_lower for term in ["binary search tree", "bst", "tree", "implementation"])
        assert any(term in summary_lower for term in ["python", "insert", "node"])
    
    def test_multilingual_content(self):
        """Test summarization of multilingual content"""
        
        llm_config = self.get_llm_config("anthropic")
        
        content = """
        This document contains information in multiple languages.
        
        English: Artificial Intelligence is transforming industries worldwide.
        
        Spanish: La inteligencia artificial está transformando industrias en todo el mundo.
        
        French: L'intelligence artificielle transforme les industries du monde entier.
        
        German: Künstliche Intelligenz verändert Branchen weltweit.
        
        All these statements convey the same message about AI's global impact.
        """
        
        response = self.make_request("POST", "/summarize", json={
            "content": content,
            "summary_type": "brief",
            **llm_config,
            "options": {
                "output_language": "en"  # Summarize in English
            }
        })
        
        data = self.assert_success_response(response)
        summary = data["summary"]
        
        # Should capture the main idea
        assert "AI" in summary or "artificial intelligence" in summary.lower()
        assert "transform" in summary.lower() or "impact" in summary.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])