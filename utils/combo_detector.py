import time
from collections import deque

class ComboDetector:
    PUNCH_JAB = "jab"
    PUNCH_CROSS = "cross"
    PUNCH_HOOK = "hook"
    PUNCH_UPPERCUT = "uppercut"

    DEFAULT_COMBOS = [
        {
            'name': 'Jab-Cross',
            'sequence': [PUNCH_JAB, PUNCH_CROSS],
            'timing': [0.7]  # Max 0.7 seconds between Jab and Cross
        },
        {
            'name': 'Jab-Jab-Cross',
            'sequence': [PUNCH_JAB, PUNCH_JAB, PUNCH_CROSS],
            'timing': [0.5, 0.7] # Max 0.5s between J-J, Max 0.7s between J-C
        },
        {
            'name': 'Jab-Cross-Hook',
            'sequence': [PUNCH_JAB, PUNCH_CROSS, PUNCH_HOOK],
            'timing': [0.7, 0.7] # Max 0.7s between J-C, Max 0.7s between C-H
        },
        {
            'name': 'Hook-Cross-Hook',
            'sequence': [PUNCH_HOOK, PUNCH_CROSS, PUNCH_HOOK],
            'timing': [0.7, 0.7]
        }
    ]

    def __init__(self, predefined_combos=None):
        """
        Initializes the ComboDetector with a set of predefined combos.
        
        If no combos are provided, uses the default combos sorted by descending sequence length to prioritize longer combos during detection.
        """
        if predefined_combos is None:
            self.predefined_combos = sorted(self.DEFAULT_COMBOS, key=lambda c: len(c['sequence']), reverse=True)
        else:
            self.predefined_combos = sorted(predefined_combos, key=lambda c: len(c['sequence']), reverse=True)

    def detect_combo(self, punch_history):
        """
        Identifies and returns the name of a punch combo detected in the recent punch history.
        
        Examines the most recent punches and their timestamps to determine if they match any predefined combo sequence and timing constraints. Returns the combo name if a match is found; otherwise, returns None.
        
        Args:
            punch_history: A deque of (punch_type, timestamp) tuples ordered from oldest to newest.
        
        Returns:
            The name of the detected combo if matched; otherwise, None.
        """
        if not punch_history or len(punch_history) < 2:
            return None

        for combo in self.predefined_combos:
            combo_sequence = combo['sequence']
            combo_timings = combo['timing']

            # Check if the recent history is long enough for this combo
            if len(punch_history) < len(combo_sequence):
                continue

            # Take the most recent punches from history that match the length of the combo sequence
            relevant_history = list(punch_history)[-len(combo_sequence):]

            # Check punch sequence
            match = True
            for i, expected_punch in enumerate(combo_sequence):
                if relevant_history[i][0] != expected_punch:
                    match = False
                    break

            if not match:
                continue

            # Check timing
            # relevant_history is [(punch_type, timestamp), (punch_type, timestamp), ...]
            # combo_timings is [max_time_between_punch1_and_punch2, max_time_between_punch2_and_punch3, ...]
            # There is one less timing value than there are punches in the sequence.
            time_match = True
            epsilon = 1e-6 # Using a slightly larger epsilon
            for i in range(len(combo_timings)):
                time_diff = relevant_history[i+1][1] - relevant_history[i][1]
                if time_diff > (combo_timings[i] + epsilon):
                    time_match = False
                    break

            if time_match:
                # Combo detected
                return combo['name']

        return None

if __name__ == '__main__':
    # Example Usage and Basic Test
    detector = ComboDetector()

    # Test Case 1: Jab-Cross
    history1 = deque(maxlen=5)
    history1.append(("jab", time.time() - 0.5))
    history1.append(("cross", time.time()))
    print(f"History 1: {list(history1)}")
    detected1 = detector.detect_combo(history1)
    print(f"Detected Combo 1: {detected1}") # Expected: Jab-Cross

    # Test Case 2: Jab-Jab-Cross
    history2 = deque(maxlen=5)
    history2.append(("jab", time.time() - 1.0))
    history2.append(("jab", time.time() - 0.4))
    history2.append(("cross", time.time()))
    print(f"History 2: {list(history2)}")
    detected2 = detector.detect_combo(history2)
    print(f"Detected Combo 2: {detected2}") # Expected: Jab-Cross (Jab-Jab-Cross fails due to timing on J-J > 0.5s)

    # Test Case 3: Jab-Cross-Hook (Correct timing)
    history3 = deque(maxlen=5)
    history3.append(("jab", time.time() - 1.2))
    history3.append(("cross", time.time() - 0.6)) # 0.6s after jab
    history3.append(("hook", time.time()))     # 0.6s after cross
    print(f"History 3: {list(history3)}")
    detected3 = detector.detect_combo(history3)
    print(f"Detected Combo 3: {detected3}") # Expected: Jab-Cross-Hook

    # Test Case 4: Jab-Cross-Hook (Incorrect timing - too slow)
    history4 = deque(maxlen=5)
    history4.append(("jab", time.time() - 2.0))
    history4.append(("cross", time.time() - 0.8)) # 1.2s after jab (too slow for default J-C 0.7)
    history4.append(("hook", time.time()))     # 0.8s after cross
    print(f"History 4: {list(history4)}")
    detected4 = detector.detect_combo(history4)
    print(f"Detected Combo 4: {detected4}") # Expected: None

    # Test Case 5: Partial match (should not detect)
    history5 = deque(maxlen=5)
    history5.append(("jab", time.time() - 0.5))
    print(f"History 5: {list(history5)}")
    detected5 = detector.detect_combo(history5)
    print(f"Detected Combo 5: {detected5}") # Expected: None

    # Test Case 6: Different combo
    history6 = deque(maxlen=5)
    history6.append(("hook", time.time() - 1.0))
    history6.append(("cross", time.time() - 0.5))
    history6.append(("hook", time.time()))
    print(f"History 6: {list(history6)}")
    detected6 = detector.detect_combo(history6)
    print(f"Detected Combo 6: {detected6}") # Expected: Hook-Cross-Hook

    # Test Case 7: No match
    history7 = deque(maxlen=5)
    history7.append(("uppercut", time.time() - 1.0))
    history7.append(("jab", time.time() - 0.5))
    history7.append(("hook", time.time()))
    print(f"History 7: {list(history7)}")
    detected7 = detector.detect_combo(history7)
    print(f"Detected Combo 7: {detected7}") # Expected: None

    # Test Case 8: Empty history
    history8 = deque(maxlen=5)
    print(f"History 8: {list(history8)}")
    detected8 = detector.detect_combo(history8)
    print(f"Detected Combo 8: {detected8}") # Expected: None
