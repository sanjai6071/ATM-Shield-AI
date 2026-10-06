import os
import sys
import time
import argparse
import yaml
import cv2

from src.utils.logger import setup_logger
from src.utils.visualizer import ConcealmentVisualizer
from src.inference.stream_reader import ResilientStreamReader
from src.inference.concealment_engine import ConcealmentEngine
from src.inference.alert_manager import ConcealmentAlertManager

logger = setup_logger("MainStream")

def load_config(config_path: str = "config/config.yaml") -> dict:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_pipeline(source_override: str = None, headless: bool = False, config_path: str = "config/config.yaml"):
    # 1. Load system config
    config = load_config(config_path)
    stream_cfg = config.get("stream", {})
    ui_cfg = config.get("ui", {})
    
    source = source_override if source_override is not None else stream_cfg.get("source", 0)
    
    # 2. Initialize Engine, Visualizer, Alert Manager
    engine = ConcealmentEngine(config)
    visualizer = ConcealmentVisualizer(config)
    alert_mgr = ConcealmentAlertManager(config)

    # 3. Start Stream Reader
    resolution = stream_cfg.get("input_resolution", None)
    stream_reader = ResilientStreamReader(
        source=source,
        reconnect_interval=stream_cfg.get("reconnect_interval_sec", 5),
        buffer_size=stream_cfg.get("frame_buffer_size", 1),
        resolution=resolution
    ).start()

    window_name = ui_cfg.get("window_name", "Senco Face Concealment & Masking Monitor")
    
    logger.info("==================================================================")
    logger.info("  SENCO FACE CONCEALMENT & MASKING SURVEILLANCE ENGINE INITIALIZED")
    logger.info(f"  Source: {source} | Headless: {headless}")
    logger.info("  Press 'q' in UI to exit, 's' to manually save snapshot")
    logger.info("==================================================================")

    prev_time = time.time()
    fps = 0.0

    try:
        while True:
            ret, frame = stream_reader.read(timeout=1.0)
            if not ret or frame is None:
                # If reading video file finished
                if not stream_reader.running:
                    break
                continue

            curr_time = time.time()
            fps = 1.0 / max(1e-5, (curr_time - prev_time))
            prev_time = curr_time

            # 4. Inference & Tracking
            detections = engine.process_frame(frame, use_tracker=True)

            # 5. Check alerts for confirmed threats
            for det in detections:
                if det.get("is_confirmed", False):
                    alert_mgr.trigger_alert(frame, det)

            # 6. Render HUD Overlay
            annotated_frame = visualizer.annotate_frame(frame, detections, fps=fps)

            # 7. Display Window
            if not headless:
                cv2.imshow(window_name, annotated_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    logger.info("User requested exit ('q'). Stopping...")
                    break
                elif key == ord('s'):
                    # Force snapshot
                    manual_det = {
                        "class_name": "manual_snapshot",
                        "threat_level": "CRITICAL",
                        "confidence": 1.0,
                        "track_id": 999,
                        "bbox": [0, 0, frame.shape[1], frame.shape[0]]
                    }
                    alert_mgr.trigger_alert(frame, manual_det)
                    logger.info("Manual snapshot captured!")

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down...")
    finally:
        stream_reader.stop()
        if not headless:
            cv2.destroyAllWindows()
        logger.info("Pipeline terminated gracefully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Senco Face Concealment & Masking Monitor")
    parser.add_argument("--source", type=str, default=None, help="RTSP URL, video file path, or webcam index (0)")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="Path to config.yaml")
    parser.add_argument("--headless", action="store_true", help="Run without graphical display window")
    args = parser.parse_args()

    run_pipeline(
        source_override=args.source,
        headless=args.headless,
        config_path=args.config
    )
