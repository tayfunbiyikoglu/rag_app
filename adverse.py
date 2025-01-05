"""Main application file for the Adverse News Search tool."""
import streamlit as st
from typing import List, Dict
import logging

# Import services
from src.services.search_service import search_internet, create_search_query
from src.services.content_service import scrape_content, quick_analyze
from src.services.analysis_service import analyze_content
from src.reports.report_generator import generate_markdown_report, convert_to_pdf
from src.utils.logging_config import setup_logging
from src.config.settings import setup_streamlit, MIN_COMPOSITE_SCORE

def process_sources(urls: List[str], num_results: int) -> List[Dict]:
    """Process sources and return analyses."""
    analyses = []

    # Phase 1: Quick Analysis
    st.subheader("Phase 1: Initial Screening")
    st.write(f"Performing quick analysis on {len(urls)} sources...")
    progress_bar = st.progress(0)

    preliminary_analyses = []
    for i, url in enumerate(urls):
        try:
            # Quick content scraping and analysis
            content = scrape_content(url)
            quick_result = quick_analyze(url, content)

            # Update progress bar and display quick results
            progress_bar.progress((i + 1) / len(urls))

            if quick_result['composite_score'] >= MIN_COMPOSITE_SCORE:
                preliminary_analyses.append((url, content, quick_result))
                st.write(f"✅ {url}")
                st.write(f"Quick Score: {quick_result['composite_score']:.2f}")
                with st.expander("Score Breakdown"):
                    st.write(f"- Preliminary Score: {quick_result['preliminary_score']:.2f}")
                    st.write(f"- Domain Score: {quick_result['domain_score']:.2f}")
                    st.write(f"- Recency Score: {quick_result['recency_score']:.2f}")
            else:
                st.write(f"❌ {url}")
                with st.expander(f"Low Score Details ({quick_result['composite_score']:.2f})"):
                    st.write("This URL was filtered out due to low risk indicators:")
                    st.write(f"- Preliminary Score: {quick_result['preliminary_score']:.2f} (Weight: 40%)")
                    st.write(f"- Domain Score: {quick_result['domain_score']:.2f} (Weight: 40%)")
                    st.write(f"- Recency Score: {quick_result['recency_score']:.2f} (Weight: 20%)")
                    st.write(f"\nMinimum required composite score: {MIN_COMPOSITE_SCORE}")
                    if quick_result['preliminary_score'] < 20:
                        st.write("📝 Low preliminary score indicates content may not be relevant to adverse news.")
                    if quick_result['domain_score'] < 20:
                        st.write("🌐 Low domain score indicates this may not be from a primary news or regulatory source.")
                    if quick_result['recency_score'] < 20:
                        st.write("📅 Low recency score suggests this content may be outdated.")

        except Exception as e:
            logging.error(f"Error processing {url}: {str(e)}")
            st.warning(f"Skipping {url} due to error: {str(e)}")

    # Sort and select top sources
    sorted_analyses = sorted(preliminary_analyses,
                           key=lambda x: x[2]['composite_score'],
                           reverse=True)[:num_results]

    # Phase 2: Detailed Analysis
    st.subheader("Phase 2: Detailed Analysis")
    st.write(f"Performing detailed analysis on top {len(sorted_analyses)} sources...")

    detailed_progress = st.progress(0)
    for idx, (url, content, quick_analysis) in enumerate(sorted_analyses):
        try:
            st.write(f"Analyzing: {url}")

            # Perform detailed analysis
            detailed_analysis = analyze_content(content, url)
            detailed_analysis['url'] = url
            detailed_analysis['quick_score'] = quick_analysis['composite_score']

            # Calculate overall risk score
            overall_score = calculate_overall_score(
                detailed_analysis['relevancy_score'],
                detailed_analysis['reliability_score']
            )
            detailed_analysis['overall_risk_score'] = overall_score

            analyses.append(detailed_analysis)

            # Display detailed results
            st.write(f"**Detailed Results for {url}**")
            st.write(f"Overall Risk Score: {overall_score:.2f}")
            st.write(f"Reliability Score: {detailed_analysis['reliability_score']}")
            st.write(f"Relevancy Score: {detailed_analysis['relevancy_score']}")
            st.write("Key Findings:", detailed_analysis['key_findings'])

            # Add divider between analyses
            if idx < len(sorted_analyses) - 1:  # Don't add divider after last item
                st.divider()

            detailed_progress.progress((idx + 1) / len(sorted_analyses))

        except Exception as e:
            logging.error(f"Error analyzing {url}: {str(e)}")
            st.warning(f"Error analyzing {url}: {str(e)}")

    return analyses

def calculate_overall_score(relevancy_score: float, reliability_score: float) -> float:
    """
    Calculate overall risk score using a two-stage approach that prioritizes relevancy.

    Args:
        relevancy_score (float): How relevant the content is to adverse news (0-100)
        reliability_score (float): How reliable the source is (0-100)

    Returns:
        float: Overall risk score (0-100)
    """
    # Stage 1: Relevancy Check
    RELEVANCY_THRESHOLD = 50
    if relevancy_score < RELEVANCY_THRESHOLD:
        return relevancy_score  # Return low score if not relevant enough

    # Stage 2: Factor in reliability only for relevant content
    return min(100, (relevancy_score * 0.8) + (reliability_score * 0.2))

