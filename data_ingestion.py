# data_ingestion.py

import config
import requests
from elasticsearch import Elasticsearch
import xml.etree.ElementTree as ET
from Bio import SeqIO
import io

# --- 1. CONFIGURATION ---
INDEX_NAME = "chimera-knowledge-base"

# --- 2. CONNECT TO ELASTICSEARCH ---
try:
    print("Connecting to Elastic Cloud...")
    client = Elasticsearch(
        hosts=[config.ELASTIC_ENDPOINT],
        api_key=config.ELASTIC_API_KEY,
        request_timeout=30
    )
    print("Successfully connected to Elastic Cloud!")
except Exception as e:
    print(f"Connection failed: {e}")
    exit()

# --- 3. FETCH DATA ---
def fetch_pubmed_data(query, max_results=200):
    """Fetches research paper abstracts from the PubMed API."""
    print(f"\n📚 Fetching papers from PubMed for query: '{query}'...")
    # ... (rest of the function is the same)
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    search_url = f"{base_url}esearch.fcgi?db=pubmed&term={query}&retmax={max_results}&retmode=json"
    try:
        search_response = requests.get(search_url)
        search_data = search_response.json()
        id_list = search_data["esearchresult"]["idlist"]
        if not id_list:
            print("No papers found.")
            return None
        print(f"Found {len(id_list)} paper IDs. Fetching details...")
        ids_str = ",".join(id_list)
        fetch_url = f"{base_url}efetch.fcgi?db=pubmed&id={ids_str}&retmode=xml"
        fetch_response = requests.get(fetch_url)
        print("Successfully fetched paper details.")
        return fetch_response.text
    except Exception as e:
        print(f"An error occurred while fetching from PubMed: {e}")
        return None

def fetch_ncbi_sequences(query):
    """Fetches viral genome sequences from the NCBI Nucleotide database."""
    # ... (This function is the same as before)
    print(f"\n🧬 Fetching sequences from NCBI for query: '{query}'...")
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    search_url = f"{base_url}esearch.fcgi?db=nuccore&term={query}&retmode=json"
    try:
        search_response = requests.get(search_url)
        search_data = search_response.json()
        id_list = search_data["esearchresult"]["idlist"]
        if not id_list:
            print("No sequences found.")
            return None
        print(f"Found {len(id_list)} sequence IDs. Fetching FASTA records...")
        ids_str = ",".join(id_list)
        fetch_url = f"{base_url}efetch.fcgi?db=nuccore&id={ids_str}&rettype=fasta&retmode=text"
        fetch_response = requests.get(fetch_url)
        print("Successfully fetched FASTA records.")
        return fetch_response.text
    except Exception as e:
        print(f"An error occurred while fetching from NCBI: {e}")
        return None

# --- 4. PARSE AND UPLOAD ALL DATA ---
def ingest_data(all_papers_xml, sequences_fasta):
    """Parses all data and uploads it to a single index."""
    print(f"\nUploading all data to index: '{INDEX_NAME}'...")
    
    if client.indices.exists(index=INDEX_NAME):
        print(f"Index '{INDEX_NAME}' found. Deleting for a fresh start...")
        client.indices.delete(index=INDEX_NAME)
    print(f"Creating new index: '{INDEX_NAME}'...")
    client.indices.create(index=INDEX_NAME)
    
    # Process and upload papers
    paper_count = 0
    if all_papers_xml:
        for papers_xml in all_papers_xml:
            if not papers_xml: continue
            root = ET.fromstring(papers_xml)
            for article in root.findall('./PubmedArticle'):
                try:
                    pmid = article.find('.//PMID').text
                    title = article.find('.//ArticleTitle').text
                    abstract_element = article.find('.//AbstractText')
                    abstract = abstract_element.text if abstract_element is not None else ""
                    doc = {
                        'doc_type': 'paper',
                        'content': f"Title: {title}. Abstract: {abstract}"
                    }
                    # Use a unique ID to prevent duplicates if papers overlap between queries
                    client.index(index=INDEX_NAME, id=f"paper_{pmid}", document=doc, op_type='create')
                    paper_count += 1
                except Exception:
                    continue
    print(f"Successfully indexed {paper_count} papers.")

    # Process and upload sequences
    sequence_count = 0
    if sequences_fasta:
        fasta_io = io.StringIO(sequences_fasta)
        for record in SeqIO.parse(fasta_io, "fasta"):
            doc = {
                'doc_type': 'sequence',
                'content': f"Definition: {record.description}. Sequence: {str(record.seq)}"
            }
            client.index(index=INDEX_NAME, id=f"seq_{record.id}", document=doc)
            sequence_count += 1
    print(f"Successfully indexed {sequence_count} sequences.")


# --- 5. MAIN EXECUTION ---
if __name__ == "__main__":
    # Query for general threats
    threat_query = "((avian influenza) OR (coronavirus)) AND (receptor binding OR spillover)"
    
    # NEW: Query for countermeasures
    countermeasure_query = "((coronavirus vaccine) OR (influenza antiviral) OR (broad-spectrum antiviral))"
    
    # Query for specific genomes
    sequence_query = "NC_045512.2[Accession] OR MN996532.1[Accession] OR AY651716[Accession]"
    
    # Fetch all data sources
    threat_papers = fetch_pubmed_data(query=threat_query)
    countermeasure_papers = fetch_pubmed_data(query=countermeasure_query)
    sequences = fetch_ncbi_sequences(query=sequence_query)

    # Ingest all data into Elasticsearch
    ingest_data([threat_papers, countermeasure_papers], sequences)
    print("\nData ingestion complete! Your knowledge base is now populated with threat and countermeasure data. 🚀")