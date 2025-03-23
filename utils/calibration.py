"""
Calibration module for adjusting punch detection parameters
"""
import cv2
import numpy as np
import time

class Calibrator:
    def __init__(self):
        """Initialize calibration parameters"""
        self.is_calibrating = False
        self.calibration_stage = 0
        self.calibration_steps = [
            "Prepare for calibration (5 sec)",
            "Throw a few jabs and crosses",
            "Throw a few hooks",
            "Throw a few uppercuts",
            "Calibration complete!"
        ]
        self.step_durations = [5, 10, 10, 10, 3]  # seconds for each step
        self.step_start_time = None
        
        # Data collected during calibration
        self.punch_velocities = []
        self.punch_distances = []
        
        # Final calibration data
        self.calibration_data = {
            "velocity_multiplier": 1.0,
            "direction_adjust": 0.0,
            "threshold_adjust": 0.0
        }
    
    def start_calibration(self):
        """Start the calibration process"""
        self.is_calibrating = True
        self.calibration_stage = 0
        self.step_start_time = time.time()
        self.punch_velocities = []
        self.punch_distances = []
        print("Calibration started")
    
    def process_calibration_frame(self, frame, keypoints):
        """
        Process a frame during calibration
        
        Args:
            frame: Input video frame
            keypoints: Detected keypoints from pose detector
            
        Returns:
            Tuple of (calibration_complete, processed_frame)
        """
        # Calculate time elapsed in current step
        current_time = time.time()
        elapsed_time = current_time - self.step_start_time
        
        # Check if current step is complete
        if elapsed_time >= self.step_durations[self.calibration_stage]:
            self.calibration_stage += 1
            self.step_start_time = current_time
            
            # If all steps are complete, finish calibration
            if self.calibration_stage >= len(self.calibration_steps):
                self._process_calibration_data()
                return True, self._draw_calibration_status(frame)
        
        # Process keypoints for the current calibration stage
        if 1 <= self.calibration_stage <= 3:  # Stages for collecting punch data
            self._collect_calibration_data(keypoints)
        
        # Draw calibration status on frame
        return False, self._draw_calibration_status(frame)
    
    def _collect_calibration_data(self, keypoints):
        """Collect data during the punch calibration stages"""
        from utils.pose_detector import PoseDetector
        
        # Extract wrist positions and calculate distances and velocities
        pose_detector = PoseDetector()
        hand_keypoints = pose_detector.get_hand_keypoints(keypoints)
        
        # Process key points relevant to the current calibration stage
        # For now, just store the positions to calculate velocities later
        for hand_key in ["left_wrist", "right_wrist"]:
            keypoint = hand_keypoints.get(hand_key)
            if keypoint is not None:
                # In a real implementation, you would calculate velocities and 
                # other metrics here based on sequential frames
                self.punch_velocities.append(keypoint[2])  # Using confidence as a proxy for now
    
    def _process_calibration_data(self):
        """Process collected data to determine calibration parameters"""
        # Calculate velocity multiplier based on collected data
        if self.punch_velocities:
            avg_velocity = sum(self.punch_velocities) / len(self.punch_velocities)
            # Adjust velocity multiplier inversely to the avg velocity
            # Lower confidence should result in higher multiplier to make detection easier
            if avg_velocity > 0:
                self.calibration_data["velocity_multiplier"] = 1.5 / avg_velocity
            else:
                self.calibration_data["velocity_multiplier"] = 1.0
            
            # Cap the multiplier to reasonable range
            self.calibration_data["velocity_multiplier"] = max(0.5, min(2.0, self.calibration_data["velocity_multiplier"]))
        
        # In a real implementation, calculate direction_adjust and threshold_adjust
        # based on collected data
        print(f"Calibration completed: {self.calibration_data}")
        self.is_calibrating = False
    
    def _draw_calibration_status(self, frame):
        """Draw calibration status overlay on the frame"""
        h, w = frame.shape[:2]
        
        # Create overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 80), (0, 0, 0), -1)
        
        # Add transparency
        alpha = 0.7
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # Add calibration step text
        if self.calibration_stage < len(self.calibration_steps):
            current_step = self.calibration_steps[self.calibration_stage]
            
            # Show remaining time for current step
            elapsed_time = time.time() - self.step_start_time
            remaining_time = max(0, self.step_durations[self.calibration_stage] - elapsed_time)
            
            step_text = f"Step {self.calibration_stage + 1}/{len(self.calibration_steps)}: {current_step}"
            time_text = f"Time remaining: {int(remaining_time)}s"
            
            cv2.putText(frame, step_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, time_text, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add progress bar
            progress_width = int(w * (elapsed_time / self.step_durations[self.calibration_stage]))
            cv2.rectangle(frame, (0, 70), (progress_width, 80), (0, 255, 0), -1)
        
        return frame
    
    def get_calibration_data(self):
        """Get the calibration data"""
        return self.calibration_data