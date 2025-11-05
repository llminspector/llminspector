import argparse
import database
import core
import embeddings
import math
import numpy as np

def compare_fingerprints(live_fingerprint, known_fingerprint):
    """
    Compares a live fingerprint with a known one from the database.
    Returns a similarity score between 0 and 1 (heuristic-based).
    """
    total_distance = 0
    common_features = 0

    for key, known_value in known_fingerprint.items():
        if key == 'model_name':
            continue

        live_value = live_fingerprint.get(key)

        # Only compare features that are present in both and were triggered
        if live_value is not None and known_value is not None:
            total_distance += (live_value - known_value) ** 2
            common_features += 1

    if common_features == 0:
        return 0

    # Calculate Root Mean Square Error (RMSE)
    rmse = math.sqrt(total_distance / common_features)

    # Convert RMSE to a similarity score (0-1). 1 - RMSE is a simple way.
    # This assumes the values are normalized between 0 and 1.
    similarity = 1 - rmse
    return max(0, similarity) # Ensure similarity is not negative


def compare_semantic_embeddings(live_embeddings, known_embeddings):
    """
    Compares semantic embeddings between live responses and known model responses.
    Returns a similarity score between 0 and 1 (embedding-based).

    Args:
        live_embeddings (list): List of embedding vectors from live responses
        known_embeddings (list): List of embedding vectors from known model

    Returns:
        float: Average cosine similarity score
    """
    if not live_embeddings or not known_embeddings:
        return 0.0

    # Calculate pairwise cosine similarities
    similarities = []
    for live_emb in live_embeddings:
        for known_emb in known_embeddings:
            sim = embeddings.cosine_similarity(live_emb, known_emb)
            similarities.append(sim)

    # Return average similarity
    return np.mean(similarities) if similarities else 0.0


def main():
    parser = argparse.ArgumentParser(
        description="Identifies the underlying LLM of an API endpoint by comparing its fingerprint to a known database.",
        epilog="Example: python llmfinder.py --url https://api.example.com/chat"
    )

    parser.add_argument("--url", type=str, required=True, help="The URL of the LLM API endpoint to fingerprint.")
    parser.add_argument("--model-in-payload", type=str, default="default", help="The model name to use in the API request payload (required by some APIs like Ollama).")
    parser.add_argument("--prompts", type=str, default="prompts.json", help="Path to the JSON file for the prompt suite.")
    parser.add_argument("--heuristic-weight", type=float, default=0.5, help="Weight for heuristic score (0-1). Semantic weight = 1 - heuristic_weight.")
    parser.add_argument("--no-embeddings", action="store_true", help="Disable semantic embedding comparison (use only heuristics).")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose/debug output for detailed logging.")

    args = parser.parse_args()

    # Enable verbose mode in all modules if requested
    if args.verbose:
        print("[*] Verbose mode enabled")
        core.set_verbose(True)
        database.set_verbose(True)
        embeddings.set_verbose(True)

    # 1. Generate the live fingerprint from the target URL
    live_fingerprint, live_responses = core.run_test_suite(args.url, args.model_in_payload, args.prompts)

    if not live_fingerprint:
        print("[!] Could not generate a fingerprint for the target. Aborting.")
        return

    # print("\n--- Live Fingerprint (Heuristic) ---")
    # for key, value in live_fingerprint.items():
    #     print(f"  {key}: {value:.2f}")

    # 2. Generate embeddings for live responses (if enabled)
    live_embeddings = []
    if not args.no_embeddings:
        print("\n[*] Generating embeddings for live responses...")
        for i, response_data in enumerate(live_responses):
            if i % 10 == 0:
                print(f"  -> Progress: {i}/{len(live_responses)} embeddings generated...", end='\r')

            response_text = response_data['response_text']
            if response_text:
                embedding = embeddings.get_embedding(response_text)
                if embedding:
                    live_embeddings.append(embedding)

        print(f"\n[+] Generated {len(live_embeddings)} embeddings for live responses.")

    # 3. Load all known fingerprints from the database
    known_fingerprints = database.load_fingerprints()
    if not known_fingerprints:
        print("\n[!] The fingerprint database is empty. Use fingerprint_profiler.py to add entries.")
        return

    # 4. Compare the live fingerprint against each known one
    scores = []
    for known in known_fingerprints:
        # Calculate heuristic similarity
        heuristic_score = compare_fingerprints(live_fingerprint, known)

        # Calculate semantic similarity (if enabled and available)
        semantic_score = 0.0
        if not args.no_embeddings and live_embeddings:
            known_response_data = database.load_response_embeddings(known['model_name'])
            if known_response_data:
                known_embeddings = [r['embedding'] for r in known_response_data if r.get('embedding')]
                if known_embeddings:
                    semantic_score = compare_semantic_embeddings(live_embeddings, known_embeddings)

        # Calculate hybrid score
        if args.no_embeddings or not live_embeddings or semantic_score == 0.0:
            # Fallback to heuristic-only if embeddings not available
            final_score = heuristic_score
            semantic_score = None  # Indicate not available
        else:
            heuristic_weight = args.heuristic_weight
            semantic_weight = 1 - heuristic_weight
            final_score = (heuristic_weight * heuristic_score) + (semantic_weight * semantic_score)

        scores.append({
            'model_name': known['model_name'],
            'heuristic_score': heuristic_score,
            'semantic_score': semantic_score,
            'final_score': final_score
        })

    # 5. Sort and display the results
    scores.sort(key=lambda x: x['final_score'], reverse=True)

    print("\n--- Match Results (Hybrid Scoring) ---")
    if not args.no_embeddings and live_embeddings:
        print(f"Weighting: {args.heuristic_weight:.0%} Heuristic + {(1-args.heuristic_weight):.0%} Semantic\n")

    for score in scores:
        model_name = score['model_name']
        final = score['final_score']
        heuristic = score['heuristic_score']
        semantic = score['semantic_score']

        if semantic is not None:
            print(f"  - Model: {model_name:<25} | Final: {final:.2%} (Heuristic: {heuristic:.2%}, Semantic: {semantic:.2%})")
        else:
            print(f"  - Model: {model_name:<25} | Final: {final:.2%} (Heuristic only)")


if __name__ == "__main__":
    main()
