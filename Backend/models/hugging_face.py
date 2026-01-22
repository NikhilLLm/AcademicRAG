import os
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
        _hf_client_cache = InferenceClient(api_key=hf_token)

    return _hf_client_cache
def hugging_face_query_expand(
    text: str,
    model_name: str = "Qwen/Qwen2.5-7B-Instruct",
    temperature: float = 0.2,
) -> str:
    """
    Expand/rewrite text into a detailed academic-style query
    using DeepSeek-V3.2 via Hugging Face Inference API (chat completion).
    Returns a string suitable for embeddings.
    """
    if not text or not text.strip():
        return ""

    client = _get_hf_client()  # Make sure your HF token is set

    prompt = f"""
Rewrite the following search query into a detailed academic-style query.
Preserve domain-specific terms and expand with technical keywords in five to six senetence paragraph
-For generalize question try to understand what is it and then expand it correctly
-This whole pipeline is for research paper so keeping in mind always try to enhance query for generalize or vague query in some meaningful
-Also if technical terms are present do not consider it vague query 
:

{text}
"""

    # Call chat_completion API
    response = client.chat_completion(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=100,
    )

    # Extract the generated content
    if hasattr(response, "choices") and len(response.choices) > 0:
        return response.choices[0].message["content"].strip()
    elif isinstance(response, dict):
        return response.get("generated_text", "").strip()
    else:
        return str(response).strip()


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
    """
    Encode text to embeddings using Hugging Face Inference API.
    Expects STRING input.
    """
    # ✅ Better type checking and error message
    if not isinstance(text, str):
        raise TypeError(f"Expected string, got {type(text).__name__}: {text}")
    
    if not text or not text.strip():
        return []
    retries=3
    
    client = _get_hf_client()
    for attempt in range(retries): 
       try:
         embedding = client.feature_extraction(text, model=model_name)
         time.sleep(2 ** attempt)  # exponential backoff
       except Exception as e:
         raise RuntimeError(f"Failed to get embeddings: {e}")
    
    # Handle different shapes
    import numpy as np
    embedding_array = np.array(embedding)
    
    if embedding_array.ndim > 1:
        embedding_array = embedding_array.mean(axis=0)
    
    return embedding_array.tolist()
