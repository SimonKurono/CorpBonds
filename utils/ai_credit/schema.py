"""
Pydantic schemas for Credit Memo AI strict JSON validation
"""
from pydantic import BaseModel, Field
from typing import List


class MacroSensitivity(BaseModel):
    """Macro sensitivity analysis"""
    rates: str = Field(..., description="Sensitivity to interest rate changes")
    spreads: str = Field(..., description="Sensitivity to credit spread movements")
    liquidity: str = Field(..., description="Liquidity considerations")


class ConfidenceScores(BaseModel):
    """Confidence metrics for the analysis"""
    overall: float = Field(..., ge=0, le=1, description="Overall confidence score (0-1)")
    data_quality: float = Field(..., ge=0, le=1, description="Quality of input data (0-1)")
    model_judgment: float = Field(..., ge=0, le=1, description="Model's analytical confidence (0-1)")


class CreditMemo(BaseModel):
    """Complete credit memo structure"""
    issuer_summary: str = Field(..., description="Executive summary of the issuer")
    bond_summary: str = Field(..., description="Summary of the bond instrument")
    business_risk: List[str] = Field(..., description="List of business risk factors")
    financial_risk: List[str] = Field(..., description="List of financial risk factors")
    structure_and_covenants: List[str] = Field(..., description="Bond structure and covenant analysis")
    macro_sensitivity: MacroSensitivity = Field(..., description="Macro environment sensitivity")
    bull_case: List[str] = Field(..., description="Positive scenarios and catalysts")
    bear_case: List[str] = Field(..., description="Negative scenarios and risks")
    key_questions: List[str] = Field(..., description="Critical questions for further analysis")
    uncertainties: List[str] = Field(..., description="Areas of uncertainty or missing data")
    confidence: ConfidenceScores = Field(..., description="Confidence metrics")
    disclaimer: str = Field(..., description="Standard disclaimer")
