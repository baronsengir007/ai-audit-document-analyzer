import json
import unittest
from typing import Dict, List
from difflib import SequenceMatcher

class TestRequirementExtraction(unittest.TestCase):
    def setUp(self):
        """Load the extracted requirements for analysis."""
        with open('docs/sample_policy.md', 'r') as f:
            self.policy_content = f.read()
        
        # Run the extraction
        from test_extraction import extract_requirements_from_text
        self.requirements = extract_requirements_from_text(self.policy_content)
        
        # Load gold standard requirements if available
        try:
            with open('docs/gold_standard_requirements.json', 'r') as f:
                self.gold_standard = json.load(f)
        except FileNotFoundError:
            self.gold_standard = None
    
    def test_requirement_count(self):
        """Test if we extracted the correct number of requirements."""
        # Count actual requirements in the policy
        actual_requirements = sum(1 for line in self.policy_content.split('\n') 
                               if any(word in line.lower() for word in ['must', 'shall', 'required', 'mandatory']))
        
        print(f"\nActual requirements in policy: {actual_requirements}")
        print(f"Extracted requirements: {len(self.requirements)}")
        
        # More strict validation
        self.assertGreaterEqual(len(self.requirements), actual_requirements * 0.9,
                              "Extracted too few requirements")
        self.assertLessEqual(len(self.requirements), actual_requirements * 1.1,
                           "Extracted too many requirements")
    
    def test_requirement_structure(self):
        """Test the structure of extracted requirements."""
        required_fields = {'id', 'requirement_text', 'type', 'keywords', 'conditions', 'confidence'}
        
        for req in self.requirements:
            # Check all required fields are present
            self.assertTrue(all(field in req for field in required_fields),
                          f"Missing required fields in requirement: {req}")
            
            # Check field types
            self.assertIsInstance(req['id'], str, "ID should be a string")
            self.assertIsInstance(req['requirement_text'], str, "Requirement text should be a string")
            self.assertIn(req['type'], ['explicit', 'implicit'], "Type should be explicit or implicit")
            self.assertIsInstance(req['keywords'], list, "Keywords should be a list")
            self.assertIsInstance(req['conditions'], list, "Conditions should be a list")
            self.assertIsInstance(req['confidence'], (int, float), "Confidence should be a number")
            
            # Check confidence range
            self.assertGreaterEqual(req['confidence'], 0.0, "Confidence should be >= 0.0")
            self.assertLessEqual(req['confidence'], 1.0, "Confidence should be <= 1.0")
            
            # Check requirement text quality
            self.assertGreater(len(req['requirement_text'].strip()), 0, "Empty requirement text")
            self.assertLess(len(req['requirement_text']), 500, "Requirement text too long")
    
    def test_requirement_quality(self):
        """Test the quality of extracted requirements."""
        quality_issues = []
        
        for req in self.requirements:
            # Check requirement text
            if not req['requirement_text'].strip():
                quality_issues.append(f"Empty requirement text in requirement {req['id']}")
            
            # Check keywords
            if not req['keywords']:
                quality_issues.append(f"No keywords in requirement {req['id']}")
            
            # Check for missing conditions
            text = req['requirement_text'].lower()
            if any(word in text for word in ['within', 'after', 'before', 'when', 'if']) and not req['conditions']:
                quality_issues.append(f"Missing conditions in requirement {req['id']}: {req['requirement_text']}")
            
            # Check confidence distribution
            if req['confidence'] == 1.0 and req['type'] == 'implicit':
                quality_issues.append(f"High confidence for implicit requirement {req['id']}")
            
            # Check for vague language
            if any(word in text for word in ['should', 'may', 'might', 'could']):
                quality_issues.append(f"Vague language in requirement {req['id']}: {req['requirement_text']}")
        
        print("\nQuality Issues Found:")
        for issue in quality_issues:
            print(f"- {issue}")
        
        self.assertEqual(len(quality_issues), 0, "Found quality issues in requirements")
    
    def test_requirement_uniqueness(self):
        """Test for duplicate requirements."""
        seen_texts = set()
        duplicates = []
        
        for req in self.requirements:
            text = req['requirement_text'].lower().strip()
            if text in seen_texts:
                duplicates.append(req['requirement_text'])
            seen_texts.add(text)
        
        print("\nDuplicate Requirements Found:")
        for dup in duplicates:
            print(f"- {dup}")
        
        self.assertEqual(len(duplicates), 0, "Found duplicate requirements")
    
    def test_requirement_accuracy(self):
        """Test accuracy against gold standard if available."""
        if not self.gold_standard:
            return
        
        # Calculate accuracy metrics
        total_requirements = len(self.gold_standard)
        correct_requirements = 0
        false_positives = 0
        false_negatives = 0
        
        # Compare each extracted requirement with gold standard
        for req in self.requirements:
            found_match = False
            for gold_req in self.gold_standard:
                # Use sequence matching to handle slight variations
                similarity = SequenceMatcher(None, req['requirement_text'], gold_req['requirement_text']).ratio()
                if similarity > 0.8:  # 80% similarity threshold
                    found_match = True
                    correct_requirements += 1
                    break
            
            if not found_match:
                false_positives += 1
        
        # Calculate false negatives
        false_negatives = total_requirements - correct_requirements
        
        # Calculate metrics
        precision = correct_requirements / (correct_requirements + false_positives) if (correct_requirements + false_positives) > 0 else 0
        recall = correct_requirements / total_requirements if total_requirements > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        print(f"\nAccuracy Metrics:")
        print(f"Precision: {precision:.2f}")
        print(f"Recall: {recall:.2f}")
        print(f"F1 Score: {f1_score:.2f}")
        
        # Set minimum acceptable thresholds
        self.assertGreaterEqual(precision, 0.8, "Precision too low")
        self.assertGreaterEqual(recall, 0.8, "Recall too low")
        self.assertGreaterEqual(f1_score, 0.8, "F1 score too low")

if __name__ == "__main__":
    unittest.main(verbosity=2) 