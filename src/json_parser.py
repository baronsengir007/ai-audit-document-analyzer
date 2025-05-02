import json
import re
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import jsonschema

class ResponseType(Enum):
    COMPLETENESS_CHECK = "completeness_check"
    REQUIRED_FIELDS = "required_fields"
    TYPE_SPECIFIC = "type_specific"

@dataclass
class ParserMetadata:
    """Metadata about the parsing process"""
    response_type: ResponseType
    confidence_score: float
    extraction_method: str
    parsing_duration_ms: float
    warnings: List[str]

# JSON Schemas for validation
SCHEMAS = {
    ResponseType.COMPLETENESS_CHECK: {
        "type": "object",
        "required": ["satisfied", "explanation", "found_keywords", "missing_keywords", "confidence_score"],
        "properties": {
            "satisfied": {"type": "boolean"},
            "explanation": {"type": "string"},
            "found_keywords": {"type": "array", "items": {"type": "string"}},
            "missing_keywords": {"type": "array", "items": {"type": "string"}},
            "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
            "suggestions": {"type": "array", "items": {"type": "string"}}
        }
    },
    ResponseType.REQUIRED_FIELDS: {
        "type": "object",
        "required": ["missing_fields", "present_fields", "field_details", "overall_completeness"],
        "properties": {
            "missing_fields": {"type": "array", "items": {"type": "string"}},
            "present_fields": {"type": "array", "items": {"type": "string"}},
            "field_details": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["field_name", "is_present", "value", "confidence"],
                    "properties": {
                        "field_name": {"type": "string"},
                        "is_present": {"type": "boolean"},
                        "location": {"type": "string"},
                        "value": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                    }
                }
            },
            "overall_completeness": {"type": "number", "minimum": 0, "maximum": 1},
            "suggestions": {"type": "array", "items": {"type": "string"}}
        }
    },
    ResponseType.TYPE_SPECIFIC: {
        "type": "object",
        "required": ["satisfied", "completeness_score", "keyword_analysis", "field_analysis"],
        "properties": {
            "satisfied": {"type": "boolean"},
            "completeness_score": {"type": "number", "minimum": 0, "maximum": 1},
            "keyword_analysis": {
                "type": "object",
                "required": ["found", "missing"],
                "properties": {
                    "found": {"type": "array", "items": {"type": "string"}},
                    "missing": {"type": "array", "items": {"type": "string"}}
                }
            },
            "field_analysis": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["field_name", "is_present", "value", "format_valid", "confidence"],
                    "properties": {
                        "field_name": {"type": "string"},
                        "is_present": {"type": "boolean"},
                        "value": {"type": "string"},
                        "format_valid": {"type": "boolean"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                    }
                }
            },
            "suggestions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["field", "issue", "recommendation"],
                    "properties": {
                        "field": {"type": "string"},
                        "issue": {"type": "string"},
                        "recommendation": {"type": "string"}
                    }
                }
            }
        }
    }
}

class LLMResponseParser:
    """Parser for converting LLM responses into structured JSON data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extract JSON object or array from text using regex"""
        # Look for JSON object
        obj_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
        obj_match = re.search(obj_pattern, text, re.DOTALL)
        if obj_match:
            return obj_match.group(0)
        
        # Look for JSON array
        arr_pattern = r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'
        arr_match = re.search(arr_pattern, text, re.DOTALL)
        if arr_match:
            return arr_match.group(0)
        
        return None
    
    def _validate_json_schema(self, data: Dict, response_type: ResponseType) -> List[str]:
        """Validate JSON data against schema"""
        try:
            jsonschema.validate(instance=data, schema=SCHEMAS[response_type])
            return []
        except jsonschema.exceptions.ValidationError as e:
            error = f"Schema validation error: {e.message}"
            self.logger.error(error)
            raise ValueError(error)
        except Exception as e:
            error = f"Unexpected validation error: {str(e)}"
            self.logger.error(error)
            raise ValueError(error)
    
    def _clean_json_string(self, text: str) -> str:
        """Clean and normalize JSON string"""
        # Remove any markdown code block markers
        text = re.sub(r'```(?:json)?\s*|\s*```', '', text)
        # Remove any leading/trailing whitespace
        text = text.strip()
        return text
    
    def _calculate_confidence(self, data: Dict, warnings: List[str]) -> float:
        """Calculate overall confidence score based on data quality and warnings"""
        base_confidence = 1.0
        
        # Reduce confidence for each warning
        base_confidence -= len(warnings) * 0.1
        
        # Check for missing or empty fields
        if isinstance(data.get('confidence_score'), (int, float)):
            base_confidence = min(base_confidence, data['confidence_score'])
        
        return max(0.0, min(1.0, base_confidence))
    
    def parse_response(self, response: str, response_type: ResponseType) -> tuple[Dict, ParserMetadata]:
        """
        Parse LLM response into structured JSON data
        
        Args:
            response: Raw LLM response text
            response_type: Type of response expected
            
        Returns:
            Tuple of (parsed data dict, parser metadata)
        """
        import time
        start_time = time.time()
        warnings = []
        
        try:
            # Clean and extract JSON
            cleaned_text = self._clean_json_string(response)
            json_str = self._extract_json_from_text(cleaned_text)
            
            if not json_str:
                raise ValueError("No JSON object found in response")
            
            # Parse JSON
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {str(e)}")
            
            # Validate against schema
            schema_warnings = self._validate_json_schema(data, response_type)
            warnings.extend(schema_warnings)
            
            # Calculate confidence
            confidence = self._calculate_confidence(data, warnings)
            
            # Create metadata
            metadata = ParserMetadata(
                response_type=response_type,
                confidence_score=confidence,
                extraction_method="regex" if len(cleaned_text) != len(json_str) else "direct",
                parsing_duration_ms=(time.time() - start_time) * 1000,
                warnings=warnings
            )
            
            return data, metadata
            
        except Exception as e:
            self.logger.error(f"Error parsing response: {str(e)}")
            raise
    
    def format_output(self, data: Dict, metadata: ParserMetadata) -> Dict:
        """Format final output with data and metadata"""
        return {
            "data": data,
            "metadata": {
                "response_type": metadata.response_type.value,
                "confidence_score": metadata.confidence_score,
                "extraction_method": metadata.extraction_method,
                "parsing_duration_ms": metadata.parsing_duration_ms,
                "warnings": metadata.warnings
            }
        } 