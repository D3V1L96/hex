import sqlite3
from datetime import datetime


class MemoryManager:
    def __init__(self, db_path="hex_memory.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    # -------------------- TABLES --------------------

    def _create_tables(self):
        # User profile (identity)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

        # Preferences (browser, apps, etc.)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            category TEXT,
            key TEXT,
            value TEXT,
            PRIMARY KEY (category, key)
        )
        """)

        # Habits (dynamic learning)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            intent TEXT,
            action TEXT,
            frequency INTEGER DEFAULT 1,
            last_used TEXT,
            PRIMARY KEY (intent, action)
        )
        """)

        # Decisions (clarifications, choices)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            context TEXT,
            choice TEXT,
            timestamp TEXT
        )
        """)

        # Response adaptation
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS response_style (
            intent TEXT PRIMARY KEY,
            style TEXT DEFAULT 'neutral',
            verbosity INTEGER DEFAULT 1
        )
        """)

        self.conn.commit()

    # -------------------- PROFILE --------------------

    def set_profile(self, key, value):
        self.cursor.execute(
            "INSERT OR REPLACE INTO user_profile VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()

    def get_profile(self, key):
        self.cursor.execute(
            "SELECT value FROM user_profile WHERE key=?",
            (key,)
        )
        row = self.cursor.fetchone()
        return row[0] if row else None

    # -------------------- PREFERENCES --------------------

    def set_preference(self, category, key, value):
        self.cursor.execute(
            "INSERT OR REPLACE INTO preferences VALUES (?, ?, ?)",
            (category, key, value)
        )
        self.conn.commit()

    def get_preference(self, category, key):
        self.cursor.execute(
            "SELECT value FROM preferences WHERE category=? AND key=?",
            (category, key)
        )
        row = self.cursor.fetchone()
        return row[0] if row else None

    # -------------------- HABITS --------------------

    def record_habit(self, intent, action):
        now = datetime.now().isoformat()
        self.cursor.execute(
            "SELECT frequency FROM habits WHERE intent=? AND action=?",
            (intent, action)
        )
        row = self.cursor.fetchone()

        if row:
            self.cursor.execute("""
            UPDATE habits
            SET frequency = frequency + 1, last_used=?
            WHERE intent=? AND action=?
            """, (now, intent, action))
        else:
            self.cursor.execute("""
            INSERT INTO habits (intent, action, frequency, last_used)
            VALUES (?, ?, 1, ?)
            """, (intent, action, now))

        self.conn.commit()

    def get_top_habit(self, intent):
        self.cursor.execute("""
        SELECT action FROM habits
        WHERE intent=?
        ORDER BY frequency DESC, last_used DESC
        LIMIT 1
        """, (intent,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    # -------------------- DECISIONS --------------------

    def remember_decision(self, context, choice):
        self.cursor.execute("""
        INSERT INTO decisions (context, choice, timestamp)
        VALUES (?, ?, ?)
        """, (context, choice, datetime.now().isoformat()))
        self.conn.commit()

    # -------------------- RESPONSE LEARNING --------------------

    def get_response_style(self, intent):
        self.cursor.execute(
            "SELECT style, verbosity FROM response_style WHERE intent=?",
            (intent,)
        )
        row = self.cursor.fetchone()
        return row if row else ("neutral", 1)

    def reinforce_response(self, intent, positive=True):
        style, verbosity = self.get_response_style(intent)

        if positive:
            verbosity = min(verbosity + 1, 3)
            style = "friendly"
        else:
            verbosity = max(verbosity - 1, 0)

        self.cursor.execute("""
        INSERT OR REPLACE INTO response_style (intent, style, verbosity)
        VALUES (?, ?, ?)
        """, (intent, style, verbosity))

        self.conn.commit()
