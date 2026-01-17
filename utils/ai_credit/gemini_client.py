"""
Gemini client for credit memo generation
"""
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from .prompts import SYSTEM_PROMPT, format_user_prompt
from .schema import CreditMemo

# Load environment variables
load_dotenv()


def generate_credit_memo(input_bundle: dict) -> dict:
    """
    Generate a credit memo using Gemini LLM.
    
    Args:
        input_bundle: Dictionary containing:
            - issuer_name: str
            - sector: str
            - maturity: str
            - coupon: float
            - seniority: str
            - leverage_description: str (optional)
            - macro_context: str (optional)
    
    Returns:
        Dictionary containing validated credit memo fields
        
    Raises:
        ValueError: If API key is missing or invalid
        RuntimeError: If generation or parsing fails
    """
    # Get API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_key_here":
        raise ValueError(
            "GOOGLE_API_KEY not found or invalid in .env file. "
            "Please obtain an API key from Google AI Studio and add it to .env"
        )
    
    # Create Gemini client
    client = genai.Client(api_key=api_key)
    
    # Format prompts
    user_prompt = format_user_prompt(
        issuer_name=input_bundle.get("issuer_name", ""),
        sector=input_bundle.get("sector", ""),
        maturity=input_bundle.get("maturity", ""),
        coupon=input_bundle.get("coupon", 0.0),
        seniority=input_bundle.get("seniority", ""),
        leverage_description=input_bundle.get("leverage_description", ""),
        macro_context=input_bundle.get("macro_context", "")
    )
    
    try:
        # Generate content using new API with system instruction
        # Using gemini-3-flash-preview as the stable model
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=1.0
            )
        )
        
        # Check if response is valid
        if not response.text:
            raise RuntimeError(
                f"Model returned empty response. "
                f"This may be due to safety filters or a model error."
            )
        
        raw_text = response.text
        
        # Try to extract JSON from response (handle potential markdown wrapping)
        json_text = raw_text.strip()
        
        # Remove markdown code blocks if present
        if json_text.startswith("```"):
            lines = json_text.split("\n")
            # Remove first line (```json or ```) and last line (```)
            # Handle cases where the code block might be inline or formatted differently
            if len(lines) >= 3:
                json_text = "\n".join(lines[1:-1])
            else:
                json_text = json_text.replace("```json", "").replace("```", "")
        
        # Parse JSON
        memo_dict = json.loads(json_text)
        
        # Validate with Pydantic
        memo_obj = CreditMemo(**memo_dict)
        
        # Return as dictionary
        return memo_obj.model_dump()
        
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse JSON from model response. "
            f"Error: {str(e)}. "
            f"Raw text: {raw_text[:500]}..."
        )
    except Exception as e:
        raise RuntimeError(f"Error generating credit memo: {str(e)}")
