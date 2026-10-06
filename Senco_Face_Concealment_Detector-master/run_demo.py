import os
import cv2
import numpy as np
import yaml
from src.utils.visualizer import ConcealmentVisualizer
from src.inference.alert_manager import ConcealmentAlertManager
from src.utils.logger import setup_logger

logger = setup_logger("DemoPipeline")

def generate_test_benchmark():
    """Generates synthetic test surveillance frames with mock concealment annotations to verify HUD and Alert Manager."""
    config_path = "config/config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    visualizer = ConcealmentVisualizer(config)
    alert_mgr = ConcealmentAlertManager(config)

    # Create dummy CCTV frame
    frame = np.full((720, 1280, 3), 40, dtype=np.uint8)
    
    # Add background grid to mimic CCTV store setting
    for y in range(0, 720, 80):
        cv2.line(frame, (0, y), (1280, y), (55, 55, 55), 1)
    for x in range(0, 1280, 80):
        cv2.line(frame, (x, 0), (x, 720), (55, 55, 55), 1)

    # Simulated detections
    mock_detections = [
        {
            "track_id": 101,
            "class_name": "balaclava_ski_mask",
            "display_name": "Balaclava / Ski Mask",
            "confidence": 0.94,
            "bbox": [200, 150, 420, 480],
            "threat_level": "CRITICAL",
            "color_bgr": [0, 0, 255],
            "is_confirmed": True
        },
        {
            "track_id": 102,
            "class_name": "full_face_helmet",
            "display_name": "Full-Face Helmet",
            "confidence": 0.89,
            "bbox": [550, 180, 750, 460],
            "threat_level": "HIGH",
            "color_bgr": [0, 69, 255],
            "is_confirmed": True
        },
        {
            "track_id": 103,
            "class_name": "clear_face",
            "display_name": "Clear Face",
            "confidence": 0.98,
            "bbox": [880, 160, 1080, 420],
            "threat_level": "NORMAL",
            "color_bgr": [0, 255, 0],
            "is_confirmed": False
        }
    ]

    # Trigger alerts
    for det in mock_detections:
        if det.get("is_confirmed", False):
            alert_mgr.trigger_alert(frame, det)

    # Render HUD
    annotated = visualizer.annotate_frame(frame, mock_detections, fps=31.4)
    
    output_demo_path = "alerts/demo_annotated_frame.jpg"
    os.makedirs(os.path.dirname(output_demo_path), exist_ok=True)
    cv2.imwrite(output_demo_path, annotated)
    logger.info(f"Demo benchmark frame successfully rendered to: {output_demo_path}")
    logger.info(f"Check incident CSV at: {alert_mgr.log_file}")

if __name__ == "__main__":
    generate_test_benchmark()
