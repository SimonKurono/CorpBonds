import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.ai_credit.schema import CreditMemo, ConfidenceScores, MacroSensitivity
from utils.ai_credit.prompts import format_user_prompt, SYSTEM_PROMPT
from utils.ai_credit.renderer import export_to_markdown
from utils.ai_credit.gemini_client import generate_credit_memo


class TestSchemas(unittest.TestCase):
    def test_valid_credit_memo(self):
        """Test that a valid dictionary parses correctly into CreditMemo model"""
        valid_data = {
            "issuer_summary": "Summary",
            "bond_summary": "Bond",
            "business_risk": ["Risk1", "Risk2"],
            "financial_risk": ["Risk1", "Risk2"],
            "structure_and_covenants": ["Cov1"],
            "macro_sensitivity": {
                "rates": "Rates",
                "spreads": "Spreads",
                "liquidity": "Liquidity"
            },
            "bull_case": ["Bull"],
            "bear_case": ["Bear"],
            "key_questions": ["Q1"],
            "uncertainties": ["U1"],
            "confidence": {
                "overall": 0.9,
                "data_quality": 0.8,
                "model_judgment": 0.9
            },
            "disclaimer": "Disclaimer"
        }
        model = CreditMemo(**valid_data)
        self.assertEqual(model.issuer_summary, "Summary")
        self.assertEqual(model.confidence.overall, 0.9)

    def test_invalid_confidence_score(self):
        """Test validation fails for confidence scores outside 0-1 range"""
        invalid_data = {
            "issuer_summary": "Summary",
            "bond_summary": "Bond",
            "business_risk": [],
            "financial_risk": [],
            "structure_and_covenants": [],
            "macro_sensitivity": {"rates": "", "spreads": "", "liquidity": ""},
            "bull_case": [],
            "bear_case": [],
            "key_questions": [],
            "uncertainties": [],
            "confidence": {
                "overall": 1.5,  # Invalid > 1.0
                "data_quality": 0.5,
                "model_judgment": 0.5
            },
            "disclaimer": ""
        }
        with self.assertRaises(ValueError):
            CreditMemo(**invalid_data)


class TestPrompts(unittest.TestCase):
    def test_format_user_prompt_basic(self):
        """Test prompt formatting with minimal requirements"""
        prompt = format_user_prompt(
            issuer_name="Test Corp",
            sector="Tech",
            maturity="2030",
            coupon=5.0,
            seniority="Senior Unsecured"
        )
        self.assertIn("Test Corp", prompt)
        self.assertIn("Tech", prompt)
        self.assertIn("2030", prompt)
        self.assertIn("5.0%", prompt)
        self.assertIn("No specific leverage information provided", prompt)

    def test_format_user_prompt_full(self):
        """Test prompt formatting with all optional fields"""
        prompt = format_user_prompt(
            issuer_name="Test Corp",
            sector="Tech",
            maturity="2030",
            coupon=5.0,
            seniority="Senior Unsecured",
            leverage_description="High leverage",
            macro_context="Recessionary"
        )
        self.assertIn("High leverage", prompt)
        self.assertIn("Recessionary", prompt)
        self.assertNotIn("No specific leverage information provided", prompt)


class TestRenderer(unittest.TestCase):
    def test_export_to_markdown(self):
        """Test that markdown export contains key sections and data"""
        memo_dict = {
            "issuer_summary": "Executive Summary Text",
            "bond_summary": "Bond Summary Text",
            "business_risk": ["Biz Risk 1", "Biz Risk 2"],
            "financial_risk": ["Fin Risk 1"],
            "structure_and_covenants": ["Cov 1"],
            "macro_sensitivity": {
                "rates": "Rate Sens",
                "spreads": "Spread Sens",
                "liquidity": "Liq Sens"
            },
            "bull_case": ["Bull 1"],
            "bear_case": ["Bear 1"],
            "key_questions": ["Q1"],
            "uncertainties": ["U1"],
            "confidence": {
                "overall": 0.95,
                "data_quality": 0.8,
                "model_judgment": 0.9
            },
            "disclaimer": "Standard Disclaimer"
        }
        
        md = export_to_markdown(memo_dict, "Apple Inc")
        
        self.assertIn("# Credit Memo: Apple Inc", md)
        self.assertIn("Executive Summary Text", md)
        self.assertIn("**Overall:** 95%", md)
        self.assertIn("Biz Risk 1", md)


class TestGeminiClient(unittest.TestCase):
    def setUp(self):
        # Sample valid input bundle
        self.input_bundle = {
            "issuer_name": "Test Issuer",
            "sector": "Test Sector",
            "maturity": "2025",
            "coupon": 5.0,
            "seniority": "Senior"
        }
        
        # Sample valid JSON response text
        self.valid_response_json = json.dumps({
            "issuer_summary": "Test Summary",
            "bond_summary": "Test Bond",
            "business_risk": ["Risk"],
            "financial_risk": ["Risk"],
            "structure_and_covenants": ["Cov"],
            "macro_sensitivity": {
                "rates": "Rates",
                "spreads": "Spreads",
                "liquidity": "Liquidity"
            },
            "bull_case": ["Bull"],
            "bear_case": ["Bear"],
            "key_questions": ["Q"],
            "uncertainties": ["U"],
            "confidence": {
                "overall": 0.9,
                "data_quality": 0.9,
                "model_judgment": 0.9
            },
            "disclaimer": "Disclaimer"
        })

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "fake_key"})
    @patch("utils.ai_credit.gemini_client.genai.Client")
    def test_generate_credit_memo_success(self, mock_client_cls):
        """Test successful memo generation"""
        # Mock client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = self.valid_response_json
        
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client
        
        result = generate_credit_memo(self.input_bundle)
        
        # Verify result structure
        self.assertEqual(result["issuer_summary"], "Test Summary")
        self.assertEqual(result["confidence"]["overall"], 0.9)
        
        # Verify API call used correct model
        mock_client.models.generate_content.assert_called_once()
        call_args = mock_client.models.generate_content.call_args
        self.assertEqual(call_args.kwargs["model"], "gemini-3-flash-preview")
        config = call_args.kwargs["config"]
        # Check attributes directly on the config object
        self.assertTrue(hasattr(config, "system_instruction"))
        self.assertEqual(config.response_mime_type, "application/json")

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "fake_key"})
    @patch("utils.ai_credit.gemini_client.genai.Client")
    def test_generate_credit_memo_empty_response(self, mock_client_cls):
        """Test handling of empty response from API"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = ""  # Empty text
        
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client
        
        with self.assertRaises(RuntimeError) as cm:
            generate_credit_memo(self.input_bundle)
        
        self.assertIn("Model returned empty response", str(cm.exception))

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "fake_key"})
    @patch("utils.ai_credit.gemini_client.genai.Client")
    def test_generate_credit_memo_malformed_json(self, mock_client_cls):
        """Test handling of invalid JSON response"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Not JSON output"
        
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client
        
        with self.assertRaises(RuntimeError) as cm:
            generate_credit_memo(self.input_bundle)
            
        self.assertIn("Failed to parse JSON", str(cm.exception))

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key(self):
        """Test error when API key is missing"""
        with self.assertRaises(ValueError) as cm:
            generate_credit_memo(self.input_bundle)
        self.assertIn("GOOGLE_API_KEY not found", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
