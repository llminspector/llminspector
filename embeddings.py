import os
import requests
import json
import hashlib
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
EMBEDDING_MODEL = 'text-embedding-3-small'
EMBEDDING_CACHE = {}

def get_embedding(text, model=EMBEDDING_MODEL):
    """
    Generate an embedding for the given text using OpenAI's API.
    Uses caching to avoid redundant API calls.

    Args:
        text (str): The text to embed
        model (str): The embedding model to use

    Returns:
        list: The embedding vector, or None if an error occurred
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")

    # Create a hash of the text for caching
    text_hash = hashlib.md5(text.encode()).hexdigest()
    cache_key = f"{model}:{text_hash}"

    # Check cache first
    if cache_key in EMBEDDING_CACHE:
        return EMBEDDING_CACHE[cache_key]

    # Call OpenAI API
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "input": text,
        "model": model
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        embedding = result['data'][0]['embedding']

        # Cache the result
        EMBEDDING_CACHE[cache_key] = embedding

        return embedding

    except requests.exceptions.RequestException as e:
        print(f"[!] Error generating embedding: {e}")
        return None


def cosine_similarity(vec1, vec2):
    """
    Calculate the cosine similarity between two vectors.

    Args:
        vec1 (list): First vector
        vec2 (list): Second vector

    Returns:
        float: Cosine similarity score between 0 and 1
    """
    if vec1 is None or vec2 is None:
        return 0.0

    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    # Calculate cosine similarity
    dot_product = np.dot(vec1, vec2)
    magnitude1 = np.linalg.norm(vec1)
    magnitude2 = np.linalg.norm(vec2)

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def compare_response_embeddings(responses1, responses2):
    """
    Compare two sets of responses using embeddings.
    Returns an average similarity score.

    Args:
        responses1 (list): List of response texts from first model
        responses2 (list): List of response texts from second model

    Returns:
        float: Average similarity score between 0 and 1
    """
    if not responses1 or not responses2:
        return 0.0

    # Generate embeddings for all responses
    embeddings1 = [get_embedding(resp) for resp in responses1]
    embeddings2 = [get_embedding(resp) for resp in responses2]

    # Filter out None values
    embeddings1 = [e for e in embeddings1 if e is not None]
    embeddings2 = [e for e in embeddings2 if e is not None]

    if not embeddings1 or not embeddings2:
        return 0.0

    # Calculate pairwise similarities and average them
    similarities = []
    for emb1 in embeddings1:
        for emb2 in embeddings2:
            sim = cosine_similarity(emb1, emb2)
            similarities.append(sim)

    return np.mean(similarities) if similarities else 0.0


def generate_aggregate_embedding(responses):
    """
    Generate a single aggregate embedding from multiple responses.
    This can be used to create a semantic "fingerprint" of a model.

    Args:
        responses (list): List of response texts

    Returns:
        list: Aggregate embedding vector (average of all response embeddings)
    """
    if not responses:
        return None

    embeddings = [get_embedding(resp) for resp in responses]
    embeddings = [e for e in embeddings if e is not None]

    if not embeddings:
        return None

    # Average all embeddings to create an aggregate
    return np.mean(embeddings, axis=0).tolist()


if __name__ == '__main__':
    # Test the module
    print("[*] Testing embeddings module...")

    test_text1 = "I am an AI assistant created by OpenAI."
    test_text2 = "I'm a helpful AI made by Anthropic."
    test_text3 = "I am an AI assistant created by OpenAI."

    print(f"[*] Generating embeddings...")
    emb1 = get_embedding(test_text1)
    emb2 = get_embedding(test_text2)
    emb3 = get_embedding(test_text3)

    if emb1 and emb2 and emb3:
        print(f"[+] Embedding dimension: {len(emb1)}")
        print(f"[*] Similarity between text1 and text2: {cosine_similarity(emb1, emb2):.4f}")
        print(f"[*] Similarity between text1 and text3: {cosine_similarity(emb1, emb3):.4f}")
        print("[+] Test successful!")
    else:
        print("[!] Test failed - could not generate embeddings")
