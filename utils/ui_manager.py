"""
UI Manager module for handling the application's user interface
"""
import cv2
import numpy as np
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

class UIManager:
    def __init__(self):
        # UI settings
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.font_color = (255, 255, 255)  # White
        self.line_thickness = 2
        self.bg_color = (0, 0, 0, 0.5)  # Semi-transparent black
        
        # Stats panel dimensions
        self.panel_width = 200
        self.panel_height = 200
        self.panel_padding = 10
        
        # Punch type colors for visualization
        self.punch_colors = {
            "jab": (46, 204, 113),  # Green
            "cross": (231, 76, 60),  # Red
            "hook": (52, 152, 219),  # Blue
            "uppercut": (155, 89, 182)  # Purple
        }
    
    def update_display(self, frame, total_count, punch_counts, session_start_time, sensitivity, paused=False):
        """
        Update the UI elements on the frame
        
        Args:
            frame: The input video frame
            total_count: Total number of punches detected
            punch_counts: Dictionary with counts for each punch type
            session_start_time: Start time of the current session
            
        Returns:
            Frame with UI elements added
        """
        # Create a copy of the frame to avoid modifying the original
        display_frame = frame.copy()
        
        # Add semi-transparent overlay for stats panel
        self._add_stats_panel(display_frame, total_count, punch_counts, session_start_time, sensitivity)

        if paused:
            self._add_paused_overlay(display_frame)
        
        # Add instructions
        self._add_instructions(display_frame)
        
        return display_frame
    
    def _add_stats_panel(self, frame, total_count, punch_counts, session_start_time, sensitivity):
        """Add the statistics panel to the frame"""
        h, w = frame.shape[:2]
        
        # Create semi-transparent overlay for stats panel
        overlay = frame.copy()
        panel_x = w - self.panel_width - self.panel_padding
        panel_y = self.panel_padding
        cv2.rectangle(overlay, 
                     (panel_x, panel_y), 
                     (panel_x + self.panel_width, panel_y + self.panel_height),
                     (0, 0, 0), 
                     -1)
        
        # Apply the overlay with transparency
        alpha = 0.7
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # Add title
        title_y = panel_y + 30
        cv2.putText(frame, "PUNCH STATS", 
                   (panel_x + 10, title_y),
                   self.font, 1, self.font_color, 2)
        
        # Add total count
        count_y = title_y + 30
        cv2.putText(frame, f"Total: {total_count}", 
                   (panel_x + 10, count_y),
                   self.font, self.font_scale, self.font_color, self.line_thickness)
        
        # Add individual punch counts
        y_offset = count_y + 5
        for punch_type, count in punch_counts.items():
            y_offset += 25
            color = self.punch_colors.get(punch_type, self.font_color)
            cv2.putText(frame, f"{punch_type.capitalize()}: {count}", 
                       (panel_x + 10, y_offset),
                       self.font, self.font_scale, color, self.line_thickness)
        
        # Add session time
        if session_start_time:
            session_duration = datetime.now() - session_start_time
            minutes, seconds = divmod(session_duration.seconds, 60)
            time_str = f"Time: {minutes:02d}:{seconds:02d}"
            cv2.putText(frame, time_str,
                       (panel_x + 10, y_offset + 30),
                       self.font, self.font_scale, self.font_color, self.line_thickness)

            # Calculate and display punches per minute
            minutes_float = session_duration.total_seconds() / 60
            if minutes_float > 0:
                ppm = total_count / minutes_float
                cv2.putText(frame, f"Pace: {ppm:.1f} p/min",
                           (panel_x + 10, y_offset + 55),
                           self.font, self.font_scale, self.font_color, self.line_thickness)

        # Show current sensitivity
        cv2.putText(frame, f"Sens.: {sensitivity}",
                   (panel_x + 10, panel_y + self.panel_height - 10),
                   self.font, self.font_scale, self.font_color, self.line_thickness)
    
    def _add_instructions(self, frame):
        """Add instruction text to the frame"""
        h, w = frame.shape[:2]
        
        instructions = [
            "ESC - Exit",
            "C - Calibrate",
            "D - Debug View",
            "R - Reset Session",
            "S - Show Stats",
            "P - Pause",
            "I - Sens. +",
            "K - Sens. -"
        ]
        
        # Create semi-transparent overlay for instructions
        overlay = frame.copy()
        inst_x = self.panel_padding
        inst_y = h - (len(instructions) * 25 + 10)
        inst_width = 150
        inst_height = len(instructions) * 25 + 10
        
        cv2.rectangle(overlay, 
                     (inst_x, inst_y), 
                     (inst_x + inst_width, inst_y + inst_height),
                     (0, 0, 0), 
                     -1)
        
        # Apply the overlay with transparency
        alpha = 0.7
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # Add instruction text
        for i, instruction in enumerate(instructions):
            y_pos = inst_y + 25 + (i * 25)
            cv2.putText(frame, instruction,
                       (inst_x + 10, y_pos),
                       self.font, self.font_scale, self.font_color, 1)

    def _add_paused_overlay(self, frame):
        """Display a paused overlay on the frame"""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, int(h/2 - 40)), (w, int(h/2 + 40)), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        cv2.putText(frame, 'PAUSED', (int(w/2) - 60, int(h/2) + 10),
                   self.font, 1.2, (0, 0, 255), 3)
    
    def generate_stats_graph(self, historical_data, current_session_data):
        """
        Generate a graph showing historical punch statistics
        
        Args:
            historical_data: List of session data from previous sessions
            current_session_data: Dictionary with current session punch counts
            
        Returns:
            Numpy array containing the graph image
        """
        # Create a new figure with matplotlib
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        fig.subplots_adjust(hspace=0.3)
        
        # Extract data for plotting
        if historical_data:
            dates = [session['date'] for session in historical_data[-5:]]  # Last 5 sessions
            total_punches = [session['total_punches'] for session in historical_data[-5:]]
            ppm_values = [session['punches_per_minute'] for session in historical_data[-5:]]
            
            # Add current session if available
            if current_session_data:
                dates.append('Current')
                current_total = sum(current_session_data.values())
                total_punches.append(current_total)
                # Estimate current PPM based on session duration
                # (this would be replaced with actual calculation in a real app)
                ppm_values.append(current_total / 1.0)  # Assuming 1 minute
            
            # Plot total punches per session
            ax1.bar(dates, total_punches, color='steelblue')
            ax1.set_title('Total Punches per Session')
            ax1.set_ylabel('Punch Count')
            ax1.tick_params(axis='x', rotation=45)
            
            # Plot punches per minute
            ax2.bar(dates, ppm_values, color='firebrick')
            ax2.set_title('Punches per Minute')
            ax2.set_ylabel('Punches/Min')
            ax2.tick_params(axis='x', rotation=45)
        else:
            # Show current session data only
            if current_session_data:
                punch_types = list(current_session_data.keys())
                counts = list(current_session_data.values())
                
                # Plot punch type distribution
                colors = [self.punch_colors.get(pt, (0, 0, 0)) for pt in punch_types]
                # Convert BGR to RGB for matplotlib
                rgb_colors = [(r/255, g/255, b/255) for b, g, r in colors]
                
                ax1.bar(punch_types, counts, color=rgb_colors)
                ax1.set_title('Current Session Punch Distribution')
                ax1.set_ylabel('Count')
                
                # Add a placeholder message in the second plot
                ax2.text(0.5, 0.5, 'No historical data available yet', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=ax2.transAxes)
                ax2.set_title('Historical Data')
                ax2.axis('off')
            else:
                # No data available
                ax1.text(0.5, 0.5, 'No data available', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=ax1.transAxes)
                ax1.set_title('Current Session')
                ax1.axis('off')
                
                ax2.text(0.5, 0.5, 'No historical data available', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=ax2.transAxes)
                ax2.set_title('Historical Data')
                ax2.axis('off')
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert matplotlib figure to OpenCV image
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        graph_image = np.array(canvas.renderer.buffer_rgba())
        # Convert RGBA to BGR for OpenCV
        graph_image = cv2.cvtColor(graph_image, cv2.COLOR_RGBA2BGR)
        
        plt.close(fig)
        
        return graph_image