import os
import csv
import time
import datetime
import cv2
import numpy as np
from typing import Dict, Any, Optional
from src.utils.logger import setup_logger

logger = setup_logger("AlertManager")

# Windows beep support for security alarm
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

class ConcealmentAlertManager:
    """Manages security incident logging, snapshot saving, audio alerts, and cooldowns."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_cfg = config.get("alert", {})
        self.snapshot_dir = self.alert_cfg.get("snapshot_dir", "alerts/snapshots")
        self.log_file = self.alert_cfg.get("log_file", "alerts/concealment_incidents.csv")
        self.cooldown_sec = self.alert_cfg.get("cooldown_seconds", 3.0)
        self.audio_alarm_enabled = self.alert_cfg.get("audio_alarm", True)
        self.save_crop = self.alert_cfg.get("save_annotated_crop", True)

        os.makedirs(self.snapshot_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.log_file) or ".", exist_ok=True)
        self._init_csv_log()

        # Track ID -> last alert timestamp
        self.last_alert_time: Dict[int, float] = {}

    def _init_csv_log(self):
        if not os.path.exists(self.log_file) or os.path.getsize(self.log_file) == 0:
            with open(self.log_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "Track_ID", "Concealment_Type", "Threat_Level", 
                    "Confidence", "BBox_Coordinates", "Snapshot_File", "Crop_File"
                ])

    def trigger_alert(self, frame: np.ndarray, detection: Dict[str, Any]) -> bool:
        """Evaluates detection and triggers snapshot/audio if cooldown has passed."""
        threat_level = detection.get("threat_level", "NORMAL")
        if threat_level not in ["MEDIUM", "HIGH", "CRITICAL"]:
            return False

        track_id = detection.get("track_id", -1)
        now = time.time()

        if track_id in self.last_alert_time:
            if now - self.last_alert_time[track_id] < self.cooldown_sec:
                return False

        self.last_alert_time[track_id] = now
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        cls_name = detection.get("class_name", "concealment")
        conf = detection.get("confidence", 0.0)
        bbox = detection.get("bbox", [0, 0, 0, 0])
        x1, y1, x2, y2 = [int(v) for v in bbox]

        # Save full scene snapshot
        snapshot_filename = f"incident_{timestamp_str}_ID{track_id}_{cls_name}_{threat_level}.jpg"
        snapshot_path = os.path.join(self.snapshot_dir, snapshot_filename)
        cv2.imwrite(snapshot_path, frame)

        # Save cropped face bbox if enabled
        crop_filename = ""
        if self.save_crop:
            h, w, _ = frame.shape
            cx1, cy1 = max(0, x1), max(0, y1)
            cx2, cy2 = min(w, x2), min(h, y2)
            if cx2 > cx1 and cy2 > cy1:
                crop = frame[cy1:cy2, cx1:cx2]
                crop_filename = f"crop_{timestamp_str}_ID{track_id}_{cls_name}.jpg"
                crop_path = os.path.join(self.snapshot_dir, crop_filename)
                cv2.imwrite(crop_path, crop)

        # Append to CSV
        with open(self.log_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.datetime.now().isoformat(),
                track_id,
                cls_name,
                threat_level,
                f"{conf:.3f}",
                f"[{x1},{y1},{x2},{y2}]",
                snapshot_filename,
                crop_filename
            ])

        logger.warning(
            f"🚨 ALERT TRIGGERED: {threat_level} Concealment ({cls_name} {int(conf*100)}%) - Track ID: {track_id}"
        )

        # Audio notification for HIGH and CRITICAL threats
        if self.audio_alarm_enabled and threat_level in ["HIGH", "CRITICAL"] and HAS_WINSOUND:
            try:
                freq = 1500 if threat_level == "CRITICAL" else 1000
                winsound.Beep(freq, 250)
            except Exception:
                pass

        return True
