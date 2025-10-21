# backend.py

import config
import os
from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import vertexai
from vertexai.generative_models import GenerativeModel
import json

# Set Google credentials directly in the code
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.GCP_KEY_PATH

# --- 1. INITIALIZE CONNECTIONS ---
app = Flask(__name__)

# Initialize Elasticsearch client
try:
    print("Connecting to Elastic Cloud...")
    es_client = Elasticsearch(
        hosts=[config.ELASTIC_ENDPOINT],
        api_key=config.ELASTIC_API_KEY,
        request_timeout=30
    )
    print("Successfully connected to Elastic Cloud!")
except Exception as e:
    print(f"Elasticsearch connection failed: {e}")
    es_client = None

# Initialize Google Cloud Vertex AI
gemini_model = None
try:
    print("Initializing Vertex AI...")
    vertexai.init(project="chimera-475519", location="us-central1")
    # Using the latest stable model confirmed by documentation
    model_name = "gemini-2.5-pro"
    print(f"Attempting to load model: '{model_name}'...")
    gemini_model = GenerativeModel(model_name)
    print(f"✅ Successfully loaded model: '{model_name}'!")
except Exception as e:
    print(f"Vertex AI initialization failed: {e}")
    gemini_model = None

# --- 2. DEFINE THE /analyze ENDPOINT ---
@app.route("/analyze", methods=["POST"])
def analyze_sequence():
    if not es_client or not gemini_model:
        return jsonify({"error": "A backend service is not available"}), 500

    sequence = request.json.get('sequence', '')
    if not sequence:
        return jsonify({"error": "Missing 'sequence' in request body"}), 400

    print(f"Received sequence for analysis: {sequence[:50]}...")

    # --- STEP 3A: THREAT CONTEXT SEARCH & REFERENCE EXTRACTION ---
    threat_context = ""
    threat_references = []
    try:
        print("Searching for threat-related documents...")
        # FIX: Include size within the body
        search_body = {
            "size": 5,
            "query": {"match": {"content": sequence}}
        }
        # CORRECT INDEX NAME
        response = es_client.search(index="chimera-knowledge-base", body=search_body)
        hits = response['hits']['hits']

        if hits:
            print(f"Found {len(hits)} relevant documents for threat analysis.")
            for hit in hits[:3]: threat_context += hit['_source']['content'] + "\n---\n"
            for hit in hits:
                doc_id = hit['_id']
                if doc_id.startswith("paper_"): threat_references.append(f"PubMed ID: {doc_id.replace('paper_', '')}")
                elif doc_id.startswith("seq_"): threat_references.append(f"NCBI Accession: {doc_id.replace('seq_', '')}")
        else:
            threat_context = "No similar research was found in the database."
    except Exception as e:
        print(f"Elasticsearch search failed: {e}")
        threat_context = "Error during database search."

    # --- STEP 3B: GENERATE THREAT REPORT ---
    analysis_report = "Failed to generate AI threat analysis."
    try:
        print("Generating AI threat analysis...")
        threat_prompt = f"""
        Analyze the following pathogen feature based on the provided research context.
        **Pathogen Feature:**\n{sequence}\n**Relevant Research:**\n{threat_context}\n
        **TASK:** Generate a report with '### Summary', '### Threat Level', '### Rationale'. ONLY the report.
        """
        ai_response = gemini_model.generate_content(threat_prompt)
        analysis_report = ai_response.text.strip()
        print("Successfully generated threat report.")
    except Exception as e:
        print(f"Gemini threat analysis failed: {e}")

    # --- STEP 4A: KEYWORD EXTRACTION ---
    countermeasure_keywords = ""
    try:
        print("Extracting keywords for countermeasure search...")
        keyword_prompt = f"""
        Extract 3-5 key virological terms from the text below.
        **TASK:** Return ONLY a comma-separated string. Example: H5N1, furin cleavage site, coronavirus.
        **Text:**\n{sequence}
        """
        keyword_response = gemini_model.generate_content(keyword_prompt)
        countermeasure_keywords = keyword_response.text.strip()
        print(f"Extracted keywords: {countermeasure_keywords}")
    except Exception as e:
        print(f"Keyword extraction failed: {e}")

    # --- STEP 4B: COUNTERMEASURE CONTEXT SEARCH & REFERENCE EXTRACTION ---
    countermeasure_context = ""
    countermeasure_references = []
    if countermeasure_keywords:
        try:
            print("Searching for countermeasure-related documents...")
            full_query = f"({countermeasure_keywords}) AND (vaccine OR antiviral OR treatment)"
             # FIX: Include size within the body
            search_body = {
                "size": 5,
                "query": {"match": {"content": full_query}}
            }
             # CORRECT INDEX NAME
            response = es_client.search(index="chimera-knowledge-base", body=search_body)
            hits = response['hits']['hits']

            if hits:
                print(f"Found {len(hits)} relevant documents for countermeasures.")
                for hit in hits[:3]: countermeasure_context += hit['_source']['content'] + "\n---\n"
                for hit in hits:
                    doc_id = hit['_id']
                    if doc_id.startswith("paper_"): countermeasure_references.append(f"PubMed ID: {doc_id.replace('paper_', '')}")
            else:
                 countermeasure_context = "No countermeasure research found for these keywords."
        except Exception as e:
            print(f"Countermeasure search failed: {e}")
            countermeasure_context = "Error searching for countermeasure research."

    # --- STEP 4C: GENERATE COUNTERMEASURES REPORT ---
    countermeasures_report = "No countermeasure information found in the database."
    if countermeasure_context != "Error searching for countermeasure research." and countermeasure_context != "No countermeasure research found for these keywords.":
        try:
            print("Generating AI countermeasures summary...")
            countermeasure_prompt = f"""
            Summarize potential countermeasures for '{countermeasure_keywords}' based on the research below.
            **Relevant Research:**\n{countermeasure_context}\n
            **TASK:** Generate ONLY a brief markdown bulleted list.
            """
            countermeasure_response = gemini_model.generate_content(countermeasure_prompt)
            countermeasures_report = countermeasure_response.text.strip()
            print("Successfully generated countermeasures report.")
        except Exception as e:
            print(f"Gemini countermeasures analysis failed: {e}")
            countermeasures_report = "Failed to generate AI countermeasure summary."

    # --- 5. RETURN THE FINAL, COMBINED REPORT ---
    all_references = sorted(list(set(threat_references + countermeasure_references)))
    final_response = {
        "status": "success",
        "analysis_report": analysis_report,
        "countermeasures_report": countermeasures_report,
        "references": all_references[:5]
    }
    return jsonify(final_response)

# --- 6. RUN THE SERVER ---
if __name__ == "__main__":
    print("Starting Flask server on http://127.0.0.1:5000")
    # Run in production mode for stability
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

