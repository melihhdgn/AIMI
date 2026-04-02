AIMI: Artificial Intelligence Medical Imaging
AIMI is an autonomous X-ray positioning and control system designed to minimize human error, reduce radiation exposure, and optimize radiology workflows using AI and sensor fusion.

📌 Problem Statement
In Turkey, 10-15% of X-rays are retaken, with 25% of these retakes caused by positioning errors. This leads to:

Increased Radiation: Patients are exposed to 30-50% more radiation per retake.

Health Risks for Technicians: Long-term exposure increases the risk of leukemia and other cancers by 1.5x.

Economic Loss: Each retake costs between 50-100 TL, leading to millions in annual waste.

Efficiency: Increased waiting times and workload on healthcare staff.

💡 The Solution
AIMI integrates Computer Vision (YOLOv8, MobileNet) and Hardware Control (Arduino/Raspberry Pi) to create a smart assistant that:

Provides 3D/Visual guidance to the patient.

Analyzes posture in real-time using YOLO-based detection.

Automatically triggers the exposure (shutter) only when the correct position is achieved.

Classifies the final image quality to ensure diagnostic accuracy.

🛠 Methodology & Technical Architecture
The system follows a multi-layered approach to ensure precision:

1. Object Detection (YOLOv8)
Utilizes a YOLOv8 CNN-based model to identify the anatomical region (currently focused on Hand/Wrist) and detect specific posture deviations in real-time.

2. Pose Analysis & Error Detection (MediaPipe)
In the current prototype, MediaPipe is used for skeletal tracking. It calculates geometric and mathematical angles of joints to determine if the patient's hand/wrist alignment matches the required medical standards.

3. Image Classification (MobileNet)
A lightweight MobileNet model classifies the captured X-ray image into three categories:

Correct: Optimal exposure and positioning.

Blurry: Movement detected during exposure.

Faulty: Anatomical positioning error.

4. Hardware Control & Feedback
Control Unit: Arduino (Prototype) managing servo motors and LED indicators.

Visual/Audio Guidance: Uses PyQt6 for the UI and Google gTTS for voice instructions to guide the patient without technician intervention.

Safety Shutter: A logic-gate system where the shutter only triggers if the AI confidence score exceeds a specific threshold.

├── 💻 1. ANA KOD (Dual PC Setup)
│   ├── UI_Main.py
│   ├── IP_Communication.py
│   └── Remote_Error_Display.py
│
├── 🛠️ 2. YARDIMCI KOD (Single PC Setup)
│   ├── Integrated_System.py
│   └── MediaPipe_Logic.py
│
└── 🧠 3. MODELLER
    ├── YOLOv8_Hand_Wrist/
    ├── MobileNet_Classifier/
    └── Datasets/
    
    📊 Performance
The models achieved high accuracy during training:

mAP@50: Between 95% - 99% for detection.

Real-world performance: Currently fluctuates around 70% due to background and lighting variations, showing the need for further data augmentation.

⚠️ Current Status & Limitations
Note: This project is currently in the prototype phase and development has been paused.

Scope: The system is currently functional only for Hand and Wrist X-rays.

Hardware: The prototype uses MediaPipe instead of LIDAR and Arduino instead of Raspberry Pi due to resource constraints.

Dataset: Trained on a controlled dataset of 8 volunteers; needs expansion for clinical reliability.

