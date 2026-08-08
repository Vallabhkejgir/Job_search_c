import sqlite3

DB_NAME = "linkedin_agent.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Table to track jobs we have seen and processed
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_jobs (
            job_id TEXT PRIMARY KEY,
            job_title TEXT,
            company_name TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_match BOOLEAN,
            match_reason TEXT
        )
    """)
    
    # Table to track people we have messaged
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messaged_users (
            profile_url TEXT PRIMARY KEY,
            name TEXT,
            company_name TEXT,
            job_id TEXT,
            messaged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def is_job_processed(job_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM processed_jobs WHERE job_id = ?", (job_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def log_job_processed(job_id, job_title, company_name, is_match, match_reason):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO processed_jobs (job_id, job_title, company_name, is_match, match_reason)
        VALUES (?, ?, ?, ?, ?)
    """, (job_id, job_title, company_name, is_match, match_reason))
    conn.commit()
    conn.close()

def is_user_messaged(profile_url):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM messaged_users WHERE profile_url = ?", (profile_url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def log_user_messaged(profile_url, name, company_name, job_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO messaged_users (profile_url, name, company_name, job_id)
        VALUES (?, ?, ?, ?)
    """, (profile_url, name, company_name, job_id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
