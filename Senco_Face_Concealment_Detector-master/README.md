# Senco Face Concealment & Masking Detection System

An enterprise-grade, real-time Computer Vision surveillance pipeline for detecting face concealment, suspicious headwear, and facial occlusion (balaclavas, full-face helmets, scarves/cloth, medical masks, and sunglasses-cap combinations) across store and CCTV feeds.

---

## 🌟 Key Features

- **Multi-Category Concealment Detection**:
  - `balaclava_ski_mask` (CRITICAL — Red HUD)
  - `full_face_helmet` (HIGH — Orange-Red HUD)
  - `scarf_bandana` (HIGH — Dark Orange HUD)
  - `surgical_mask` (MEDIUM — Amber HUD)
  - `sunglasses_cap_combo` (LOW — Yellow HUD)
  - `clear_face` (NORMAL — Green HUD)
- **Zero-Latency Streaming Engine**: Multi-threaded RTSP / Video / Webcam reader with automated reconnect and stale-frame dropping.
- **ByteTrack Multi-Object Tracking**: Persistent tracking across frames to eliminate flickering false alarms using configurable persistence filters.
- **Incident Logger & Snapshots**: Automated CSV logging (`alerts/concealment_incidents.csv`) + cropped & full-scene high-res snapshots (`alerts/snapshots/`).
- **Surveillance HUD Visualizer**: Real-time glassmorphic status overlays, top alert warning banner, and live FPS counters.
- **Full YOLOv8 / YOLO11 Training Harness**: Scripts for dataset preparation, custom fine-tuning, mAP evaluation, and model export (ONNX, TensorRT, OpenVINO).

---

## 🚀 Quick Start

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Run Real-Time Stream (Webcam / RTSP / Video)
```bash
# Webcam
python main_stream.py --source 0

# RTSP Stream
python main_stream.py --source rtsp://admin:password@192.168.1.100:554/stream1

# Video File
python main_stream.py --source test_cctv.mp4
```

### 3. Run Benchmark Demo / Test
```bash
python run_demo.py
```

---

## 🧠 Training & Export Pipeline

### Train Custom Model
```bash
python src/training/train.py --data config/concealment_data.yaml --model yolov8s.pt --epochs 60 --batch 16
```

### Evaluate Model Performance
```bash
python src/training/evaluate.py --weights models/face_concealment_yolov8.pt --data config/concealment_data.yaml
```

### Export to ONNX / TensorRT
```bash
python src/training/export.py --weights models/face_concealment_yolov8.pt --format onnx --half
```

---

## ⚙️ Configuration (`config/config.yaml`)

Edit parameters such as confidence thresholds, alert cooldowns, stream sources, and persistence frames in `config/config.yaml`.
