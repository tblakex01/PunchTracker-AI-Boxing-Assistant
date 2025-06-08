# Feature Ideas for PunchTracker

This document outlines potential new features for the PunchTracker application. These ideas aim to enhance the user experience, provide more detailed feedback, and add new training functionalities.

## 1. Combo Detection

*   **Description:** Implement a feature to detect predefined punch combinations (e.g., jab-cross-hook, jab-jab-cross, hook-cross-hook). The system would analyze the sequence and timing of detected punches to identify known combos. Users could potentially define their own custom combinations.
*   **Rationale:**
    *   Adds a layer of gamification and makes training more engaging.
    *   Allows users to practice and get feedback on specific boxing combinations.
    *   Could be used to structure workouts around combo execution.
*   **Potential Implementation:**
    *   Modify `utils/punch_counter.py`:
        *   Store a short history (e.g., last 5-7 punches) of detected punch types and their timestamps.
        *   This history should be cleared or reset after a combo is detected or a certain time without a punch elapses.
    *   Create a new module `utils/combo_detector.py`:
        *   Define a list or dictionary of known punch combinations. Each combination would be a sequence of punch types and potentially expected time intervals between punches.
        *   Implement logic to compare the recent punch history from `PunchCounter` against the predefined combo patterns.
        *   Could include a scoring system for combo accuracy (timing, correct punches).
    *   Update `main.py`:
        *   Integrate the `ComboDetector` to process punches from `PunchCounter`.
    *   Update `utils/ui_manager.py`:
        *   Display detected combos on the screen (e.g., "Jab-Cross-Hook!").
        *   Show statistics for combo attempts, successes, and types.
    *   Update `utils/data_manager.py`:
        *   Store statistics related to combo performance in the session data.

## 2. Target Mode / Gamification

*   **Description:** Introduce an interactive training mode where the application displays visual targets on the screen. Targets could appear at random locations or in a predefined sequence, requiring the user to "hit" them with the correct type of punch (or any punch).
*   **Rationale:**
    *   Makes training more interactive, fun, and game-like.
    *   Helps improve punching accuracy, reaction time, and coordination.
    *   Can be adapted for various skill levels by changing target speed, size, and sequence complexity.
*   **Potential Implementation:**
    *   Create a new module `utils/target_manager.py`:
        *   Responsible for generating targets (e.g., position, size, type if punch-specific).
        *   Manages target lifecycle (appearance, disappearance, hit detection).
        *   Could define different game modes (e.g., reaction test, sequence practice).
    *   Integrate `TargetManager` with `main.py`:
        *   Add a new application state or mode for "Target Mode".
        *   Pass necessary data (like hand positions from `PoseDetector`) to `TargetManager`.
    *   Modify `utils/ui_manager.py`:
        *   Draw targets on the video frame (e.g., as circles or specific shapes).
        *   Display game-related information like score, time remaining, upcoming targets, or feedback on hits/misses.
    *   Modify `utils/punch_counter.py` (or `PoseDetector`):
        *   Provide accurate and timely hand/wrist coordinates to `TargetManager` for hit detection.
        *   Hit detection logic would compare the position of the user's fist (wrist keypoint) at the moment of a punch with the target's position.
    *   Update `utils/data_manager.py`:
        *   Store scores, accuracy, reaction times, and other relevant metrics from target mode sessions.

## 3. Advanced Performance Metrics & Feedback

*   **Description:** Expand on the existing statistics by calculating and displaying more detailed performance metrics. This could include:
    *   **Punch Speed Estimation:** Estimate the speed of punches (e.g., in pixels/second or a calibrated m/s if depth can be factored in) based on wrist keypoint displacement over time.
    *   **Punch Power Estimation (Conceptual):** While true power is difficult to measure accurately with only a 2D camera, a proxy could be estimated. This might involve looking at the acceleration of the hand/wrist or the extent of motion blur if detectable. This would be an experimental and more challenging feature.
    *   **Reaction Time (especially if Target Mode is implemented):** Measure the time taken to hit a target after it appears.
    *   **Punch Accuracy (especially if Target Mode is implemented):** Measure how close to the center of a target a punch lands.
    *   **Fatigue Monitoring (Conceptual):** Attempt to infer user fatigue by analyzing trends in punch speed, frequency, form (e.g., changes in arm extension, guard position), or consistency over the duration of a session. This would require establishing baseline metrics.
*   **Rationale:**
    *   Provides users with more in-depth, quantitative insights into their performance.
    *   Helps identify areas for improvement (e.g., speed, power, consistency).
    *   Can make training more data-driven.
*   **Potential Implementation:**
    *   Modify `utils/punch_counter.py`:
        *   For **Speed Estimation:** Enhance `_calculate_velocity` to provide more consistent speed readings. Consider averaging speed over the punch's active frames.
        *   For **Power Proxy:** This is complex. Could start by looking at peak velocity or acceleration of the wrist.
        *   For **Fatigue Monitoring:** Track metrics like average punch speed, punch rate, and possibly key body posture angles over time. Detect significant declines or deviations from initial values.
    *   Update `utils/data_manager.py`:
        *   Add new fields to the session data schema to store these advanced metrics (e.g., average/max punch speed, reaction times, accuracy scores).
    *   Update `utils/ui_manager.py`:
        *   Display these new metrics on the stats panel or create a new "Advanced Stats" view.
        *   Potentially provide real-time feedback (e.g., a visual gauge for punch speed, or an alert if fatigue is detected).
        *   Enhance `generate_stats_graph` to include visualizations for these new metrics over one or multiple sessions.
    *   Modify `utils/calibration.py`:
        *   Calibration might be needed for more accurate speed/power estimations, potentially by having the user punch a known distance.

These feature ideas can be developed incrementally and would significantly enhance the capabilities of the PunchTracker application.
