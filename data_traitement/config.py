"""
Configuration pour le traitement des PDFs dans le pipeline RAG
"""

# Configuration pour le nettoyage des PDFs
CLEAN_CONFIG = {
    # Patterns pour détecter le début du contenu principal
    # Normalisés en minuscules, sans ponctuation
    "content_start_patterns": [
        "introduction",
        "part 1",
        "part i",
        "part one",
        "chapter 1",
        "chapter i",
        "chapter one",
        "preface",
    ],

    # Longueur minimum du contenu pour valider (en caractères)
    "min_content_length": 100,
}

# Chemins des répertoires
PATHS = {
    "input_pdfs": "c:/Users/Jordi/Desktop/DLproject/data",
    "output_texts": "c:/Users/Jordi/Desktop/DLproject/rag/data/cleaned",
    "chroma_db": "../chroma_db",
}

# OpenAI embedding model
EMBED_MODEL = "text-embedding-3-small"

# ChromaDB collection name
COLLECTION_NAME = "books"
