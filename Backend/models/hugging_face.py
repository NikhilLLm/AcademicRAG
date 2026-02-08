import os
os.environ["HF_ENDPOINT"] = "https://router.huggingface.co" # Global override
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import numpy as np

load_dotenv(".env")

_hf_client_cache = None

import time
def _get_hf_client():
    global _hf_client_cache

    if _hf_client_cache is None:
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise RuntimeError("HF_TOKEN not found in .env")

        print("🔌 Loading Hugging Face Inference Client...")
        _hf_client_cache = InferenceClient(
            api_key=hf_token,
            base_url="https://router.huggingface.co/hf-inference"
        )

    return _hf_client_cache

def hugging_face_query_expand(
    text: str,
    model_name: str = "Qwen/Qwen2.5-7B-Instruct",
    temperature: float = 0.2,
) -> str:

    if not text.strip():
        return ""

    client = _get_hf_client()

    prompt = f"""
Rewrite the following search query into a detailed academic-style query.
Preserve domain-specific terms and expand with technical keywords in a 5–6 sentence paragraph.
This is for research paper retrieval.

Query:
{text}
"""

    for attempt in range(5):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=250,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"⚠️ HF Query Expand Exception: {e}")
            if attempt == 4:
                return text
            time.sleep(2)

    return text



def hugging_face_llm(
    prompt: str,
    model_name: str,
    temperature: float,
) -> str:
    """
    Run text generation using Hugging Face Inference API.
    Returns STRING.
    """
    if not prompt or not prompt.strip():
        return ""

    client = _get_hf_client()

    output = client.text_generation(
        prompt,
        model=model_name,
        temperature=temperature,
    )

    return str(output)  # Ensure string


def hugging_face_embed(
    text: str,
    model_name: str = "sentence-transformers/all-mpnet-base-v2"
) -> list:
    
    if not isinstance(text, str):
        raise TypeError("Embedding input must be string")
    
    if not text.strip():
        return []
    
    client = _get_hf_client()
    
    for attempt in range(3):
        try:
            # Use feature_extraction for embeddings
            embedding = client.feature_extraction(
                text,
                model=model_name
            )
            
            # Convert to list if numpy array
            if isinstance(embedding, np.ndarray):
                return embedding.tolist()
            elif isinstance(embedding, list) and len(embedding) > 0:
                # Sometimes returns nested list
                if isinstance(embedding[0], list):
                    return embedding[0]
                return embedding
            return list(embedding)
            
        except Exception as e:
            print(f"⚠️ HF Embedding Exception: {e}")
            if attempt == 2:
                raise RuntimeError("Embedding failed") from e
            time.sleep(2 ** attempt)