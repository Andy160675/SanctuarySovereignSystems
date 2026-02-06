# Sovereign Search: Full Functionality & Options

The **Blade of Truth** provides a sophisticated, hybrid search engine for evidence verification and policy auditing. This document details the search capabilities and the "Full Search" options now available across the system.

## 1. Search Substrate
The search engine is powered by **txtai**, using a hybrid approach that combines:
- **Vector Search**: Semantic understanding using `nomic-embed-text-v1.5`.
- **BM25 Search**: Traditional keyword relevance.

## 2. Functionality Options

### Alpha (Hybrid Weight)
- **Parameter**: `alpha` (float, 0.0 to 1.0)
- **Description**: Controls the balance between Vector and Keyword search.
- **0.0**: 100% Keyword (BM25) - best for exact names, IDs, or rare terms.
- **1.0**: 100% Vector (Semantic) - best for concepts, themes, or similar meanings.
- **0.5 (Default)**: Balanced hybrid search.

### Limit
- **Parameter**: `limit` (integer, 1 to 50)
- **Description**: The maximum number of results to return. Default is 7.

### Min Score
- **Parameter**: `min_score` (float, 0.0 to 1.0)
- **Description**: Filters out results with a confidence score lower than this value. Useful for pruning low-relevance noise.

## 3. Interfaces

### Governance Cockpit (Streamlit)
- **Location**: `Boardroom UI -> Truth`
- **Features**: Global search bar on dashboard, dedicated Truth page with result expanders and source metadata.

### Boardroom Shell (Electron)
- **Location**: `Truth Tab`
- **Features**: Advanced controls for **Limit**, **Alpha**, and **Min Score**. Real-time search feedback via the EventRelay system.

### API (FastAPI)
- **Endpoint**: `GET /search?q={query}&limit=10&alpha=0.5&min_score=0.1`
- **Service**: `truth-engine` (Port 5050 or 8001)

## 4. Searchable Metadata
The following metadata is indexed and searchable (via SQL-like syntax if enabled, or keyword matching):
- `filename`
- `extension`
- `path`
- `size`
- `created_utc`

---
*The Blade of Truth doesn't just find documents; it understands the evidence.*
