**AutoniMake**

AutoniMake is a code-free AI robotics platform that allows users to train computer vision models and instantly connect those models to real-world hardware actions.

Instead of writing complex machine learning pipelines, users can capture examples, train a model, and control hardware devices in minutes.

Our goal is to make building autonomous robotics systems as accessible as building a website.

**Features**

Code-Free AI Training
Train computer vision models directly from a camera feed without writing machine learning code.

Real-Time AI Inference
Camera input is processed using a CNN classifier to recognize gestures or objects.

Hardware Integration
AI predictions are converted into commands that control real-world devices.

Modular Architecture
A Raspberry Pi hub communicates with ESP32 peripherals like displays, motors, or sensors.

Rapid Prototyping
Build and test autonomous behaviors in minutes rather than days.

System Architecture
Camera Input
      │
      ▼
OpenCV Processing
      │
      ▼
CNN Classification (PyTorch)
      │
      ▼
Command Mapping
      │
      ▼
Raspberry Pi Hub
      │
      ▼
ESP32 Peripheral Devices

Example command flow:

Gesture Detected → "thumbs_up"
        ↓
Command Generated → "ROBOT:F"
        ↓
ESP32 Executes → Robot Moves Forward


**Technologies Used**
Languages

Python

C++ (Arduino)

JavaScript

HTML / CSS

Frameworks & Libraries

OpenCV

PyTorch

FastAPI

U8g2

Hardware

Raspberry Pi

ESP32


Serial (UART)

Custom command protocol


**How It Works**

1. Capture Training Data

Users capture images directly from a camera feed using the web interface.

2. Train the Model

The platform trains a convolutional neural network (CNN) to recognize patterns in the captured images.

The CNN learns hierarchical visual features:

Image→FeatureExtraction→PatternRecognition→Classification


3. Real-Time Predictions

Incoming camera frames are processed and classified in real time.

Example output:

Prediction: thumbs_up
Confidence: 94%
4. Trigger Hardware Actions

Predictions are mapped to commands sent to ESP32 modules.

Example:

thumbs_up → ROBOT:F
stop → ROBOT:S

Example Use Cases

Gesture-controlled robots

Object-following autonomous vehicles

Smart accessibility tools

AI-driven hardware interfaces

Robotics education

Getting Started
1. Clone the Repository
git clone https://github.com/yourusername/autonimake.git
cd autonimake
2. Install Dependencies
pip install -r requirements.txt
3. Run the Backend
uvicorn server:app --host 0.0.0.0 --port 8000
4. Connect Hardware

Connect the ESP32 to the Raspberry Pi via USB

Upload the ESP32 firmware using the Arduino IDE

Start sending commands from the hub

Example Serial Command
DISPLAY:Hello World
ROBOT:F
Challenges We Faced

Integrating real-time computer vision with embedded hardware

Creating a reliable communication protocol between devices

Optimizing the model to train quickly for live demonstrations

Ensuring low-latency hardware responses

What We Learned

Through building AutoniMake we gained experience in:

real-time computer vision systems

CNN-based classification

embedded systems communication

modular robotics architecture

designing user-friendly AI interfaces

Future Improvements

Drag-and-drop behavior builder

Support for additional sensors and robotics modules

Cloud-based training options

Expanded AI models for object detection and tracking

Plug-and-play hardware ecosystem
