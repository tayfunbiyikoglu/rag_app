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
        </style>
    """, unsafe_allow_html=True)

    # Center the content
    col1, col2 = st.columns([0.2, 2])

    with col1:
        st.image("static/logo.png", width=60)

    with col2:
        st.markdown("<h1 style='color: #4B4BC8; margin-left: -1rem; margin-top: -1rem'>Financial Institution Adverse News Search 🔍</h1>", unsafe_allow_html=True)

    st.write("Enter a financial institution name to search for adverse news and regulatory actions.")

    # Add information expander
    with st.expander("ℹ️ Understanding Our Two-Phase Analysis System"):
        st.write("""
        Our adverse news analysis employs a sophisticated two-phase approach to ensure accurate and relevant results:

        **Phase 1: Initial Screening**
        - Quick analysis of content relevance and source credibility
        - Filters out obviously irrelevant or low-quality content
        - Helps prioritize the most significant findings

        **Phase 2: Detailed Analysis**

        For content that passes initial screening, we perform a detailed two-stage scoring:

        1️⃣ **Relevancy Assessment** (Primary Factor)
        - Evaluates how relevant the content is to adverse news
        - Score below 50: Content is not significantly relevant
        - Score 50+: Content contains meaningful adverse news information

        2️⃣ **Final Risk Score Calculation**
        For content passing the relevancy threshold:
        - 80% weight given to relevancy score
        - 20% weight given to source reliability

        This approach ensures that:
        - Only genuinely relevant adverse news gets highlighted
        - High reliability alone doesn't inflate scores of non-relevant content
        - Focus remains on actual adverse news findings rather than peripheral mentions

        **Understanding the Scores:**
        - Overall Risk Score: Final assessment combining relevancy and reliability
        - Relevancy Score: How significant the adverse news content is
        - Reliability Score: How trustworthy the source is
        """)

    # User inputs
    fi_name = st.text_input("Financial Institution Name")
    num_results = st.slider("Number of top sources to analyze in detail", 1, 20, 10,
                          help="First, we'll quickly analyze all found sources. Then, we'll perform detailed analysis on this many top-scoring sources.")

    if st.button("Search and Analyze"):
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
