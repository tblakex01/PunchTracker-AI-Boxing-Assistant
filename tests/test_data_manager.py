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


def test_json_backup_write_failure(tmp_path, capsys):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    dm = DataManager(data_dir=data_dir)
    dm.create_new_session()
    session_data = {
        'date': '2023-01-01 00:00:00',
        'duration': 5.0,
        'total_punches': 2,
        'punch_types': {'jab': 2},
        'punches_per_minute': 24.0
    }

    os.chmod(data_dir, 0o500)
    dm.save_session_data(session_data)
    os.chmod(data_dir, 0o700)

    output = capsys.readouterr().out
    assert "Failed to write backup file" in output
    assert len(list(data_dir.glob('session_*.json'))) == 0
