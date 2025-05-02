import unittest
import json
import logging
from unittest.mock import patch, MagicMock
from llm_response_scorer import (
    LLMResponseScorer,
    ScoreType,
    Score,
    ScoringResult
)

class TestLLMResponseScorer(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.scorer = LLMResponseScorer(logger=self.logger)
        
        # Test data
        self.valid_json_response = json.dumps({
            "field1": "value1",
            "field2": "value2",
            "field3": "value3"
        })
        
        self.invalid_json_response = "{ invalid json }"
        
        self.context = {
            "keywords": ["value1", "value2"],
            "topic": "test_topic"
        }
        
        self.expected_fields = ["field1", "field2", "field3"]
        
        self.reference_response = json.dumps({
            "field1": "value1",
            "field2": "value2",
            "field3": "value3"
        })
    
    def test_score_creation(self):
        """Test creation of score objects"""
        score = Score(
            score_type=ScoreType.RELEVANCE,
            value=0.8,
            weight=0.3,
            details={"test": "details"}
        )
        self.assertEqual(score.score_type, ScoreType.RELEVANCE)
        self.assertEqual(score.value, 0.8)
        self.assertEqual(score.weight, 0.3)
        self.assertEqual(score.details["test"], "details")
    
    def test_completeness_scoring(self):
        """Test completeness scoring"""
        # Test with all fields present
        score = self.scorer._calculate_completeness(
            self.valid_json_response,
            self.expected_fields
        )
        self.assertEqual(score.value, 1.0)
        self.assertEqual(len(score.details["missing_fields"]), 0)
        
        # Test with missing fields
        partial_response = json.dumps({"field1": "value1"})
        score = self.scorer._calculate_completeness(
            partial_response,
            self.expected_fields
        )
        self.assertLess(score.value, 1.0)
        self.assertEqual(len(score.details["missing_fields"]), 2)
        
        # Test with invalid JSON
        score = self.scorer._calculate_completeness(
            self.invalid_json_response,
            self.expected_fields
        )
        self.assertEqual(score.value, 0.0)
    
    def test_accuracy_scoring(self):
        """Test accuracy scoring"""
        # Test with identical responses
        score = self.scorer._calculate_accuracy(
            self.valid_json_response,
            self.reference_response
        )
        self.assertEqual(score.value, 1.0)
        
        # Test with different responses
        different_response = json.dumps({
            "field1": "different",
            "field2": "values",
            "field3": "here"
        })
        score = self.scorer._calculate_accuracy(
            different_response,
            self.reference_response
        )
        self.assertLess(score.value, 1.0)
    
    def test_confidence_scoring(self):
        """Test confidence scoring"""
        # Test with definitive language
        response = "This must be correct. It will always work."
        score = self.scorer._calculate_confidence(response)
        self.assertGreater(score.details["definitive_language"], 0)
        
        # Test with uncertain language
        response = "This may work. It could be correct."
        score = self.scorer._calculate_confidence(response)
        self.assertGreater(score.details["uncertain_language"], 0)
    
    def test_consistency_scoring(self):
        """Test consistency scoring"""
        # Test with no previous responses
        score = self.scorer._calculate_consistency(
            self.valid_json_response,
            []
        )
        self.assertEqual(score.value, 1.0)
        
        # Test with similar previous responses
        previous_responses = [
            json.dumps({"field1": "value1", "field2": "value2"}),
            json.dumps({"field1": "value1", "field2": "value2"})
        ]
        score = self.scorer._calculate_consistency(
            self.valid_json_response,
            previous_responses
        )
        self.assertGreater(score.value, 0.0)
    
    def test_full_scoring(self):
        """Test complete scoring process"""
        result = self.scorer.score_response(
            response=self.valid_json_response,
            context=self.context,
            expected_fields=self.expected_fields,
            reference=self.reference_response,
            previous_responses=[self.reference_response]
        )
        
        # Check overall structure
        self.assertIsInstance(result, ScoringResult)
        self.assertGreater(result.overall_score, 0.0)
        self.assertEqual(len(result.scores), 5)  # All score types
        
        # Check individual scores
        for score in result.scores:
            self.assertIsInstance(score, Score)
            self.assertGreaterEqual(score.value, 0.0)
            self.assertLessEqual(score.value, 1.0)
    
    def test_response_validation(self):
        """Test response validation"""
        # Test valid response
        schema = {
            "type": "object",
            "properties": {
                "field1": {"type": "string"},
                "field2": {"type": "string"},
                "field3": {"type": "string"}
            },
            "required": ["field1", "field2", "field3"]
        }
        
        is_valid, errors = self.scorer.validate_response(
            self.valid_json_response,
            schema
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Test invalid response
        is_valid, errors = self.scorer.validate_response(
            self.invalid_json_response,
            schema
        )
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_score_weights(self):
        """Test score weight configuration"""
        # Test default weights
        self.assertEqual(
            self.scorer.default_weights[ScoreType.RELEVANCE],
            0.3
        )
        self.assertEqual(
            self.scorer.default_weights[ScoreType.COMPLETENESS],
            0.3
        )
        
        # Test weight impact on overall score
        result1 = self.scorer.score_response(
            response=self.valid_json_response,
            context=self.context,
            expected_fields=self.expected_fields
        )
        
        # Create scorer with different weights
        scorer2 = LLMResponseScorer()
        scorer2.default_weights[ScoreType.RELEVANCE] = 0.5
        scorer2.default_weights[ScoreType.COMPLETENESS] = 0.1
        
        result2 = scorer2.score_response(
            response=self.valid_json_response,
            context=self.context,
            expected_fields=self.expected_fields
        )
        
        # Scores should be different due to different weights
        self.assertNotEqual(result1.overall_score, result2.overall_score)

if __name__ == "__main__":
    unittest.main() 