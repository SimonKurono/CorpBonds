"""
Credit Memo AI - GenAI-powered buy-side credit analysis

This page generates qualitative credit memos using Google's Gemini LLM.
Completely isolated from production analytics, auth, and portfolio logic.
"""
import streamlit as st
import sys
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.ai_credit.gemini_client import generate_credit_memo
from utils.ai_credit.renderer import render_memo, export_to_markdown
import utils.ui as ui

# Page config

# ╭────────────────────────── Render sections ──────────────────────╮

ui.configure_page(page_title="Credit Memo AI", page_icon="🤖", layout="wide")

ui.render_sidebar()


# --- HEADER ---
st.markdown("""
Generate structured buy-side credit analysis. Provide issuer details and context below.
""")

with st.expander("ℹ️ About this Tool", expanded=False):
    st.info(
        """
        **What it does:** This tool uses Google's **Gemini 3 Flash** LLM to act as a senior credit analyst. 
        It ingests your qualitative inputs and generates a structured "Memo" typical of buy-side investment committees.

        **What it outputs:**
        - **Risk Analysis**: Solvency, liquidity, and business model risks.
        - **Macro Sensitivity**: How rates/inflation impact the issuer.
        - **Scenario Planning**: Bull/Bear/Base case outcomes.
        - **Confidence Score**: The model's self-assessed certainty based on provided context.
        
        *Note: No data is stored reliably. Please export results to Markdown if needed.*
        """
    )

st.divider()

# --- INPUT SECTION ---

# Row 1: Issuer Details
st.subheader("Issuer Details")
col1, col2 = st.columns(2)

with col1:
    issuer_name = st.text_input(
        "Issuer Name",
        placeholder="e.g., Apple Inc"
    )

with col2:
    sector = st.text_input(
        "Sector",
        placeholder="e.g., Technology"
    )

# Row 2: Bond Details
col3, col4, col5 = st.columns(3)

with col3:
    maturity = st.text_input(
        "Maturity",
        placeholder="e.g. 2028"
    )

with col4:
    coupon = st.number_input(
        "Coupon (%)",
        min_value=0.0,
        max_value=20.0,
        value=5.0,
        step=0.125,
        format="%.3f"
    )

with col5:
    seniority = st.selectbox(
        "Seniority",
        options=["Senior Secured", "Senior Unsecured", "Subordinated"]
    )

# Row 3: Context (Expandable)
with st.expander("Additional Context (Optional)", expanded=True):
    col6, col7 = st.columns(2)
    
    with col6:
        leverage_description = st.text_area(
            "Leverage / Credit Profile",
            placeholder="Describe leverage metrics, coverage ratios, or recent financial performance...",
            height=150
        )
    
    with col7:
        macro_context = st.text_area(
            "Macro / Market Context",
            placeholder="Describe current rate environment, sector trends, or specific market conditions...",
            height=150
        )

# Row 4: Action
st.write("") # Spacer
generate_col, _, _ = st.columns([1, 2, 2])
with generate_col:
    generate_button = st.button("Generate Analysis", type="primary", use_container_width=True)

st.divider()

# --- GENERATION LOGIC ---

if generate_button:
    # Validate required inputs
    if not issuer_name or not sector or not maturity:
        st.error("Please provide Issuer Name, Sector, and Maturity to proceed.")
    else:
        # Prepare input bundle
        input_bundle = {
            "issuer_name": issuer_name,
            "sector": sector,
            "maturity": maturity,
            "coupon": coupon,
            "seniority": seniority,
            "leverage_description": leverage_description,
            "macro_context": macro_context
        }
        
        try:
            with st.spinner("Synthesizing credit memo..."):
                # Generate memo
                memo = generate_credit_memo(input_bundle)
                
                # Store in session state
                st.session_state["current_memo"] = memo
                st.session_state["current_issuer"] = issuer_name
                
            st.success("Analysis generated successfully.")
            
        except ValueError as e:
            st.error(f"Configuration Error: {str(e)}")
            st.info("Ensure GOOGLE_API_KEY is set in your .env file.")
            
        except RuntimeError as e:
            st.error(f"Generation Error: {str(e)}")
            
            # Show raw response if available
            if "Raw text:" in str(e):
                with st.expander("View Raw Model Response"):
                    raw_text = str(e).split("Raw text: ")[-1]
                    st.code(raw_text, language="text")
            elif "Response object:" in str(e): # Handle debug info in error
                 with st.expander("View Debug Info"):
                    st.code(str(e), language="text")
                    
        except Exception as e:
            st.error(f"Unexpected Error: {str(e)}")

# --- OUTPUT DISPLAY ---

if "current_memo" in st.session_state:
    memo = st.session_state["current_memo"]
    issuer = st.session_state["current_issuer"]
    
    # Render the memo
    render_memo(memo)
    
    st.divider()
    
    # Download and Raw Data
    col_d1, col_d2 = st.columns([1, 3])
    
    with col_d1:
        # Download button
        markdown_content = export_to_markdown(memo, issuer)
        st.download_button(
            label="Download Markdown",
            data=markdown_content,
            file_name=f"credit_memo_{issuer.replace(' ', '_').lower()}.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    with st.expander("View Raw JSON Data"):
        st.json(memo)

elif not generate_button:
    # Placeholder state
    st.info("Enter details above and click 'Generate Analysis' to begin.")
