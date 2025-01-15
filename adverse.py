"""Main application file for the Adverse News Search tool."""
import logging
import asyncio
import streamlit as st
from datetime import datetime
from src.utils.pdf_utils import convert_to_pdf
from src.services.search_service import create_search_query, search_internet
from src.utils.logging_config import setup_logging
from src.config.settings import setup_streamlit

async def main():
    """Main application function."""
    # Setup
    setup_logging()
    setup_streamlit()
    
    logging.warning("Starting main application...")
    logging.warning(f"Called from: {__file__}")
    
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
    
    with col1:
        st.image("static/logo.png", width=60)
        
    with col2:
        st.markdown("<h1 style='color: #4B4BC8; margin-left: -1rem; margin-top: -1rem'>Adverse News Search 🔍</h1>", unsafe_allow_html=True)

    st.write("Enter a financial institution name to search for adverse news and regulatory actions.")
    
    # Input fields
    fi_name = st.text_input("Enter Financial Institution Name", key="fi_name_input")
    
    # Sliders in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        months_interval = st.slider("Search Time Period (months)", 
                                  min_value=1, 
                                  max_value=24, 
                                  value=6,
                                  key="months_slider")
    
    with col2:
        num_results = st.slider("Number of Results", 
                              min_value=5, 
                              max_value=20, 
                              value=10,
                              help="Number of search results to analyze",
                              key="results_slider")

    # Search button
    if st.button("Search and Analyze", key="search_button", use_container_width=True):
        if not fi_name:
            st.warning("Please enter a financial institution name.")
            return

        with st.spinner("Searching and analyzing..."):
            try:
                # Create search query
                logging.warning(f"Creating search query for '{fi_name}' with {months_interval} months interval")
                query = create_search_query(fi_name, months_interval)
                
                if not query:
                    logging.warning("Query creation failed")
                    return
                    
                # Perform search with user-specified number of results
                logging.warning(f"Starting internet search with query: '{query}', num_results: {num_results}")
                search_results = await search_internet(query, num_results)
                
                if not search_results or not search_results['results']:
                    st.error("No results found in the specified time period.")
                    logging.warning("No results found")
                    return

                # Display overall summary
                summary = search_results['summary']
                st.markdown("---")
                st.markdown(f"### Overall Assessment")
                
                # Display decision box
                decision_color = "#28a745" if not summary['has_adverse_news'] else "#dc3545"
                st.markdown(
                    f"""
                    <div style="padding: 1rem; border-radius: 0.5rem; background-color: {decision_color}; color: white; margin-bottom: 1rem; text-align: center;">
                        <h4 style="margin: 0; color: white;">Adverse News: {'YES' if summary['has_adverse_news'] else 'NO'}</h4>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Display metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Articles", summary['total_articles'])
                with col2:
                    st.metric("Highest Risk Score", f"{summary['highest_risk_score']}/100")
                
                # Display summary
                st.markdown("#### Summary")
                st.markdown(f"_{summary['summary']}_")
                st.markdown("---")

                # Display individual results
                st.markdown("### Detailed Analysis")
                for i, result in enumerate(search_results['results'], 1):
                    with st.expander(f"🔍 {result['title']}", expanded=True):
                        analysis = result['analysis']
                        date_str = result.get('date', 'Date not available')
                        st.markdown(f"""
                        - **Risk Score**: {analysis['score']}/100
                        - **Source**: [{result['source']}]({result['link']})
                        - **Date**: {date_str}
                        - **Summary**: {analysis['summary']}
                        - **Reason**: {analysis['reason']}
                        """)
                
                # Add PDF export button
                if search_results['results']:
                    st.divider()
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        report_content = f"""# Adverse News Analysis Report
                                
## Executive Summary
Analysis performed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total results analyzed: {len(search_results['results'])}

Overall Assessment:
{summary['summary']}

Key Metrics:
- Total Articles: {summary['total_articles']}
- Highest Risk Score: {summary['highest_risk_score']}/100

## Detailed Findings

"""
                        for result in search_results['results']:
                            analysis = result['analysis']
                            date_str = result.get('date', 'Date not available')
                            report_content += f"""### {result['title']}
- **Date**: {date_str}
- **Source**: {result['source']} ({result['link']})
- **Risk Score**: {analysis['score']}/100
- **Summary**: {analysis['summary']}
- **Reason**: {analysis['reason']}

"""
                        # Generate PDF
                        pdf_buffer = convert_to_pdf(report_content)
                        
                        st.download_button(
                            "📄 Download PDF Report",
                            data=pdf_buffer,
                            file_name=f"adverse_news_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        logging.warning("PDF report generated and downloaded")

            except Exception as e:
                st.error(f"An error occurred during the search: {str(e)}")
                logging.error(f"Search error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
