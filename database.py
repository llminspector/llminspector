import sqlite3
import json

DB_PATH = 'fingerprints/fingerprints.db'

def init_db():
    """
    Initializes the database and creates/updates the fingerprints table.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Define all expected columns
    all_columns = {
        'model_name': 'TEXT PRIMARY KEY',
        'mentions_chatgpt': 'REAL',
        'mentions_openai': 'REAL',
        'mentions_meta': 'REAL',
        'jailbreak_successful': 'REAL',
        'dan_jailbreak_successful': 'REAL',
        'refusal_pattern': 'REAL',
        'math_correct': 'REAL',
        'json_correct': 'REAL',
        'logic_correct': 'REAL',
        'counting_correct': 'REAL',
        'markdown_correct': 'REAL',
        'yaml_correct': 'REAL',
        'bat_ball_correct': 'REAL',
        'js_floating_point_correct': 'REAL',
        'python_prime_correct': 'REAL'
    }

    # First, ensure the table exists with at least the primary key
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS fingerprints (
            model_name TEXT PRIMARY KEY
        )
    ''')

    # Get existing columns
    cursor.execute("PRAGMA table_info(fingerprints)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # Add any missing columns
    for col_name, col_type in all_columns.items():
        if col_name not in existing_columns:
            print(f"[*] Adding column '{col_name}' to fingerprints table.")
            cursor.execute(f"ALTER TABLE fingerprints ADD COLUMN {col_name} {col_type}")

    # Create response_embeddings table for storing semantic fingerprints
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS response_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            prompt_category TEXT,
            prompt_text TEXT,
            response_text TEXT,
            embedding TEXT,
            FOREIGN KEY (model_name) REFERENCES fingerprints(model_name)
        )
    ''')

    # Create index for faster lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_model_name
        ON response_embeddings(model_name)
    ''')

    conn.commit()
    conn.close()

def save_fingerprint(model_name, features):
    """
    Saves or updates a model's fingerprint in the database.
    'features' should be a dictionary with feature names as keys and scores as values.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    columns = ', '.join(features.keys())
    placeholders = ', '.join('?' for _ in features)
    values = list(features.values())
    
    # Use INSERT OR REPLACE to handle both new entries and updates
    query = f'''
        INSERT OR REPLACE INTO fingerprints (model_name, {columns})
        VALUES (?, {placeholders})
    '''
    
    cursor.execute(query, [model_name] + values)
    
    conn.commit()
    conn.close()

def load_fingerprints():
    """
    Loads all fingerprints from the database.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM fingerprints')
    rows = cursor.fetchall()
    
    conn.close()
    
    # Convert rows to a list of dictionaries
    return [dict(row) for row in rows]

def save_response_embeddings(model_name, responses_data):
    """
    Saves response embeddings for a model.

    Args:
        model_name (str): The name of the model
        responses_data (list): List of dicts with keys:
            - prompt_category (str)
            - prompt_text (str)
            - response_text (str)
            - embedding (list)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # First, delete any existing embeddings for this model
    cursor.execute('DELETE FROM response_embeddings WHERE model_name = ?', (model_name,))

    # Insert new embeddings
    for data in responses_data:
        embedding_json = json.dumps(data['embedding']) if data.get('embedding') else None
        cursor.execute('''
            INSERT INTO response_embeddings
            (model_name, prompt_category, prompt_text, response_text, embedding)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            model_name,
            data.get('prompt_category'),
            data.get('prompt_text'),
            data.get('response_text'),
            embedding_json
        ))

    conn.commit()
    conn.close()


def load_response_embeddings(model_name):
    """
    Loads all response embeddings for a given model.

    Args:
        model_name (str): The name of the model

    Returns:
        list: List of dicts containing response data and embeddings
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT prompt_category, prompt_text, response_text, embedding
        FROM response_embeddings
        WHERE model_name = ?
    ''', (model_name,))

    rows = cursor.fetchall()
    conn.close()

    # Convert to list of dicts and parse embeddings
    results = []
    for row in rows:
        data = dict(row)
        if data['embedding']:
            data['embedding'] = json.loads(data['embedding'])
        results.append(data)

    return results


def get_all_model_names_with_embeddings():
    """
    Returns a list of all model names that have embeddings stored.

    Returns:
        list: List of model names
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT model_name
        FROM response_embeddings
        ORDER BY model_name
    ''')

    rows = cursor.fetchall()
    conn.close()

    return [row[0] for row in rows]


if __name__ == '__main__':
    print("[*] Initializing database...")
    init_db()
    print("[+] Database initialized successfully at", DB_PATH)
