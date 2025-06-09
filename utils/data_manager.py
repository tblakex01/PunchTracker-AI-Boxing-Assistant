"""
Data Manager module for handling session data storage and retrieval
"""
import os
import json
import time
from datetime import datetime
import sqlite3

class DataManager:
    def __init__(self, data_dir="data"):
        """
        Initialize the data manager
        
        Args:
            data_dir: Directory to store data files
        """
        self.data_dir = os.path.abspath(data_dir)
        self.db_path = os.path.join(self.data_dir, "punch_sessions.db")
        self.current_session_id = None
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
            
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the SQLite database for storing session data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sessions table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            duration REAL,
            total_punches INTEGER,
            punches_per_minute REAL,
            jab_count INTEGER,
            cross_count INTEGER,
            hook_count INTEGER,
            uppercut_count INTEGER,
            combo_successes INTEGER DEFAULT 0,
            combo_attempts INTEGER DEFAULT 0,
            combo_details TEXT DEFAULT '{}'
        )
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"Database initialized at {self.db_path}")
    
    def create_new_session(self):
        """Create a new tracking session"""
        # Generate a unique session ID based on timestamp
        self.current_session_id = int(time.time())
        print(f"New session created with ID: {self.current_session_id}")
    
    def save_session_data(self, session_data):
        """
        Save session data to the database
        
        Args:
            session_data: Dictionary containing session information
        """
        if not session_data:
            print("No session data to save")
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract punch type counts
        punch_types = session_data.get('punch_types', {})
        
        # Insert session data into database
        cursor.execute('''
        INSERT INTO sessions 
        (date, duration, total_punches, punches_per_minute, jab_count, cross_count, hook_count, uppercut_count, combo_successes, combo_attempts, combo_details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_data['date'],
            session_data['duration'],
            session_data['total_punches'],
            session_data['punches_per_minute'],
            punch_types.get('jab', 0),
            punch_types.get('cross', 0),
            punch_types.get('hook', 0),
            punch_types.get('uppercut', 0),
            session_data.get('combo_stats', {}).get('successes', 0), # combo_successes
            session_data.get('combo_stats', {}).get('attempts', 0),  # combo_attempts
            json.dumps(session_data.get('combo_stats', {}).get('detected_combos', {})) # combo_details_json
        ))
        
        conn.commit()
        
        # Get the ID of the inserted row
        cursor.execute("SELECT last_insert_rowid()")
        session_id = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"Session data saved with ID: {session_id}")
        
        # Also save a JSON backup for easy debugging and portability
        self._save_json_backup(session_id, session_data)
    
    def _save_json_backup(self, session_id, session_data):
        """Save a JSON backup of the session data"""
        backup_file = os.path.join(self.data_dir, f"session_{session_id}.json")
        
        try:
            with open(backup_file, 'w') as f:
                json.dump(session_data, f, indent=4)
        except IOError as e:
            print(f"Failed to write backup file {backup_file}: {e}")
            return

        print(f"Session backup saved to {backup_file}")
    
    def get_historical_data(self, limit=10):
        """
        Retrieve historical session data from the database
        
        Args:
            limit: Maximum number of sessions to retrieve (default 10)
            
        Returns:
            List of session data dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get the most recent sessions
        cursor.execute('''
        SELECT date, duration, total_punches, punches_per_minute, 
               jab_count, cross_count, hook_count, uppercut_count,
               combo_successes, combo_attempts, combo_details
        FROM sessions
        ORDER BY date DESC
        LIMIT ?
        ''', (limit,))
        
        sessions = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        historical_data = []
        for session in sessions:
            historical_data.append({
                'date': session[0],
                'duration': session[1],
                'total_punches': session[2],
                'punches_per_minute': session[3],
                'punch_types': {
                    'jab': session[4],
                    'cross': session[5],
                    'hook': session[6],
                    'uppercut': session[7]
                },
                'combo_stats': {
                    'successes': session[8],
                    'attempts': session[9],
                    'detected_combos': json.loads(session[10]) if session[10] else {}
                }
            })
        
        return historical_data
    
    def get_stats_summary(self):
        """
        Generate a summary of all session statistics
        
        Returns:
            Dictionary with summary statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get aggregate statistics
        cursor.execute('''
        SELECT 
            COUNT(*) as total_sessions,
            SUM(total_punches) as total_punches,
            AVG(punches_per_minute) as avg_ppm,
            MAX(punches_per_minute) as max_ppm,
            SUM(jab_count) as total_jabs,
            SUM(cross_count) as total_crosses,
            SUM(hook_count) as total_hooks,
            SUM(uppercut_count) as total_uppercuts,
            SUM(duration) as total_duration,
            SUM(combo_successes) as total_combo_successes
        FROM sessions
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or result[0] == 0:
            return {
                'total_sessions': 0,
                'total_punches': 0,
                'avg_ppm': 0,
                'max_ppm': 0,
                'total_minutes': 0,
                'punch_distribution': {
                    'jab': 0,
                    'cross': 0,
                    'hook': 0,
                    'uppercut': 0
                },
                'total_combo_successes': 0
            }
        
        # Calculate the punch distribution percentages
        total_punches = result[1] or 1  # Avoid division by zero
        
        summary = {
            'total_sessions': result[0],
            'total_punches': result[1],
            'avg_ppm': result[2],
            'max_ppm': result[3],
            'total_minutes': result[8] / 60 if result[8] else 0,
            'punch_distribution': {
                'jab': (result[4] / total_punches) * 100 if result[4] else 0,
                'cross': (result[5] / total_punches) * 100 if result[5] else 0,
                'hook': (result[6] / total_punches) * 100 if result[6] else 0,
                'uppercut': (result[7] / total_punches) * 100 if result[7] else 0
            },
            'total_combo_successes': result[9] if result[9] is not None else 0
        }
        
        return summary