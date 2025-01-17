"""Main application file for the Adverse News Search tool."""
import logging
import asyncio
import streamlit as st
from datetime import datetime
from src.utils.pdf_utils import convert_to_pdf
from src.services.search_service import (
    create_search_query,
    search_internet,
    analyze_results_summary
)
from src.utils.logging_config import setup_logging
from src.config.settings import setup_streamlit
import os

async def main():
    """Main application function."""
    # Setup
    setup_logging()
    setup_streamlit()

    logging.warning("Starting main application...")
    logging.warning(f"Called from: {__file__}")

    # Initialize session state
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'fi_name_saved' not in st.session_state:
        st.session_state.fi_name_saved = None
    if 'pdf_downloaded' not in st.session_state:
        st.session_state.pdf_downloaded = False

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
        </style>
    """, unsafe_allow_html=True)

    # Center the content
    col1, col2 = st.columns([0.2, 1.8])

    with col2:
        st.title("Adverse News Search")

        # Input fields
        fi_name = st.text_input("Enter Financial Institution Name:")

        # Search options in columns
        col_options1, col_options2, col_options3 = st.columns(3)
        with col_options1:
            months = st.number_input("Search Period (Last n Months):", min_value=1, max_value=24, value=6)
        with col_options2:
            min_score = st.slider("Minimum Risk Score:", min_value=0, max_value=100, value=50, step=5)
        with col_options3:
            num_results = st.number_input("Number of Results to analyze:", min_value=5, max_value=20, value=10, help="Maximum number of search results to analyze")

        # Search button
        if st.button("Search for Adverse News"):
            if fi_name:
                with st.spinner('Searching for adverse news...'):
                    # Create search query
                    query = create_search_query(fi_name, months)
                    st.info(f"🔍 Search query: `{query}`")
                    logging.warning(f"Generated search query: {query}")

                    # Perform search with minimum score threshold
                    raw_results = await search_internet(query, min_score=min_score, months=months, num_results=num_results)

                    # Filter results to only include those that mention the institution name
                    results = []
                    for result in raw_results:
                        title_match = fi_name.lower() in result['title'].lower()
                        snippet_match = fi_name.lower() in result['snippet'].lower()
                        if title_match or snippet_match:
                            results.append(result)
                        else:
                            logging.info(f"Filtered out result: {result['title']} (institution name not found)")

                    # Store results in session state
                    st.session_state.search_results = results
                    st.session_state.fi_name_saved = fi_name

                    if results:
                        # Log filtering results
                        st.info(f"Found {len(raw_results)} results, filtered to {len(results)} relevant matches.")
                        logging.warning(f"Filtered {len(raw_results) - len(results)} irrelevant results")
                        logging.warning(f"Remaining relevant results: {len(results)}")

                        # Create summary
                        summary = await analyze_results_summary(results)

                        # Display results
                        st.markdown("### Search Results")

                        # Display summary first
                        if summary.get("has_adverse_news"):
                            st.error(f"""
                            #### Risk Summary
                            - Highest Risk Score: {summary['highest_risk_score']}
                            - Total Articles: {summary['total_articles']}

                            {summary['summary']}
                            """)

                        # Display individual results
                        for result in results:
                            date_str = result.get('date', 'Date not available')
                            with st.expander(f"{result['title']} - Risk Score: {result['analysis']['score']} ({date_str})"):
                                st.markdown(f"""
                                **Source:** {result['source']}
                                **Date:** {date_str}
                                **Link:** [{result['link']}]({result['link']})

                                **Snippet:**
                                {result['snippet']}

                                **Analysis:**
                                {result['analysis'].get('reason', result['analysis'].get('summary', 'No analysis available'))}
                                """)
                    else:
                        st.info("No significant adverse news found within the specified criteria.")
            else:
                st.warning("Please enter a financial institution name.")

        # Show PDF section if we have results and haven't downloaded yet
        if st.session_state.search_results and not st.session_state.pdf_downloaded:
            st.markdown("---")
            st.markdown("### Download Report")

            # Generate PDF report option
            if st.button("📄 Generate PDF Report", key="generate_pdf"):
                logging.warning("PDF generation button clicked")
                with st.spinner("🔄 Generating PDF report..."):
                    try:
                        # Create filename with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"adverse_news_{st.session_state.fi_name_saved}_{timestamp}.pdf"
                        output_path = os.path.join(os.getcwd(), filename)
                        logging.warning(f"Will generate PDF at: {output_path}")

                        # Generate PDF
                        logging.warning("Starting PDF generation...")
                        pdf_path = convert_to_pdf(st.session_state.search_results, st.session_state.fi_name_saved, output_path)
                        logging.warning(f"PDF generated at: {pdf_path}")

                        # Read PDF file
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        logging.warning(f"Read {len(pdf_bytes)} bytes from PDF")

                        # Clean up the file
                        os.remove(pdf_path)
                        logging.warning("Temporary PDF file cleaned up")

                        # Store PDF in session state
                        st.session_state.pdf_bytes = pdf_bytes
                        st.session_state.pdf_filename = filename

                        # Show success message
                        st.success("✅ PDF generated successfully!")

                    except Exception as e:
                        st.error(f"❌ Error generating PDF: {str(e)}")
                        logging.error(f"PDF generation error: {str(e)}", exc_info=True)

            # Show download button if PDF was generated
            if hasattr(st.session_state, 'pdf_bytes'):
                if st.download_button(
                    label="⬇️ Download PDF Report",
                    data=st.session_state.pdf_bytes,
                    file_name=st.session_state.pdf_filename,
                    mime="application/pdf",
                    key="download_pdf"
                ):
                    # Set downloaded flag and clean up
                    st.session_state.pdf_downloaded = True
                    del st.session_state.pdf_bytes
                    del st.session_state.pdf_filename
                    st.rerun()  # Rerun to hide the section

if __name__ == "__main__":
    asyncio.run(main())
