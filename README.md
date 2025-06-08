# 🥊 PunchTracker - AI Boxing Assistant 🥊

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![TensorFlow](https://img.shields.io/badge/TensorFlow-v2.12+-orange.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-v4.5+-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

A real-time boxing assistant application that uses computer vision and machine learning to track, count, and analyze your punches.


## ✨ Features

- 📹 Real-time webcam punch detection
- 🔍 Advanced pose estimation using TensorFlow's MoveNet
- 👊 Detects and classifies different punch types (jabs, crosses, hooks, uppercuts)
- 📊 Live statistics and performance tracking
- 🎯 Visual feedback for punch detection
- 🔧 User calibration for personalized detection
- 💾 Session history and progress tracking
- 📈 Performance analytics and visualization

## 🚀 Tech Stack

- **Machine Learning**: [TensorFlow](https://www.tensorflow.org/) + [TensorFlow Hub](https://tfhub.dev/)
- **Computer Vision**: [OpenCV](https://opencv.org/)
- **Data Processing**: [NumPy](https://numpy.org/)
- **Visualization**: [Matplotlib](https://matplotlib.org/)
- **Data Storage**: SQLite

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- Webcam
- Required libraries (see requirements.txt)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/punchtracker.git
   cd punchtracker
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 📋 Usage

1. Start the application:
   ```bash
   python main.py
   ```

2. Controls:
   - `ESC`: Exit the application
   - `C`: Start calibration
   - `D`: Toggle debug view (shows skeleton)
   - `R`: Reset current session
   - `S`: Show detailed statistics

3. Calibration:
   - Follow the on-screen instructions to calibrate the application to your movements
   - Move through each step of different punch types
   - The system will adjust its detection parameters to your specific style

## 📊 Data Storage

All session data is stored in a local SQLite database in the `data` folder. This includes:
- Session date and duration
- Total punch count and types
- Punches per minute
- Historical performance data

## 🏗️ Project Structure

```
punchtracker/
├── main.py              # Main application entry point
├── requirements.txt     # Required dependencies
├── data/                # Session data storage
├── models/              # Model storage (downloaded automatically)
└── utils/
    ├── pose_detector.py # TensorFlow pose detection module
    ├── punch_counter.py # Punch detection and classification
    ├── ui_manager.py    # UI and visualization components
    ├── data_manager.py  # Data storage and retrieval
    └── calibration.py   # User calibration system
```

## 🔧 Advanced Configuration

The application can be customized by modifying the following parameters:

- **Pose Detection**: Change model type in `pose_detector.py` (lightning or thunder)
- **Detection Sensitivity**: Adjust thresholds in `punch_counter.py`
- **UI Customization**: Modify colors and layout in `ui_manager.py`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## 🙏 Acknowledgements

- [TensorFlow](https://www.tensorflow.org/) for the MoveNet model
- [OpenCV](https://opencv.org/) for computer vision capabilities
- [NumPy](https://numpy.org/) and [Matplotlib](https://matplotlib.org/) for data processing and visualization

## 🌟 Future Features / Contributing Ideas

Looking for ways to contribute or curious about what's next? Check out our [list of feature ideas](./FEATURE_IDEAS.md)!

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/yourusername">Anthony M</a>
</p>
