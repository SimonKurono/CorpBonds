"""
Prompts for Credit Memo AI generation
"""

SYSTEM_PROMPT = """You are a senior buy-side credit analyst preparing investment memos for institutional fixed-income portfolios.

Your role:
- Synthesize provided information into structured credit analysis
- Flag uncertainties and data gaps explicitly
- Never hallucinate specific numbers, dates, or facts not provided
- Provide qualitative analysis only (no price targets, default probabilities, or return forecasts)
- Use professional buy-side language

Output requirements:
- Return ONLY valid JSON matching the exact schema provided
- No markdown, no code blocks, no explanatory text
- Ensure all required fields are populated
- Lists must contain at least 2-3 items each
- Confidence scores must be between 0 and 1
"""

USER_PROMPT_TEMPLATE = """Generate a credit memo based on the following information:

ISSUER INFORMATION:
- Name: {issuer_name}
- Sector: {sector}

BOND INFORMATION:
- Maturity: {maturity}
- Coupon: {coupon}%
- Seniority: {seniority}

LEVERAGE CONTEXT:
{leverage_description}

MACRO ENVIRONMENT:
{macro_context}

Return a JSON object with the following structure:
{{
  "issuer_summary": "string - executive summary of issuer",
  "bond_summary": "string - summary of bond instrument", 
  "business_risk": ["list of business risks"],
  "financial_risk": ["list of financial risks"],
  "structure_and_covenants": ["list of structure/covenant points"],
  "macro_sensitivity": {{
    "rates": "string - interest rate sensitivity",
    "spreads": "string - credit spread sensitivity",
    "liquidity": "string - liquidity considerations"
  }},
  "bull_case": ["list of positive scenarios"],
  "bear_case": ["list of negative scenarios"],
  "key_questions": ["list of critical questions"],
  "uncertainties": ["list of data gaps and uncertainties"],
  "confidence": {{
    "overall": 0.0-1.0,
    "data_quality": 0.0-1.0,
    "model_judgment": 0.0-1.0
  }},
  "disclaimer": "standard disclaimer text"
}}

IMPORTANT: 
- Only synthesize the information provided above
- Flag any missing data in the 'uncertainties' field
- Do not invent specific financial metrics or dates
- Return ONLY the JSON object, no other text
"""


def format_user_prompt(
    issuer_name: str,
    sector: str,
    maturity: str,
    coupon: float,
    seniority: str,
    leverage_description: str = "",
    macro_context: str = ""
) -> str:
    """Format the user prompt with input data"""
    
    leverage_text = leverage_description if leverage_description.strip() else "No specific leverage information provided."
    macro_text = macro_context if macro_context.strip() else "No specific macro context provided."
    
    return USER_PROMPT_TEMPLATE.format(
        issuer_name=issuer_name,
        sector=sector,
        maturity=maturity,
        coupon=coupon,
        seniority=seniority,
        leverage_description=leverage_text,
        macro_context=macro_text
    )
