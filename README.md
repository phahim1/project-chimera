# **Chimera Sentinel: AI Threat & Countermeasure Analysis**

An AI-powered system that scans biomedical research to identify emerging pathogen threats, suggest countermeasures, and provide supporting scientific references.

## Problem Solved
Keeping up with the vast amount of biomedical research to identify potential pandemic threats is a monumental task. Manually searching, reading, and synthesizing information across thousands of papers is slow and risks missing critical connections.

## Solution
Chimera Sentinel automates this process using a multi-stage AI pipeline:
1.  **Knowledge Base:** Ingests research papers (PubMed) and genomic sequences (NCBI) into an Elasticsearch index.
2.  **Threat Analysis:** Uses Google Gemini (via Vertex AI) to analyze a user query against relevant documents retrieved from Elasticsearch, generating a structured threat assessment (Summary, Threat Level, Rationale).
3.  **Countermeasure Suggestion:** Extracts keywords from the query, performs a targeted search for relevant vaccine/antiviral research, and uses Gemini to synthesize potential countermeasures.
4.  **References:** Provides citations (PubMed IDs, NCBI Accessions) for the documents used in the analysis.

## Key Features
* AI-Generated Threat Analysis Report
* AI-Generated Countermeasure Suggestions
* Supporting References with Clickable Links
* Web-Based Interface (Streamlit)

## Tech Stack
* **AI:** Google Cloud Vertex AI (Gemini 1.0 Pro)
* **Search:** Elasticsearch
* **Backend:** Python, Flask
* **Frontend:** Streamlit
* **Data Sources:** NCBI E-utils (PubMed, Nucleotide)
* **Libraries:** Biopython, Pandas, Requests

## How to Run
1.  Clone the repository: `git clone https://github.com/phahim1/project-chimera.git`
2.  Navigate to the directory: `cd project-chimera`
3.  Install requirements: `pip install -r requirements.txt`
4.  Add your Elastic Cloud Endpoint/API Key and Google Cloud Service Account JSON key path to `config.py`. Ensure the `.json` key file is in the project directory (and listed in `.gitignore`).
5.  Run data ingestion (only needs to be done once): `python data_ingestion.py`
6.  Run the backend server: `python backend.py`
7.  In a separate terminal, run the frontend app: `streamlit run app.py`
8.  Open the local URL provided by Streamlit in your browser.

## Demo Video
* Watch our **short video demonstration** showcasing Chimera Sentinel analyzing a potential threat, generating countermeasures, and providing references: [https://www.youtube.com/watch?v=c_SwUdnzrBY](https://www.youtube.com/watch?v=c_SwUdnzrBY)
 

## Future Work
* Integrate real-time monitoring of news feeds or public health alerts for earlier signal detection.
* Develop more sophisticated visualization for identified threats and countermeasures.

* ## License
This project is licensed under the MIT License. See the LICENSE file for details.




