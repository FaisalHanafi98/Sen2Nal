"""
Sen2Nal Streamlit Dashboard

Main dashboard application - landing page.
"""

import streamlit as st

from src.config import settings
from src.constants import FOOTER_DISCLAIMER

# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(
    page_title="Sen2Nal - Stock Sentiment Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# Session State Initialization
# =============================================================================

if "disclaimer_accepted" not in st.session_state:
    st.session_state.disclaimer_accepted = False


# =============================================================================
# Disclaimer Modal (First-time Users)
# =============================================================================


def show_disclaimer_modal():
    """Show disclaimer agreement modal for first-time users."""
    st.markdown("## ⚠️ Important Notice")

    st.markdown(
        """
    Before using Sen2Nal, please read and acknowledge the following:

    1. **Sen2Nal is NOT a financial advisor** and does not provide investment advice.
    2. **You may lose money** by investing in securities.
    3. **Past performance does NOT guarantee future results.**
    4. **All investment decisions are YOUR responsibility.**
    5. The creator(s) bear **NO LIABILITY** for any financial losses.

    This platform is for **INFORMATIONAL AND EDUCATIONAL PURPOSES ONLY**.
    """
    )

    agree = st.checkbox("✅ I understand and accept all terms", key="disclaimer_checkbox")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Continue to Sen2Nal", disabled=not agree, use_container_width=True):
            st.session_state.disclaimer_accepted = True
            st.rerun()

    if not agree:
        st.stop()


# =============================================================================
# Main Application
# =============================================================================


def main():
    """Main dashboard page."""

    # Show disclaimer if not accepted
    if not st.session_state.disclaimer_accepted:
        show_disclaimer_modal()
        return

    # Header
    st.title("📊 Sen2Nal - Stock Sentiment Analysis")
    st.markdown("### *Combining NLP Sentiment with Calendar Pattern Recognition*")

    st.markdown("---")

    # Welcome Message
    st.info(
        """
    👋 **Welcome to Sen2Nal!**

    This is the **Phase 0 Foundation** setup. The full dashboard is under development.

    **What Sen2Nal does:**
    - Analyzes stock sentiment using FinBERT (NLP model)
    - Identifies calendar-based seasonal patterns
    - Combines signals for trading insights
    - Tracks performance against LLM recommendations
    """
    )

    # System Status
    st.markdown("### 🔧 System Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Environment", value=settings.environment.upper())

    with col2:
        from src.database.connection import check_db_connection

        db_connected = check_db_connection()
        st.metric(
            label="Database",
            value="Connected ✓" if db_connected else "Disconnected ✗",
            delta="PostgreSQL" if db_connected else None,
        )

    with col3:
        st.metric(label="API Version", value="v1.0.0")

    st.markdown("---")

    # Quick Links
    st.markdown("### 🔗 Quick Links")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
        **API Documentation**
        - [Swagger UI](http://localhost:{settings.api_port}/api/v1/docs)
        - [Health Check](http://localhost:{settings.api_port}/api/v1/health)
        """
        )

    with col2:
        st.markdown(
            """
        **Development**
        - Run `make help` for available commands
        - See `README.md` for setup instructions
        """
        )

    with col3:
        st.markdown(
            """
        **Documentation**
        - `SEN2NAL_PRD.md` - Product specs
        - `SEN2NAL_TECHNICAL_ARCHITECTURE.md` - System design
        """
        )

    st.markdown("---")

    # Development Roadmap
    st.markdown("### 🗺️ Development Roadmap")

    phases = [
        {
            "phase": "Phase 0: Foundation (Days 1-5)",
            "status": "🟢 In Progress",
            "tasks": [
                "✅ Project structure scaffold",
                "✅ Database schema (Alembic)",
                "✅ FastAPI health endpoint",
                "✅ Streamlit placeholder",
                "⏳ Environment setup",
            ],
        },
        {
            "phase": "Phase 1: Data Pipeline (Days 6-12)",
            "status": "⚪ Pending",
            "tasks": [
                "S&P 500 stock list ingestion",
                "Calendar dimension setup",
                "News & Reddit API clients",
                "Text processing pipeline",
                "APScheduler daily job",
            ],
        },
        {
            "phase": "Phase 2: Scoring Engine (Days 13-19)",
            "status": "⚪ Pending",
            "tasks": [
                "FinBERT integration",
                "Calendar pattern calculator",
                "Signal combination logic",
                "Conflict detection",
                "Topic extraction",
            ],
        },
        {
            "phase": "Phase 3: API & Dashboard (Days 20-26)",
            "status": "⚪ Pending",
            "tasks": [
                "All FastAPI endpoints",
                "Top 10 stocks dashboard",
                "Stock detail page",
                "Sector aggregation",
                "Legal disclaimers",
            ],
        },
    ]

    for phase_info in phases:
        with st.expander(f"{phase_info['status']} {phase_info['phase']}", expanded=False):
            for task in phase_info["tasks"]:
                st.markdown(f"- {task}")

    # Footer Disclaimer
    st.markdown("---")
    st.markdown(
        f"""
    <div style="text-align: center; color: #888; font-size: 0.85em; padding: 20px;">
    {FOOTER_DISCLAIMER}
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
