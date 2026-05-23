import time

_shared_model = None

def get_shared_embedding_model(model_name: str = "all-MiniLM-L6-v2"):
    global _shared_model
    if _shared_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print(f"[EMBEDDINGS] Initializing shared model: {model_name}...")
            start = time.time()
            _shared_model = SentenceTransformer(model_name)
            print(f"[EMBEDDINGS] Loaded shared model in {time.time() - start:.2f}s")
        except Exception as e:
            print(f"[EMBEDDINGS] Error loading model: {e}")
            _shared_model = None
    return _shared_model
