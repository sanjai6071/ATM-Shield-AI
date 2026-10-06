import sqlite3
import os

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

DB_PATH = os.path.join(
    BASE_DIR,
    "database",
    "incidents.db"
)
 

def create_database():

    connection = sqlite3.connect(DB_PATH)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            incident_time TEXT,

            threat_type TEXT,

            confidence REAL,

            threat_level TEXT,

            threat_score INTEGER,

            status TEXT,

            evidence_file TEXT

        )
    """)

    connection.commit()

    connection.close()

    print("✅ Incident database ready")


if __name__ == "__main__":
    create_database()

def add_incident(threat_type, confidence, threat_level, threat_score, status, evidence_file):

    connection = sqlite3.connect(DB_PATH)

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO incidents
        (incident_time, threat_type, confidence, threat_level, threat_score, status, evidence_file)
        VALUES (datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?)
    """, (
        threat_type,
        confidence,
        threat_level,
        threat_score,
        status,
        evidence_file
    ))

    connection.commit()
    connection.close()

    print("✅ Incident stored:", threat_type)

def get_incidents():

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM incidents
        ORDER BY id DESC
    """)

    incidents = cursor.fetchall()

    connection.close()

    return [dict(row) for row in incidents]