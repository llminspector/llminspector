import argparse
import database
import core
import embeddings

def main():
    parser = argparse.ArgumentParser(
        description="Analyzes a known LLM to generate and save its fingerprint.",
        epilog="Example: python fingerprint_profiler.py --url http://localhost:11434/api/chat --model llama3:8b --save-as llama3-8b"
    )

    parser.add_argument("--url", type=str, required=True, help="The URL of the LLM API endpoint.")
    parser.add_argument("--model", type=str, required=True, help="The model name to use in the API request (for Ollama, etc.).")
    parser.add_argument("--save-as", type=str, required=True, help="The name under which to save the fingerprint in the database.")
    parser.add_argument("--prompts", type=str, default="prompts.json", help="Path to the JSON file with the prompt suite.")
    parser.add_argument("--runs", type=int, default=3, help="The number of times to run the test suite to create a stable, averaged fingerprint.")

    args = parser.parse_args()

    # Initialize the database
    database.init_db()

    # Run the test suite multiple times to gather a stable sample of features
    all_fingerprints = []
    all_responses = []  # Collect all responses for embedding generation

    for i in range(args.runs):
        print(f"\n--- Starting Run {i+1}/{args.runs} ---")
        fingerprint, responses_data = core.run_test_suite(args.url, args.model, args.prompts)
        if fingerprint:
            all_fingerprints.append(fingerprint)
            all_responses.extend(responses_data)  # Collect responses from each run

    if not all_fingerprints:
        print("[!] No fingerprints were generated after all runs. Aborting.")
        return

    # Average the fingerprints from all runs
    final_fingerprint = {}
    feature_keys = {key for fp in all_fingerprints for key in fp.keys()}

    for key in feature_keys:
        values = [fp.get(key, 0) for fp in all_fingerprints if fp.get(key) is not None]
        if values:
            final_fingerprint[key] = sum(values) / len(values)

    # Print and save the heuristic fingerprint
    print("\n--- Averaged Fingerprint ---")
    if not final_fingerprint:
        print("[!] No features were extracted. Nothing to save.")
        return

    for key, value in final_fingerprint.items():
        print(f"  {key}: {value:.2f}")

    database.save_fingerprint(args.save_as, final_fingerprint)
    print(f"\n[+] Heuristic fingerprint for '{args.save_as}' saved to database.")

    # Generate and save embeddings for semantic comparison
    print("\n[*] Generating embeddings for responses...")
    print(f"[*] Total responses to embed: {len(all_responses)}")

    responses_with_embeddings = []
    for i, response_data in enumerate(all_responses):
        if i % 10 == 0:  # Progress indicator every 10 responses
            print(f"  -> Progress: {i}/{len(all_responses)} embeddings generated...", end='\r')

        response_text = response_data['response_text']
        if response_text:  # Only generate embedding if there's text
            embedding = embeddings.get_embedding(response_text)
            if embedding:
                response_data['embedding'] = embedding
                responses_with_embeddings.append(response_data)

    print(f"\n[*] Generated {len(responses_with_embeddings)} embeddings successfully.")

    if responses_with_embeddings:
        database.save_response_embeddings(args.save_as, responses_with_embeddings)
        print(f"[+] Semantic embeddings for '{args.save_as}' saved to database.")
    else:
        print("[!] No embeddings were generated. Semantic comparison will not be available.")

    print(f"\n[+] Complete profile for '{args.save_as}' has been saved.")

if __name__ == "__main__":
    main()
