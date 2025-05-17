"""
Punch Counter module for detecting and tracking punch movements
"""
import numpy as np
import time
import math
from collections import deque

class PunchCounter:
    # Punch types
    JAB = "jab"
    CROSS = "cross"
    HOOK = "hook"
    UPPERCUT = "uppercut"
    
    def __init__(self):
        # Counters for different punch types
        self.total_count = 0
        self.punch_counts = {
            self.JAB: 0,
            self.CROSS: 0,
            self.HOOK: 0,
            self.UPPERCUT: 0
        }
        
        # Track position history for velocity calculation
        self.position_history = {
            "left_wrist": deque(maxlen=10),
            "right_wrist": deque(maxlen=10)
        }
        
        # Timestamps for position history
        self.timestamp_history = {
            "left_wrist": deque(maxlen=10),
            "right_wrist": deque(maxlen=10)
        }
        
        # Cooldown to prevent rapid punch detections
        self.last_punch_time = {
            "left": 0,
            "right": 0
        }
        self.punch_cooldown = 0.5  # seconds
        
        # Punch detection parameters
        self.velocity_threshold = 50  # pixels per frame
        self.direction_threshold = 0.7  # cosine similarity threshold
        
        # Calibration adjustments
        self.calibration_data = {
            "velocity_multiplier": 1.0,
            "direction_adjust": 0.0
        }

    def increase_sensitivity(self, step=5):
        """Decrease velocity threshold to increase sensitivity"""
        self.velocity_threshold = max(5, self.velocity_threshold - step)

    def decrease_sensitivity(self, step=5):
        """Increase velocity threshold to decrease sensitivity"""
        self.velocity_threshold = self.velocity_threshold + step
    
    def reset_counter(self):
        """Reset all punch counters"""
        self.total_count = 0
        for punch_type in self.punch_counts:
            self.punch_counts[punch_type] = 0
    
    def get_punch_types_count(self):
        """Get the count of each punch type"""
        return self.punch_counts
    
    def apply_calibration(self, calibration_data):
        """Apply calibration adjustments"""
        self.calibration_data = calibration_data
        print(f"Applied calibration: {calibration_data}")
    
    def _calculate_velocity(self, positions, timestamps):
        """Calculate the velocity of a keypoint based on its position history"""
        if len(positions) < 2 or len(timestamps) < 2:
            return 0, None
        
        # Get the two most recent positions
        pos1 = positions[-2]
        pos2 = positions[-1]
        time1 = timestamps[-2]
        time2 = timestamps[-1]
        
        # Skip if positions are None
        if pos1 is None or pos2 is None:
            return 0, None
            
        # Calculate displacement
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        displacement = math.sqrt(dx*dx + dy*dy)
        
        # Calculate time difference
        dt = time2 - time1
        if dt == 0:
            return 0, None
            
        # Calculate velocity and direction
        velocity = displacement / dt
        direction = (dx/displacement, dy/displacement) if displacement > 0 else None
        
        # Apply calibration
        velocity *= self.calibration_data["velocity_multiplier"]
        
        return velocity, direction
    
    def _is_punch_motion(self, velocity, direction, hand):
        """Determine if a hand motion qualifies as a punch"""
        # Check velocity threshold
        if velocity < self.velocity_threshold:
            return False
            
        # Punches generally move forward (x-axis in mirrored view)
        # For left hand (right side of screen), x direction should be negative
        # For right hand (left side of screen), x direction should be positive
        if direction is None:
            return False
            
        forward_direction = direction[0] < 0 if hand == "left" else direction[0] > 0
        if not forward_direction:
            return False
            
        # Check cooldown to prevent multiple detections of the same punch
        current_time = time.time()
        if current_time - self.last_punch_time[hand] < self.punch_cooldown:
            return False
            
        # Update last punch time
        self.last_punch_time[hand] = current_time
        
        return True
    
    def _classify_punch_type(self, keypoints, hand, velocity):
        """
        Classify the type of punch based on hand position relative to shoulders and head
        
        Args:
            keypoints: Dictionary of keypoints
            hand: 'left' or 'right' indicating which hand threw the punch
            velocity: The velocity of the punch
            
        Returns:
            String indicating punch type (jab, cross, hook, uppercut)
        """
        wrist_key = f"{hand}_wrist"
        elbow_key = f"{hand}_elbow"
        shoulder_key = f"{hand}_shoulder"
        opposite_shoulder_key = "right_shoulder" if hand == "left" else "left_shoulder"
        
        # Get keypoints
        wrist = keypoints.get(wrist_key)
        elbow = keypoints.get(elbow_key)
        shoulder = keypoints.get(shoulder_key)
        opposite_shoulder = keypoints.get(opposite_shoulder_key)
        
        # Return default if keypoints are missing
        if None in (wrist, elbow, shoulder, opposite_shoulder):
            # Return cross for right hand (dominant hand), jab for left
            return self.CROSS if hand == "right" else self.JAB
        
        # Calculate vertical position of wrist relative to elbow
        wrist_above_elbow = wrist[1] < elbow[1]
        
        # Calculate horizontal position of wrist relative to shoulder
        wrist_outside_shoulder = wrist[0] < shoulder[0] if hand == "left" else wrist[0] > shoulder[0]
        
        # Detect if arm is extended (distance from wrist to shoulder)
        wrist_to_shoulder_dist = math.sqrt((wrist[0] - shoulder[0])**2 + (wrist[1] - shoulder[1])**2)
        elbow_to_shoulder_dist = math.sqrt((elbow[0] - shoulder[0])**2 + (elbow[1] - shoulder[1])**2)
        wrist_to_elbow_dist = math.sqrt((wrist[0] - elbow[0])**2 + (wrist[1] - elbow[1])**2)
        arm_length = elbow_to_shoulder_dist + wrist_to_elbow_dist
        arm_extension_ratio = wrist_to_shoulder_dist / arm_length if arm_length > 0 else 0
        
        is_extended = arm_extension_ratio > 0.8
        
        # Classify based on arm position
        if wrist_above_elbow and is_extended:
            return self.UPPERCUT
        elif wrist_outside_shoulder and not is_extended:
            return self.HOOK
        elif hand == "right" and is_extended:
            return self.CROSS
        else:
            return self.JAB
    
    def detect_punches(self, keypoints_list):
        """
        Detect punches from pose keypoints
        
        Args:
            keypoints_list: List of keypoints from the pose detector
            
        Returns:
            List of detected punches with type and coordinates
        """
        from utils.pose_detector import PoseDetector
        
        # Extract hand keypoints
        pose_detector = PoseDetector()
        hand_keypoints = pose_detector.get_hand_keypoints(keypoints_list)
        
        # Update position history
        current_time = time.time()
        for hand_key in ["left_wrist", "right_wrist"]:
            keypoint = hand_keypoints.get(hand_key)
            if keypoint is not None:
                self.position_history[hand_key].append((keypoint[0], keypoint[1]))
                self.timestamp_history[hand_key].append(current_time)
        
        # Detect punches from both hands
        detected_punches = []
        
        for hand, wrist_key in [("left", "left_wrist"), ("right", "right_wrist")]:
            # Calculate velocity and direction
            velocity, direction = self._calculate_velocity(
                self.position_history[wrist_key], 
                self.timestamp_history[wrist_key]
            )
            
            # Check if motion is a punch
            if self._is_punch_motion(velocity, direction, hand):
                # Classify punch type
                punch_type = self._classify_punch_type(hand_keypoints, hand, velocity)
                
                # Get wrist coordinates for visualization
                wrist_coords = self.position_history[wrist_key][-1]
                
                # Update counter
                self.punch_counts[punch_type] += 1
                self.total_count += 1
                
                # Add to detected punches
                detected_punches.append((punch_type, wrist_coords))
                
                print(f"Detected {punch_type.upper()} - Total punches: {self.total_count}")
        
        return detected_punches