import os
import sqlite3
import tempfile

from utils.data_manager import DataManager

def test_create_and_save_session():
    with tempfile.TemporaryDirectory() as tmpdir:
        dm = DataManager(data_dir=tmpdir)
        dm.create_new_session()
        session_data = {
            'date': '2023-01-01 00:00:00',
            'duration': 10.0,
            'total_punches': 5,
            'punch_types': {'jab': 2, 'cross': 3},
            'punches_per_minute': 30.0
        }
        dm.save_session_data(session_data)
        hist = dm.get_historical_data()
        assert len(hist) == 1
        assert hist[0]['total_punches'] == 5
