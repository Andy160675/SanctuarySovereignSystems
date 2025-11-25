import os
import sys
from pathlib import Path
from txtai.embeddings import Embeddings
from tqdm import tqdm
import json
import re
from datetime import datetime

def clean_text(text):
    """Clean and preprocess text"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove non-printable characters except newlines and tabs
    text = re.sub(r'[^\x20-\x7E\n\t]', '', text)
    return text.strip()

def load_documents(corpus_path):
    """Load documents from corpus directory"""
    documents = []
    corpus = Path(corpus_path)
    
    # Supported file extensions
    extensions = {'.md', '.txt', '.py', '.ps1', '.yaml', '.yml', '.json'}
    
    for file_path in corpus.glob('**/*'):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Clean content
                content = clean_text(content)
                
                # Skip empty files
                if len(content.strip()) < 50:
                    continue
                
                # Create document with metadata
                doc = {
                    'text': content,
                    'path': str(file_path.relative_to(corpus)),
                    'filename': file_path.name,
                    'extension': file_path.suffix,
                    'size': len(content)
                }
                
                documents.append(doc)
                print(f"Loaded: {file_path.name} ({len(content)} chars)")
                
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    return documents

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python build_index.py <corpus_path> <index_path>")
        sys.exit(1)
    
    corpus_path = sys.argv[1]
    index_path = sys.argv[2]
    
    # Load documents
    print("Loading corpus documents...")
    documents = load_documents(corpus_path)
    print(f"Loaded {len(documents)} documents")

    if not documents:
        print("ERROR: No documents loaded!")
        sys.exit(1)

    # Create embeddings index
    print("\nCreating embeddings model...")
    embeddings = Embeddings({
        'path': 'sentence-transformers/all-MiniLM-L6-v2',
        'content': True,
        'transform': 'text'
    })

    # Index documents
    print("\nIndexing documents...")
    data = [(i, doc['text'], doc) for i, doc in enumerate(documents)]

    embeddings.index(data)

    # Save index
    os.makedirs(index_path, exist_ok=True)
    embeddings.save(index_path)

    # Save metadata
    metadata = {
        'total_documents': len(documents),
        'corpus_path': corpus_path,
        'created': str(datetime.now()),
        'files': [{'path': doc['path'], 'size': doc['size']} for doc in documents]
    }

    with open(f'{index_path}/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✅ Index built successfully!")
    print(f"📁 Index saved to: {index_path}")
    print(f"📊 Indexed {len(documents)} documents")