def main():
    """Main application function."""
    # Setup
    setup_logging()
    setup_streamlit()
    
    # Initialize session state for modal
    if 'show_modal' not in st.session_state:
        st.session_state.show_modal = False

    def toggle_modal():
        st.session_state.show_modal = not st.session_state.show_modal

    # Inject custom CSS
    st.markdown("""
        <style>
        .block-container {
            padding-top: 2rem;
        }
        div.block-container {
            padding-top: 2rem;
        }
        div.block-container > div:first-child {
            margin-top: 1rem;
        }
        .phase-box {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .phase-title {
            color: #4B4BC8;
            font-size: 1.2rem;
            margin-bottom: 0.5rem;
        }
        /* Info button styling */
        div[data-testid="stButton"] button:first-of-type {
            background-color: transparent;
            border: none;
            padding: 0;
            font-size: 1.5rem;
            line-height: 1;
            cursor: pointer;
        }
        /* Main action buttons styling */
        div[data-testid="stButton"] button {
            background-color: #4B4BC8;
            color: white;
            padding: 0.75rem 2rem;
            font-size: 1rem;
            width: 100%;
            border: none;
            border-radius: 5px;
            transition: background-color 0.3s ease;
        }
        div[data-testid="stButton"] button:hover {
            background-color: #3939A2;
            color: #E50050;
        }
        /* Modal close button specific styling */
        div[data-testid="stButton"] button[kind="secondary"] {
            background-color: #6B6BE8;
            padding: 0.5rem 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Center the content
    col1, col2, col3 = st.columns([0.2, 1.7, 0.1])
    
    with col1:
        st.image("static/logo.png", width=60)
        
    with col2:
        st.markdown("<h1 style='color: #4B4BC8; margin-left: -1rem; margin-top: -1rem'>Adverse News Search 🔍</h1>", unsafe_allow_html=True)
    
    with col3:
        st.button("ℹ️", on_click=toggle_modal, key="info_button")

    # Handle modal state
    if st.session_state.show_modal:
        with st.expander("Understanding Our Analysis System", expanded=True):
            st.markdown("""
                <div class='phase-box'>
                    <div class='phase-title'>📊 Phase 1: Initial Screening</div>
                    • Performs Google search for adverse news<br>
                    • Quick analysis of each result with composite scoring:<br>
                    &nbsp;&nbsp;- Risk Score (60%): Analyzes content for risk terms<br>
                    &nbsp;&nbsp;- Domain Score (25%): Rates source credibility<br>
                    &nbsp;&nbsp;- Recency Score (15%): Considers publication date
                </div>
                
                <div class='phase-box'>
                    <div class='phase-title'>🔍 Phase 2: Detailed Analysis</div>
                    • In-depth content analysis of top results<br>
                    • Evaluates relevancy with threshold of 50<br>
                    • Final score combines:<br>
                    &nbsp;&nbsp;- Content relevancy (80%)<br>
                    &nbsp;&nbsp;- Source reliability (20%)
                </div>
                
                <div style='margin-top: 1rem;'>
                    <strong>💡 Key Benefits:</strong><br>
                    ✓ Smart scoring prioritizes important findings<br>
                    ✓ Considers both content and source quality<br>
                    ✓ Balances recency with relevance
                </div>
            """, unsafe_allow_html=True)
            
            st.write("")  # Add some space
            left_col, center_col, right_col = st.columns([1, 1, 1])
            with center_col:
                if st.button("✕ Close", key="close_modal", use_container_width=True):
                    st.session_state.show_modal = False
                    st.rerun()

    st.write("Enter a financial institution name to search for adverse news and regulatory actions.")

    # Input fields
    fi_name = st.text_input("Financial Institution Name")
    num_results = st.slider("Number of top sources to analyze in detail", 1, 20, 10,
                          help="First, we'll quickly analyze all found sources. Then, we'll perform detailed analysis on this many top-scoring sources.")

    # Search button
    if st.button("Search and Analyze", key="search_button", use_container_width=True):
        if not fi_name:
            st.warning("Please enter a financial institution name.")
            return

        with st.spinner("Searching and analyzing..."):
            # Create search query
            query = create_search_query(fi_name)

            # Search for URLs
            urls = search_internet(query, num_results)

            if not urls:
                st.error("No results found.")
                return

            # Process sources
            analyses = process_sources(urls, num_results)

            # Generate report for UI display (without scoring explanation)
            report_for_ui = generate_markdown_report(fi_name, analyses, include_scoring_explanation=False)

            # Generate full report for PDF (with scoring explanation)
            full_report = generate_markdown_report(fi_name, analyses, include_scoring_explanation=True)

            # Display the report in the UI
            st.markdown(report_for_ui)

            # Add PDF download button
            pdf_content = convert_to_pdf(full_report, fi_name)
            if pdf_content:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.download_button(
                        label="📑 Download PDF Report",
                        data=pdf_content,
                        file_name=f"adverse_news_report_{fi_name}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

            st.write("---")

if __name__ == "__main__":
    main()
