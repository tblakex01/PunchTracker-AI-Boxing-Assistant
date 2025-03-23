"""
Pose Detector module using TensorFlow's MoveNet for skeletal tracking
"""
import os
import numpy as np
import tensorflow as tf
import tensorflow_hub as tfhub
import cv2

class PoseDetector:
    # MoveNet keypoint indices
    KEYPOINT_NOSE = 0
    KEYPOINT_LEFT_EYE = 1
    KEYPOINT_RIGHT_EYE = 2
    KEYPOINT_LEFT_EAR = 3
    KEYPOINT_RIGHT_EAR = 4
    KEYPOINT_LEFT_SHOULDER = 5
    KEYPOINT_RIGHT_SHOULDER = 6
    KEYPOINT_LEFT_ELBOW = 7
    KEYPOINT_RIGHT_ELBOW = 8
    KEYPOINT_LEFT_WRIST = 9
    KEYPOINT_RIGHT_WRIST = 10
    KEYPOINT_LEFT_HIP = 11
    KEYPOINT_RIGHT_HIP = 12
    KEYPOINT_LEFT_KNEE = 13
    KEYPOINT_RIGHT_KNEE = 14
    KEYPOINT_LEFT_ANKLE = 15
    KEYPOINT_RIGHT_ANKLE = 16
    
    def __init__(self, model_type="movenet_lightning"):
        """
        Initialize the pose detector with TensorFlow MoveNet model
        
        Args:
            model_type (str): Type of MoveNet model to use ('movenet_lightning' or 'movenet_thunder')
        """
        self.model_type = model_type
        self.model_path = self._get_model_path()
        self.model = self._load_model()
        self.input_size = 192 if model_type == "movenet_lightning" else 256
        self.keypoint_threshold = 0.3  # Confidence threshold for keypoints
        
    def _get_model_path(self):
        """Get the TF Hub model path based on the selected model type"""
        if self.model_type == "movenet_lightning":
            return "https://tfhub.dev/google/movenet/singlepose/lightning/4"
        elif self.model_type == "movenet_thunder":
            return "https://tfhub.dev/google/movenet/singlepose/thunder/4"
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    def _load_model(self):
        """Load the TensorFlow model from TF Hub"""
        print(f"Loading MoveNet model: {self.model_type}")
        module = tfhub.load(self.model_path)
        model = module.signatures['serving_default']
        print("Model loaded successfully")
        return model
    
    def _preprocess_image(self, image):
        """Preprocess the input image for the model"""
        # Resize and pad the image to the model's input dimensions
        input_img = tf.image.resize_with_pad(
            tf.expand_dims(tf.convert_to_tensor(image), axis=0),
            self.input_size, self.input_size
        )
        # Convert to float32
        input_img = tf.cast(input_img, dtype=tf.float32)
        return input_img
    
    def detect_pose(self, image):
        """
        Detect poses in the input image
        
        Args:
            image: Input RGB image
            
        Returns:
            List of detected keypoints with their coordinates and confidence scores
        """
        # Preprocess the image
        input_img = self._preprocess_image(image)
        
        # Run inference
        outputs = self.model(input_img)
        keypoints = outputs['output_0'].numpy()
        
        # The model returns keypoints in format [1, 1, 17, 3] where the last dimension
        # consists of [y, x, confidence]
        keypoints = keypoints[0, 0, :, :]
        
        # Convert normalized coordinates to pixel coordinates
        h, w, _ = image.shape
        keypoints_with_scores = []
        
        for i, keypoint in enumerate(keypoints):
            y, x, confidence = keypoint
            # Skip keypoints with low confidence
            if confidence < self.keypoint_threshold:
                keypoints_with_scores.append((i, None, None, 0.0))
                continue
                
            # Convert to pixel coordinates
            px = int(x * w)
            py = int(y * h)
            keypoints_with_scores.append((i, px, py, confidence))
        
        return keypoints_with_scores
    
    def draw_pose(self, image, keypoints):
        """
        Draw the detected pose keypoints and connections on the image
        
        Args:
            image: The input image
            keypoints: List of detected keypoints
            
        Returns:
            Image with pose visualization
        """
        output_img = image.copy()
        
        # Define connections between keypoints for visualization
        connections = [
            (self.KEYPOINT_NOSE, self.KEYPOINT_LEFT_EYE),
            (self.KEYPOINT_NOSE, self.KEYPOINT_RIGHT_EYE),
            (self.KEYPOINT_LEFT_EYE, self.KEYPOINT_LEFT_EAR),
            (self.KEYPOINT_RIGHT_EYE, self.KEYPOINT_RIGHT_EAR),
            (self.KEYPOINT_LEFT_SHOULDER, self.KEYPOINT_RIGHT_SHOULDER),
            (self.KEYPOINT_LEFT_SHOULDER, self.KEYPOINT_LEFT_ELBOW),
            (self.KEYPOINT_RIGHT_SHOULDER, self.KEYPOINT_RIGHT_ELBOW),
            (self.KEYPOINT_LEFT_ELBOW, self.KEYPOINT_LEFT_WRIST),
            (self.KEYPOINT_RIGHT_ELBOW, self.KEYPOINT_RIGHT_WRIST),
            (self.KEYPOINT_LEFT_SHOULDER, self.KEYPOINT_LEFT_HIP),
            (self.KEYPOINT_RIGHT_SHOULDER, self.KEYPOINT_RIGHT_HIP),
            (self.KEYPOINT_LEFT_HIP, self.KEYPOINT_RIGHT_HIP),
            (self.KEYPOINT_LEFT_HIP, self.KEYPOINT_LEFT_KNEE),
            (self.KEYPOINT_RIGHT_HIP, self.KEYPOINT_RIGHT_KNEE),
            (self.KEYPOINT_LEFT_KNEE, self.KEYPOINT_LEFT_ANKLE),
            (self.KEYPOINT_RIGHT_KNEE, self.KEYPOINT_RIGHT_ANKLE)
        ]
        
        # Create a keypoint lookup dictionary for faster access
        keypoint_dict = {kp[0]: (kp[1], kp[2], kp[3]) for kp in keypoints}
        
        # Draw connections
        for connection in connections:
            start_idx, end_idx = connection
            if start_idx in keypoint_dict and end_idx in keypoint_dict:
                start_point = keypoint_dict[start_idx]
                end_point = keypoint_dict[end_idx]
                
                # Skip if either keypoint was not detected
                if None in (start_point[0], start_point[1], end_point[0], end_point[1]):
                    continue
                
                # Draw the connection line
                cv2.line(output_img, 
                         (start_point[0], start_point[1]), 
                         (end_point[0], end_point[1]), 
                         (0, 255, 0), 2)
        
        # Draw keypoints
        for idx, x, y, confidence in keypoints:
            # Skip keypoints with low confidence
            if x is None or y is None:
                continue
                
            # Color based on confidence: green for high confidence, yellow for medium, red for low
            if confidence > 0.7:
                color = (0, 255, 0)  # Green
            elif confidence > 0.5:
                color = (0, 255, 255)  # Yellow
            else:
                color = (0, 0, 255)  # Red
                
            cv2.circle(output_img, (x, y), 5, color, -1)
            
        return output_img
    
    def get_hand_keypoints(self, keypoints):
        """
        Extract hand keypoints (wrists, elbows, shoulders) which are important for punch detection
        
        Args:
            keypoints: List of all detected keypoints
            
        Returns:
            Dictionary with hand keypoint coordinates
        """
        hand_keypoints = {}
        keypoint_dict = {kp[0]: (kp[1], kp[2], kp[3]) for kp in keypoints}
        
        # Extract important keypoints for punch detection
        important_keypoints = [
            ("left_wrist", self.KEYPOINT_LEFT_WRIST),
            ("right_wrist", self.KEYPOINT_RIGHT_WRIST),
            ("left_elbow", self.KEYPOINT_LEFT_ELBOW),
            ("right_elbow", self.KEYPOINT_RIGHT_ELBOW),
            ("left_shoulder", self.KEYPOINT_LEFT_SHOULDER),
            ("right_shoulder", self.KEYPOINT_RIGHT_SHOULDER)
        ]
        
        for name, idx in important_keypoints:
            if idx in keypoint_dict and keypoint_dict[idx][0] is not None:
                hand_keypoints[name] = (keypoint_dict[idx][0], keypoint_dict[idx][1], keypoint_dict[idx][2])
            else:
                hand_keypoints[name] = None
                
        return hand_keypoints