"""
Streamlit renderer for credit memos
"""
import streamlit as st
from datetime import datetime


def render_memo(memo: dict):
    """
    Render a credit memo in Streamlit with formatted sections.
    
    Args:
        memo: Validated credit memo dictionary
    """
    
    st.markdown("### Executive Summary")
    
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Issuer Profile")
        st.write(memo["issuer_summary"])
    
    with col2:
        st.caption("Bond Instrument")
        st.write(memo["bond_summary"])
    
    st.divider()
    
    # Tabs for detailed analysis
    tab_risk, tab_scenarios, tab_structure = st.tabs([
        "Risk Analysis", "Scenarios", "Structure & Macro"
    ])
    
    with tab_risk:
        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            st.markdown("#### Business Risk")
            for risk in memo["business_risk"]:
                st.markdown(f"• {risk}")
        
        with col_r2:
            st.markdown("#### Financial Risk")
            for risk in memo["financial_risk"]:
                st.markdown(f"• {risk}")

    with tab_scenarios:
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            st.markdown("#### Bull Case")
            for item in memo["bull_case"]:
                st.markdown(f"• {item}")
        
        with col_s2:
            st.markdown("#### Bear Case")
            for item in memo["bear_case"]:
                st.markdown(f"• {item}")

    with tab_structure:
        st.markdown("#### Structure & Covenants")
        for item in memo["structure_and_covenants"]:
            st.markdown(f"• {item}")
        
        st.write("")
        st.markdown("#### Macro Sensitivity")
        macro = memo["macro_sensitivity"]
        
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.info(f"**Rates**\n\n{macro['rates']}")
        m_col2.info(f"**Spreads**\n\n{macro['spreads']}")
        m_col3.info(f"**Liquidity**\n\n{macro['liquidity']}")
    
    st.divider()
    
    # Outlook Section
    col_q1, col_q2 = st.columns(2)
    
    with col_q1:
        st.markdown("#### Key Questions")
        for q in memo["key_questions"]:
             st.markdown(f"- {q}")
    
    with col_q2:
        st.markdown("#### Uncertainties / Data Gaps")
        for u in memo["uncertainties"]:
             st.markdown(f"- {u}")
    
    st.divider()
    
    # Confidence Metrics
    st.caption("Model Confidence Assessment")
    conf = memo["confidence"]
    
    c_col1, c_col2, c_col3 = st.columns(3)
    c_col1.metric("Overall Confidence", f"{conf['overall']:.0%}")
    c_col2.metric("Data Quality", f"{conf['data_quality']:.0%}")
    c_col3.metric("Model Judgment", f"{conf['model_judgment']:.0%}")
    
    st.caption(f"Disclaimer: {memo['disclaimer']}")


def export_to_markdown(memo: dict, issuer_name: str) -> str:
    """
    Convert credit memo to markdown format for download.
    
    Args:
        memo: Validated credit memo dictionary
        issuer_name: Name of the issuer for the title
        
    Returns:
        Markdown-formatted string
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    md = f"""# Credit Memo: {issuer_name}
*Generated: {timestamp}*

---

## Executive Summary
### Issuer Profile
{memo["issuer_summary"]}

### Bond Summary
{memo["bond_summary"]}

---

## Risk Analysis
### Business Risk
"""
    for risk in memo["business_risk"]:
        md += f"- {risk}\n"
    
    md += "\n### Financial Risk\n"
    for risk in memo["financial_risk"]:
        md += f"- {risk}\n"
    
    md += "\n---\n\n## Scenarios\n\n### Bull Case\n"
    for item in memo["bull_case"]:
        md += f"- {item}\n"
    
    md += "\n### Bear Case\n"
    for item in memo["bear_case"]:
        md += f"- {item}\n"
    
    md += "\n---\n\n## Structure & Macro\n\n### Structure & Covenants\n"
    for item in memo["structure_and_covenants"]:
        md += f"- {item}\n"
    
    md += "\n### Macro Sensitivity\n"
    macro = memo["macro_sensitivity"]
    md += f"**Rates:** {macro['rates']}\n\n"
    md += f"**Spreads:** {macro['spreads']}\n\n"
    md += f"**Liquidity:** {macro['liquidity']}\n"
    
    md += "\n---\n\n## Outlook\n\n### Key Questions\n"
    for q in memo["key_questions"]:
        md += f"- {q}\n"
    
    md += "\n### Uncertainties\n"
    for u in memo["uncertainties"]:
        md += f"- {u}\n"
    
    md += "\n---\n\n## Confidence Metrics\n"
    conf = memo["confidence"]
    md += f"**Overall:** {conf['overall']:.0%} | **Data Quality:** {conf['data_quality']:.0%} | **Model Judgment:** {conf['model_judgment']:.0%}\n"
    
    md += f"\n---\n\n*{memo['disclaimer']}*\n"
    
    return md
