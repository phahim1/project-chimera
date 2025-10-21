# app.py

import streamlit as st
import requests

# --- CONFIGURATION ---
BACKEND_URL = "http://127.0.0.1:5000/analyze"

# --- USER INTERFACE ---

# Set the page title and a descriptive header
st.set_page_config(page_title="Project Chimera", layout="wide")
st.title("🛡️ Chimera Sentinel: AI Threat & Countermeasure Analysis")
st.write("This tool uses AI to scan biomedical research to identify potential threats and suggest evidence-based countermeasures.")

# Create a text area for user input
sequence_input = st.text_area("Enter Pathogen Feature for Analysis:", height=150, placeholder="e.g., A new strain of avian influenza H5N1 with a novel furin cleavage site...")

# Create a button to trigger the analysis
if st.button("Run Full Analysis", type="primary"):
    if sequence_input:
        # Show a spinner with a more descriptive message
        with st.spinner("Executing multi-stage analysis... Identifying threat, extracting keywords, searching countermeasures, and compiling references..."):
            try:
                # Prepare the data and send the request to the Flask backend
                payload = {"sequence": sequence_input}
                response = requests.post(BACKEND_URL, json=payload, timeout=90) 
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # --- DISPLAY THREAT ANALYSIS REPORT ---
                    st.subheader("Threat Analysis Report")
                    analysis_report = response_data.get("analysis_report", "No report generated.")
                    st.markdown(analysis_report)

                    # --- DISPLAY COUNTERMEASURES REPORT ---
                    st.subheader("Suggested Countermeasures Report")
                    countermeasures_report = response_data.get("countermeasures_report", "No countermeasure information found.")
                    st.markdown(countermeasures_report)

                    # --- NEW: DISPLAY REFERENCES ---
                    references = response_data.get("references", [])
                    if references:
                        st.subheader("📚 Supporting References")
                        st.write("The analysis and suggestions above are based on information synthesized from the following sources:")
                        for ref in references:
                            # Make PubMed IDs clickable links
                            if "PubMed ID:" in ref:
                                pmid = ref.split(":")[-1].strip()
                                link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                                st.markdown(f"- [{ref}]({link})")
                            # Make NCBI Accessions clickable links
                            elif "NCBI Accession:" in ref:
                                acc = ref.split(":")[-1].strip()
                                link = f"https://www.ncbi.nlm.nih.gov/nuccore/{acc}"
                                st.markdown(f"- [{ref}]({link})")
                            else:
                                st.markdown(f"- {ref}") # Fallback for other ID types
                    
                else:
                    # Show an error message if something went wrong
                    error_message = response.json().get("error", "An unknown error occurred.")
                    st.error(f"Error from backend: {error_message}")

            except requests.exceptions.ConnectionError:
                st.error("Connection Error: Could not connect to the backend. Is the server running?")
            except requests.exceptions.Timeout:
                st.error("Request Timed Out: The multi-stage analysis is taking longer than expected. Please try again.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
    else:
        # Show a warning if the user clicks the button with no input
        st.warning("Please enter a pathogen feature to analyze.")
    
    