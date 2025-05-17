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
from utils.data_manager import DataManager
from utils.calibration import Calibrator

class PunchTracker:
    def __init__(self):
        # Initialize components
        self.pose_detector = PoseDetector()
        self.punch_counter = PunchCounter()
        self.ui_manager = UIManager()
        self.data_manager = DataManager()
        self.calibrator = Calibrator()
        
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
        """Start a new punching session"""
        self.session_start_time = datetime.now()
        self.punch_counter.reset_counter()
        self.data_manager.create_new_session()
        print(f"New session started at {self.session_start_time}")
    
    def end_session(self):
        """End the current session and save data"""
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        session_data = {
            'date': self.session_start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration': session_duration,
            'total_punches': self.punch_counter.total_count,
            'punch_types': self.punch_counter.get_punch_types_count(),
            'punches_per_minute': self.punch_counter.total_count / (session_duration / 60) if session_duration > 0 else 0
        }
        self.data_manager.save_session_data(session_data)
        print(f"Session ended. {self.punch_counter.total_count} punches recorded over {session_duration:.1f} seconds.")
    
    def start_calibration(self):
        """Start the calibration process"""
        self.is_calibrating = True
        self.calibrator.start_calibration()
        print("Calibration started. Follow the on-screen instructions.")
    
    def process_frame(self, frame):
        """Process a single frame from the webcam"""
        # Detect poses in the frame
        poses = self.pose_detector.detect_pose(frame)

        if self.is_paused:
            return self.ui_manager.update_display(
                frame,
                self.punch_counter.total_count,
                self.punch_counter.get_punch_types_count(),
                self.session_start_time,
                self.punch_counter.velocity_threshold,
                paused=True
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
                paused=False
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