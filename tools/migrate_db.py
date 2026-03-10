import sqlite3
import os

def migrate():
    db_path = 'moviehub.db'
    if not os.path.exists(db_path):
        print("Database file not found. Nothing to migrate.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Operator 컬럼 추가 시도
        print("Adding 'Operator' column to 'events' table...")
        cursor.execute("ALTER TABLE events ADD COLUMN Operator VARCHAR DEFAULT 'LOTTE'")
        conn.commit()
        print("Successfully added 'Operator' column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'Operator' already exists. Skipping.")
        else:
            print(f"Error adding column: {e}")

    # 2. 인덱스 추가 (성능 향상)
    try:
        print("Creating index on 'Operator'...")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_events_Operator ON events (Operator)")
        conn.commit()
        print("Index created.")
    except Exception as e:
        print(f"Error creating index: {e}")

    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
