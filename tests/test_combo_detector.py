import unittest
import time
from collections import deque
from utils.combo_detector import ComboDetector # Assuming utils is in PYTHONPATH or accessible

class TestComboDetector(unittest.TestCase):

    def setUp(self):
        # Using default combos from the ComboDetector class for these tests
        """
        Initializes ComboDetector instances with default and custom combos for testing.
        
        Sets up self.detector with default combos and self.custom_detector with custom-defined combos for use in test cases.
        """
        self.detector = ComboDetector()
        # Test specific combos for more fine-grained tests if needed
        self.custom_combos = [
            {'name': 'Test-Jab-Cross', 'sequence': ['jab', 'cross'], 'timing': [0.5]},
            {'name': 'Test-Triple-Jab', 'sequence': ['jab', 'jab', 'jab'], 'timing': [0.3, 0.3]}
        ]
        self.custom_detector = ComboDetector(predefined_combos=self.custom_combos)

    def test_empty_history(self):
        """
        Tests that no combo is detected when the punch history is empty.
        """
        history = deque(maxlen=5)
        self.assertIsNone(self.detector.detect_combo(history))

    def test_history_too_short_for_any_combo(self):
        """
        Tests that no combo is detected when the punch history contains fewer punches than required for any combo.
        """
        history = deque(maxlen=5)
        history.append(('jab', time.time()))
        self.assertIsNone(self.detector.detect_combo(history))

    def test_simple_jab_cross_correct_timing(self):
        """
        Tests detection of the "Jab-Cross" combo when punches occur within the allowed timing interval.
        
        Verifies that the detector correctly identifies the "Jab-Cross" combo when a jab and cross are performed in sequence with a time gap less than or equal to the combo's timing constraint.
        """
        history = deque(maxlen=5)
        history.append((ComboDetector.PUNCH_JAB, time.time() - 0.4)) # 0.4s ago
        history.append((ComboDetector.PUNCH_CROSS, time.time()))    # now
        # Uses default combo: {'name': 'Jab-Cross', 'sequence': ['jab', 'cross'], 'timing': [0.7]}
        self.assertEqual(self.detector.detect_combo(history), 'Jab-Cross')

    def test_simple_jab_cross_too_slow(self):
        """
        Tests that the "Jab-Cross" combo is not detected when punches are spaced too far apart.
        
        Verifies that if the time interval between a jab and a cross exceeds the allowed threshold, no combo is detected.
        """
        history = deque(maxlen=5)
        history.append((ComboDetector.PUNCH_JAB, time.time() - 1.0))  # 1.0s ago
        history.append((ComboDetector.PUNCH_CROSS, time.time()))     # now
        # Default Jab-Cross timing is 0.7s
        self.assertIsNone(self.detector.detect_combo(history))

    def test_jab_jab_cross_correct_timing(self):
        """
        Tests detection of the "Jab-Jab-Cross" combo when punches occur within allowed timing intervals.
        
        Verifies that the detector correctly identifies the "Jab-Jab-Cross" combo when the sequence and timing constraints (0.5s between jabs, 0.7s between jab and cross) are satisfied.
        """
        history = deque(maxlen=7)
        history.append((ComboDetector.PUNCH_JAB, time.time() - 0.8)) # t0
        history.append((ComboDetector.PUNCH_JAB, time.time() - 0.4)) # t0 + 0.4s (within 0.5s for J-J)
        history.append((ComboDetector.PUNCH_CROSS, time.time()))    # t0 + 0.8s (0.4s after last J, within 0.7s for J-C)
        # Default: {'name': 'Jab-Jab-Cross', 'sequence': ['jab', 'jab', 'cross'], 'timing': [0.5, 0.7]}
        self.assertEqual(self.detector.detect_combo(history), 'Jab-Jab-Cross')

    def test_jab_jab_cross_first_timing_too_slow(self):
        """
        Tests that "Jab-Jab-Cross" is not detected if the first timing interval is too slow, but "Jab-Cross" is detected from the last two punches.
        """
        history = deque(maxlen=7)
        # Control timestamps precisely for testability
        base_time = time.time()
        history.append((ComboDetector.PUNCH_JAB, base_time - 1.0)) # t0
        history.append((ComboDetector.PUNCH_JAB, base_time - 0.3)) # t1 = t0 + 0.7s (too slow for J-J's 0.5s)
        history.append((ComboDetector.PUNCH_CROSS, base_time))    # t2 = t1 + 0.3s
        # Jab-Jab-Cross should fail. Jab-Cross (last two punches) should be detected.
        self.assertEqual(self.detector.detect_combo(history), 'Jab-Cross')

    def test_jab_jab_cross_second_timing_too_slow(self):
        """
        Tests that "Jab-Jab-Cross" is not detected when the second timing interval exceeds the allowed limit.
        
        Verifies that if the time between the second jab and the cross exceeds the combo's timing constraint, no combo is detected.
        """
        history = deque(maxlen=7)
        history.append((ComboDetector.PUNCH_JAB, time.time() - 1.0)) # t0
        history.append((ComboDetector.PUNCH_JAB, time.time() - 0.8)) # t0 + 0.2s (ok for J-J's 0.5s)
        history.append((ComboDetector.PUNCH_CROSS, time.time()))    # t0 + 1.0s (0.8s after last J, too slow for J-C's 0.7s)
        self.assertIsNone(self.detector.detect_combo(history))

    def test_incorrect_punch_type_in_sequence(self):
        """
        Tests that a combo is not detected when the punch sequence contains an incorrect punch type.
        
        Verifies that the detector does not recognize a "Jab-Cross" combo if the second punch is a hook instead of a cross.
        """
        history = deque(maxlen=5)
        history.append((ComboDetector.PUNCH_JAB, time.time() - 0.4))
        history.append((ComboDetector.PUNCH_HOOK, time.time())) # Should be CROSS for Jab-Cross
        self.assertIsNone(self.detector.detect_combo(history))

    def test_longer_history_ending_in_valid_combo(self):
        """
        Tests that a valid combo at the end of a longer punch history is correctly detected.
        
        Verifies that unrelated punches earlier in the history do not prevent detection of a valid "Jab-Cross" combo formed by the last two punches.
        """
        history = deque(maxlen=7)
        history.append((ComboDetector.PUNCH_UPPERCUT, time.time() - 2.0))
        history.append((ComboDetector.PUNCH_HOOK, time.time() - 1.5))
        history.append((ComboDetector.PUNCH_JAB, time.time() - 0.4)) # Start of Jab-Cross
        history.append((ComboDetector.PUNCH_CROSS, time.time()))    # End of Jab-Cross
        self.assertEqual(self.detector.detect_combo(history), 'Jab-Cross')

    def test_sub_combo_detection_priority(self):
        # DEFAULT_COMBOS are sorted by length descending in __init__
        # Jab-Jab-Cross vs Jab-Cross
        """
        Tests that longer combos are prioritized over shorter sub-combos when both could match.
        
        Verifies that the detector returns the longest valid combo ("Jab-Jab-Cross") when timing allows, and falls back to a shorter combo ("Jab-Cross") if the longer combo's timing constraints are not met.
        """
        history = deque(maxlen=7)
        # This sequence is a valid Jab-Jab-Cross
        history.append((ComboDetector.PUNCH_JAB, time.time() - 0.8)) # t0
        history.append((ComboDetector.PUNCH_JAB, time.time() - 0.4)) # t0 + 0.4s (J-J OK)
        history.append((ComboDetector.PUNCH_CROSS, time.time()))    # t0 + 0.8s (J-C OK)
        # Expected: Jab-Jab-Cross because it's longer and checked first
        self.assertEqual(self.detector.detect_combo(history), 'Jab-Jab-Cross')

        # This sequence is a valid Jab-Cross but NOT Jab-Jab-Cross due to first timing
        history2 = deque(maxlen=7)
        history2.append((ComboDetector.PUNCH_JAB, time.time() - 1.0)) # t0
        history2.append((ComboDetector.PUNCH_JAB, time.time() - 0.3)) # t0 + 0.7s (J-J too slow)
        history2.append((ComboDetector.PUNCH_CROSS, time.time()))    # t0 + 1.0s (J-C OK from last two punches)
        # Expected: Jab-Cross because Jab-Jab-Cross fails on timing
        self.assertEqual(self.detector.detect_combo(history2), 'Jab-Cross')


    def test_custom_combos_correct_timing(self):
        """
        Tests detection of a custom combo when punches occur within the allowed timing interval.
        
        Verifies that the custom "Test-Jab-Cross" combo is correctly detected when the punch sequence and timing constraints are satisfied.
        """
        history = deque(maxlen=5)
        history.append(('jab', time.time() - 0.3))
        history.append(('cross', time.time()))
        self.assertEqual(self.custom_detector.detect_combo(history), 'Test-Jab-Cross')

    def test_custom_combos_too_slow(self):
        """
        Tests that a custom combo is not detected when the timing between punches exceeds the allowed interval.
        """
        history = deque(maxlen=5)
        history.append(('jab', time.time() - 0.6)) # Custom timing is 0.5s
        history.append(('cross', time.time()))
        self.assertIsNone(self.custom_detector.detect_combo(history))

    def test_exact_timing_boundary(self):
        # Test with timing exactly at the boundary
        # Jab-Cross default timing is 0.7s
        # Construct timestamps to ensure exact difference
        """
        Tests that a combo is detected when the timing between punches is exactly at the allowed boundary.
        
        Verifies that the "Jab-Cross" combo is recognized when the interval between punches matches the maximum allowed timing constraint.
        """
        punch1_ts = time.time()
        punch2_ts = punch1_ts + 0.7 # Exact difference of 0.7

        history = deque(maxlen=5)
        history.append((ComboDetector.PUNCH_JAB, punch1_ts))
        history.append((ComboDetector.PUNCH_CROSS, punch2_ts))
        self.assertEqual(self.detector.detect_combo(history), 'Jab-Cross', "Should detect combo at exact timing boundary")

    def test_just_over_timing_boundary(self):
        # Test with timing just over the boundary
        # Construct timestamps to ensure exact difference
        """
        Tests that a combo is not detected when the timing between punches slightly exceeds the allowed boundary.
        """
        punch1_ts = time.time()
        punch2_ts = punch1_ts + 0.701 # Exact difference of 0.701

        history = deque(maxlen=5)
        history.append((ComboDetector.PUNCH_JAB, punch1_ts))
        history.append((ComboDetector.PUNCH_CROSS, punch2_ts))
        self.assertIsNone(self.detector.detect_combo(history), "Should not detect combo just over timing boundary")

if __name__ == '__main__':
    # This allows running the tests directly from this file
    # You might need to adjust PYTHONPATH if utils is not found:
    # Example: export PYTHONPATH=$PYTHONPATH:$(pwd)/.. (if tests is subdir of project root)
    unittest.main()
