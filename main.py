#!/usr/bin/env python
"""
PunchTracker - A TensorFlow and OpenCV application for tracking punch movements
"""
import os
import time
import cv2
import numpy as np
import tensorflow as tf
from datetime import datetime

from utils.pose_detector import PoseDetector
from utils.punch_counter import PunchCounter
from utils.ui_manager import UIManager
from utils.combo_detector import ComboDetector # Added
from utils.data_manager import DataManager
from utils.calibration import Calibrator

class PunchTracker:
    def __init__(self):
        # Initialize components
        """
        Initializes the PunchTracker application and its core components.
        
        Sets up pose detection, punch counting, UI management, data handling, calibration, and combo detection modules. Initializes combo detection state, application control flags, session timing, and camera configuration parameters.
        """
        self.pose_detector = PoseDetector()
        self.punch_counter = PunchCounter(self.pose_detector)
        self.ui_manager = UIManager()
        self.data_manager = DataManager()
        self.calibrator = Calibrator()
        
        # Combo Detection related attributes
        self.combo_detector = ComboDetector() # Uses default combos
        self.current_detected_combo = None
        self.last_combo_detected_time = 0
        self.combo_display_duration = 3.0  # seconds
        self.combo_stats = {
            'attempts': 0,
            'successes': 0,
            'detected_combos': {}
        }

        # Application state
        self.is_running = False
        self.is_calibrating = False
        self.show_debug = False
        self.is_paused = False
        self.session_start_time = None
        
        # Camera settings
        self.camera_id = 0
        self.frame_width = 640
        self.frame_height = 480
        self.cap = None
        
    def initialize_camera(self):
        """Initialize the webcam"""
        self.cap = cv2.VideoCapture(self.camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        if not self.cap.isOpened():
            raise ValueError("Could not open camera. Check if it's connected properly.")
    
    def start_session(self):
        """
        Starts a new punching session by resetting punch counters, combo detection state, and combo statistics, recording the session start time, and creating a new session record in the data manager.
        """
        self.session_start_time = datetime.now()
        self.punch_counter.reset_counter()
        # Reset combo stats for the new session
        self.current_detected_combo = None
        self.last_combo_detected_time = 0
        self.combo_stats = {'attempts': 0, 'successes': 0, 'detected_combos': {}}
        print("Combo stats reset for new session.")
        self.data_manager.create_new_session()
        print(f"New session started at {self.session_start_time}")
    
    def end_session(self):
        """
        Ends the current punching session and saves session statistics.
        
        Compiles session data including start time, duration, total punches, punch type counts, punches per minute, and combo statistics, then saves this information using the data manager.
        """
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        session_data = {
            'date': self.session_start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration': session_duration,
            'total_punches': self.punch_counter.total_count,
            'punch_types': self.punch_counter.get_punch_types_count(),
            'punches_per_minute': self.punch_counter.total_count / (session_duration / 60) if session_duration > 0 else 0,
            'combo_stats': self.combo_stats
        }
        self.data_manager.save_session_data(session_data)
        print(f"Session ended. {self.punch_counter.total_count} punches recorded over {session_duration:.1f} seconds.")
    
    def start_calibration(self):
        """Start the calibration process"""
        self.is_calibrating = True
        self.calibrator.start_calibration()
        print("Calibration started. Follow the on-screen instructions.")
    
    def process_frame(self, frame):
        """
        Processes a single webcam frame for pose detection, punch counting, combo detection, calibration, and UI updates.
        
        If the application is paused, updates the UI with current statistics without further processing. If calibration mode is active, processes calibration frames and applies calibration data upon completion. Otherwise, detects punches and checks for combos based on punch event history, updating combo statistics and providing visual feedback for detected punches. The UI is updated with punch and combo information, and pose visualization is overlaid if debug mode is enabled.
        
        Args:
            frame: The current video frame from the webcam.
        
        Returns:
            The processed frame with overlays and UI updates applied.
        """
        # Detect poses in the frame
        poses = self.pose_detector.detect_pose(frame)

        if self.is_paused:
            return self.ui_manager.update_display(
                frame,
                self.punch_counter.total_count,
                self.punch_counter.get_punch_types_count(),
                self.session_start_time,
                self.punch_counter.velocity_threshold,
                paused=True,
                current_detected_combo=self.current_detected_combo,
                last_combo_detected_time=self.last_combo_detected_time,
                combo_display_duration=self.combo_display_duration,
                combo_stats=self.combo_stats
            )
        
        if self.is_calibrating:
            # Handle calibration mode
            calibration_complete, frame = self.calibrator.process_calibration_frame(frame, poses)
            if calibration_complete:
                self.is_calibrating = False
                self.punch_counter.apply_calibration(self.calibrator.get_calibration_data())
                print("Calibration completed!")
        else:
            # Normal processing - detect punches
            punches_detected = self.punch_counter.detect_punches(poses)

            # Combo Detection Logic
            if len(self.punch_counter.punch_event_history) > 0:
                detected_combo_name = self.combo_detector.detect_combo(self.punch_counter.punch_event_history)

                if detected_combo_name:
                    if self.current_detected_combo != detected_combo_name or \
                       (time.time() - self.last_combo_detected_time > self.combo_display_duration):

                        print(f"COMBO DETECTED: {detected_combo_name}")
                        self.current_detected_combo = detected_combo_name
                        self.last_combo_detected_time = time.time()

                        self.combo_stats['successes'] += 1
                        self.combo_stats['detected_combos'][detected_combo_name] = \
                            self.combo_stats['detected_combos'].get(detected_combo_name, 0) + 1

                        self.punch_counter.punch_event_history.clear()
            
            # Add visual feedback if punches are detected
            if punches_detected:
                for punch_info in punches_detected:
                    punch_type, coords = punch_info
                    # Visual feedback for the punch
                    cv2.circle(frame, (int(coords[0]), int(coords[1])), 15, (0, 0, 255), -1)
            
            # Update the UI with the latest data
            frame = self.ui_manager.update_display(
                frame,
                self.punch_counter.total_count,
                self.punch_counter.get_punch_types_count(),
                self.session_start_time,
                self.punch_counter.velocity_threshold,
                paused=False,
                current_detected_combo=self.current_detected_combo,
                last_combo_detected_time=self.last_combo_detected_time,
                combo_display_duration=self.combo_display_duration,
                combo_stats=self.combo_stats
            )
            
            # Show debug visualization if enabled
            if self.show_debug:
                frame = self.pose_detector.draw_pose(frame, poses)
        
        return frame
    
    def run(self):
        """Main application loop"""
        self.initialize_camera()
        self.is_running = True
        self.start_session()
        
        try:
            while self.is_running:
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to grab frame from camera")
                    break
                
                # Mirror the frame for a more intuitive display
                frame = cv2.flip(frame, 1)
                
                # Process the current frame
                display_frame = self.process_frame(frame)
                
                # Display the resulting frame
                cv2.imshow('PunchTracker', display_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC key
                    break
                elif key == ord('c'):
                    self.start_calibration()
                elif key == ord('d'):
                    self.show_debug = not self.show_debug
                elif key == ord('r'):
                    self.start_session()
                elif key == ord('s'):
                    stats_image = self.ui_manager.generate_stats_graph(
                        self.data_manager.get_historical_data(),
                        self.punch_counter.get_punch_types_count()
                    )
                    cv2.imshow('Punch Statistics', stats_image)
                elif key == ord('p'):
                    self.is_paused = not self.is_paused
                elif key == ord('i'):
                    self.punch_counter.increase_sensitivity()
                elif key == ord('k'):
                    self.punch_counter.decrease_sensitivity()
        
        finally:
            # Cleanup
            self.end_session()
            if self.cap is not None:
                self.cap.release()
            cv2.destroyAllWindows()
            print("Application terminated")

if __name__ == "__main__":
    try:
        app = PunchTracker()
        app.run()
    except Exception as e:
        print(f"Error: {e}")