# 🧠 INNOWAH (NeuroBand Plus) — Multimodal Alzheimer's Risk Prediction System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-black.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Random%20Forest-F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8.svg?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore-FFCA28.svg?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com/)
[![ESP32](https://img.shields.io/badge/Hardware-ESP32%20IoT-E7352C.svg?style=for-the-badge&logo=espressif&logoColor=white)](https://www.espressif.com/)

---

## 📌 Executive Summary

**INNOWAH (NeuroBand Plus)** is a non-invasive, early-stage screening platform designed for early detection and risk stratification of Alzheimer’s disease and mild cognitive impairment (MCI). By fusing **software-derived cognitive metrics** with **real-time hardware physiological telemetry** from ESP32 wearable devices, INNOWAH provides an affordable, accessible, home-based alternative to traditional, costly diagnostic methods (e.g., PET scans, lumbar punctures, or clinical MRIs).

The platform ingests **29 multimodal parameters** (14 software features + 15 hardware features) and processes them using a trained **RandomForest Classifier** backed by an **Explainable AI (XAI)** clinical domain framework, categorizing patient risk into **Normal**, **Mild Risk**, or **High Risk**.

---

## 🌟 Key Features

### 🧩 1. Software Cognitive Assessment Suite
- **Card Memory Recall Test (`memory.html`):** Evaluates visual working memory, immediate recall, delayed recall, and error rate across adaptive difficulty grids.
- **N-Back Attention Task (`n-back.html`):** Measures dynamic working memory, decision-making reaction time, and error consistency under cognitive load.
- **Clinical Questionnaire (`questionnaire.html`):** Evaluates spatial orientation, language capabilities, attention span, and daily functioning activities.
- **Computer Vision Paper-Folding Task (`OpenCV`):** Analyzes motor planning and visuospatial orientation by performing edge detection (`Canny`), Hough line transformation, and horizontal/vertical structural symmetry evaluation (`cv2.absdiff`) on patient-uploaded folded paper images.

### ⌚ 2. IoT Wearable Sensor Telemetry
- **ESP32 Wristband Device (`wristband.ino`):**
  - **IMU Sensor (MPU-6050):** Tracks motor degradation markers including gait speed, stride variability, turning velocity, postural sway, and daily step counts.
  - **PPG Pulse Oximeter (MAX30100):** Captures heart rate (HR), oxygen saturation ($SpO_2$), and heart rate variability (HRV) metrics ($RMSSD$, $SDNN$, $LF/HF\ ratio$).
  - **Body Temperature Sensor:** Monitors peripheral thermal drift.
  - **OLED Display (SSD1306):** Provides live local vitals telemetry feedback.
- **ESP32 Headband Device (`headband.ino`):**
  - **EEG Sensor Module:** Real-time extraction of brainwave frequency powers ($\alpha$, $\theta$, $\delta$, $\beta$, $\gamma$), calculating the **Theta/Alpha Ratio ($TAR$)**—a fundamental biomarker in cognitive decline—and dominant frequency.

### 🤖 3. Machine Learning & Explainable AI (XAI)
- **RandomForest Classifier:** Multiclass model trained on standardized feature vectors with high resilience to missing values and noise.
- **Clinical Fallback Inference Engine:** Rule-based fallback mechanism ensuring robust system operation even during partial sensor loss or offline model states.
- **5 Cognitive Domain Breakdown:** Deconstructs overall risk into five granular domains:
  1. 🧠 **Memory**
  2. 💡 **Reasoning & Executive Function**
  3. 📐 **Visuospatial Processing**
  4. 🗣️ **Language & Orientation**
  5. 🏃 **Motor & Behavioral Control**

### 📊 4. Real-Time Cloud & Clinical Reporting
- **Firebase Authentication & Firestore:** Real-time multi-device database sync linking physical ESP32 Device IDs to user accounts.
- **Automated Excel Diagnostic Report:** Generates exportable `.xlsx` reports detailing 5-minute hardware vitals time series, software scores, and personalized clinical recommendations via `openpyxl`.

---

## 🏗 System Architecture & Data Flow

```mermaid
graph TD
    subgraph Client System & Wearables
        A1[ESP32 Wristband: MPU6050 + MAX30100] -->|HTTP POST JSON| API1[/api/hardware_data\]
        A2[ESP32 Headband: EEG Sensor Module] -->|HTTP POST JSON| API1
        B1[Web Portal: Cognitive Games] -->|Scores & Metrics| API2[/save_cognitive_scores\]
        B2[Web Portal: OpenCV Fold Test] -->|Base64 Image| API3[/process_fold_test\]
    end

    subgraph Backend Engine & Cloud
        API1 & API2 & API3 --> FEX[feature_extractor.py: 29-Feature Normalizer]
        FEX --> DB[(Firebase Firestore)]
        FEX --> ML[inference_engine.py: RandomForest Model]
        ML -->|Fallback Check| RULE[Rule-Based Clinical Risk Evaluator]
    end

    subgraph Diagnostic Output
        ML & RULE --> DIAG[5-Domain Diagnostic Breakdown]
        DIAG --> UI[Interactive Dashboard Gauges & Alerts]
        DIAG --> EXCEL[Excel Clinical Report Exporter]
    end
```

---

## 📁 Repository Structure

```
Mini-project-og/
├── app.py                     # Main Flask Application & REST API Routing
├── feature_extractor.py       # Data Pipeline & 29-Feature Vector Normalizer
├── inference_engine.py        # ML Inference & Fallback Clinical Rules Engine
├── render_api.py              # Cloud API Entry point for Render deployment
├── wristband.ino              # ESP32 Firmware for Wristband (IMU + PPG + Temp + OLED)
├── headband.ino               # ESP32 Firmware for Headband (EEG Brainwave Processing)
├── presentation_guide.md      # Project Presentation & Defense Q&A Documentation
├── requirements.txt           # Python Package Dependencies
├── render.yaml                # Render Cloud Deployment Configuration
├── Procfile                   # Gunicorn / Waitress Production Command
│
├── model/                     # Machine Learning Model Artifacts
│   ├── innowah_model.pkl      # Trained RandomForest Classifier
│   ├── innowah_scaler.pkl     # StandardScaler Model Weights
│   └── model_meta.json        # Model Feature Names & Metadata
│
├── templates/                 # Frontend HTML Web Interfaces
│   ├── index.html             # Main Patient & Diagnostic Dashboard
│   ├── memory.html            # Interactive Memory Recall Game
│   ├── n-back.html            # Working Memory N-Back Task
│   ├── questionnaire.html     # Clinical Questionnaire & Fold Test UI
│   └── signup.html            # User Registration & ESP32 Linking
│
└── static/                    # Frontend Styles & Client Scripts
    ├── index_style.css        # Dashboard Styles & Dynamic Gauge Animations
    ├── memory_style.css       # Memory Game Styles
    ├── nback_style.css        # N-Back Game Styles
    ├── questionnaire_style.css# Questionnaire & Camera Styles
    ├── signup_style.css       # Signup Page Styling
    └── firebase_setup.js      # Firebase Initialization & Auth Configuration
```

---

## 📊 Feature Matrix (29 Parameters)

| Domain | Feature Name | Source | Description |
| :--- | :--- | :--- | :--- |
| **Software** | `immediate_recall` | Memory Game | Short-term pattern memory recall score |
| **Software** | `delayed_recall` | Memory Game | Retention recall score after interference task |
| **Software** | `memory_accuracy` | Memory Game | Ratio of correct card matches vs total flips |
| **Software** | `memory_error_rate` | Memory Game | Frequency of incorrect card selection pairs |
| **Software** | `nback_accuracy` | N-Back Game | Accuracy percentage on working memory targets |
| **Software** | `reaction_time_ms` | N-Back Game | Mean reaction time (milliseconds) |
| **Software** | `error_consistency` | N-Back Game | Variance in decision-making errors |
| **Software** | `orientation_score` | Questionnaire | Awareness of time, date, location |
| **Software** | `language_score` | Questionnaire | Naming, comprehension, and expression score |
| **Software** | `attention_score` | Questionnaire | Serial subtraction & focus retention |
| **Software** | `daily_activity_score` | Questionnaire | Functional daily living activity index |
| **Software** | `paper_fold_success` | OpenCV Fold Test | Binary score derived from edge symmetry |
| **Software** | `fold_symmetry_score` | OpenCV Fold Test | Differential pixel symmetry analysis (`absdiff`) |
| **Software** | `fold_line_count` | OpenCV Fold Test | Hough Transform line detection count |
| **Hardware** | `gait_speed` | ESP32 IMU | Calculated walking velocity from accelerometer |
| **Hardware** | `stride_variability` | ESP32 IMU | Variance in acceleration step patterns |
| **Hardware** | `turning_velocity` | ESP32 IMU | Gyroscope angular velocity during turns |
| **Hardware** | `postural_sway` | ESP32 IMU | Standing postural stability deviation |
| **Hardware** | `step_count` | ESP32 IMU | Total step count accumulated during test |
| **Hardware** | `heart_rate` | ESP32 PPG | Filtered pulse rate (BPM) |
| **Hardware** | `spo2` | ESP32 PPG | Oxygen saturation level percentage |
| **Hardware** | `rmssd` | ESP32 PPG | Root mean square of successive RR differences |
| **Hardware** | `sdnn` | ESP32 PPG | Standard deviation of NN intervals |
| **Hardware** | `lf_hf_ratio` | ESP32 PPG | Low Frequency to High Frequency autonomic balance |
| **Hardware** | `skin_temp` | ESP32 Temp | Body temperature reading (°C) |
| **Hardware** | `alpha_power` | ESP32 EEG | Alpha brainwave power spectrum (8-12 Hz) |
| **Hardware** | `theta_power` | ESP32 EEG | Theta brainwave power spectrum (4-8 Hz) |
| **Hardware** | `delta_power` | ESP32 EEG | Delta brainwave power spectrum (0.5-4 Hz) |
| **Hardware** | `theta_alpha_ratio` | ESP32 EEG | Key biomarker ratio ($TAR = \frac{\text{Theta}}{\text{Alpha}}$) |

---

## ⚡ Quick Start Guide

### Prerequisites
- **Python 3.10+**
- **Git**
- **Arduino IDE** (for uploading firmware to ESP32 microcontrollers)
- **Firebase Account** (for live real-time synchronization)

### 1. Installation & Environment Setup

```bash
# Clone the repository
git clone https://github.com/R-MANI-KANDAN/innowah.git
cd innowah

# Create and activate virtual environment
# On Windows:
python -m venv venv
.\venv\Scripts\activate

# On Linux/macOS:
# python3 -m venv venv
# source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 2. Firebase Configuration
Place your Firebase Admin SDK service account key file in the root directory named `serviceAccountKey.json`:

```json
{
  "type": "service_account",
  "project_id": "your-firebase-project-id",
  "private_key_id": "your-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk@your-project.iam.gserviceaccount.com"
}
```

### 3. Run the Flask Web Application

```bash
python app.py
```

Open your browser and navigate to `http://localhost:5000` to access the application dashboard.

---

## 📡 Hardware & Firmware Setup

1. Open `wristband.ino` and `headband.ino` in **Arduino IDE**.
2. Install the necessary Arduino libraries:
   - `Adafruit SSD1306` & `Adafruit GFX`
   - `MAX30100lib`
   - `WiFi` & `HTTPClient`
3. Configure Wi-Fi credentials and target backend endpoint:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   const char* serverURL = "http://<YOUR_SERVER_IP>:5000/api/hardware_data";
   ```
4. Connect your ESP32 boards via USB and select the appropriate COM port.
5. Flash `wristband.ino` to the Wristband ESP32 and `headband.ino` to the Headband ESP32.

---

## 🔌 API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/hardware_data` | Endpoint for ESP32 microcontrollers to push JSON vitals telemetry |
| `GET` | `/get_data` | AJAX polling endpoint for dashboard live telemetry updates |
| `POST` | `/save_cognitive_scores` | Receives software game scores and updates user state |
| `POST` | `/process_fold_test` | Processes base64 folded paper image via OpenCV |
| `POST` | `/predict_risk` | Triggers the RandomForest ML & Clinical Fallback prediction engine |
| `GET` | `/download_report` | Generates and downloads the comprehensive Excel clinical report |

---

## 🚀 Cloud Deployment

The repository includes pre-configured deployment settings for hosting on **Render** or **Heroku**:

- `requirements_render.txt`: Optimized lightweight dependency requirements.
- `render.yaml`: Infrastructure as Code configuration specifying environment runtime and startup options.
- `Procfile`: Gunicorn WSGI web server deployment command:
  ```gunicorn
  web: gunicorn app:app
  ```

---

