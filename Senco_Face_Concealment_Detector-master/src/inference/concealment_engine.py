import os
import torch
import numpy as np
from typing import List, Dict, Any, Optional
from ultralytics import YOLO
from src.utils.logger import setup_logger

logger = setup_logger("ConcealmentEngine")

class ConcealmentEngine:
    """Core Inference and Tracking Engine for Face Concealment & Masking Detection."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_cfg = config.get("model", {})
        self.classes_cfg = config.get("classes", {})
        self.alert_cfg = config.get("alert", {})

        self.device = self._resolve_device(self.model_cfg.get("device", "auto"))
        self.conf_threshold = self.model_cfg.get("conf_threshold", 0.35)
        self.iou_threshold = self.model_cfg.get("iou_threshold", 0.45)
        self.imgsz = self.model_cfg.get("imgsz", 640)
        self.half = self.model_cfg.get("half_precision", False) and self.device.type == "cuda"
        self.persistence_frames = self.alert_cfg.get("persistence_frames", 3)

        # Track history: track_id -> consecutive frames detected with concealment
        self.track_persistence: Dict[int, int] = {}
        self.track_active: Dict[int, str] = {}

        self.model = self._load_model()
        from src.inference.landmark_occlusion import FacialLandmarkOcclusionDetector
        self.occlusion_detector = FacialLandmarkOcclusionDetector()

    def _resolve_device(self, device_str: str) -> torch.device:
        if device_str == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device(device_str)

    def _load_model(self) -> YOLO:
        weights_path = self.model_cfg.get("weights_path", "models/face_concealment_yolov8.pt")
        fallback_model = self.model_cfg.get("fallback_model", "yolov8n.pt")

        if os.path.exists(weights_path):
            logger.info(f"Loading custom face concealment weights: {weights_path}")
            model = YOLO(weights_path)
        else:
            logger.warning(f"Custom weights '{weights_path}' not found. Initializing with pretrained YOLO model: {fallback_model}")
            model = YOLO(fallback_model)

        return model

    def _match_class_config(self, raw_class_name: str) -> Dict[str, Any]:
        """Maps detected raw class names to standardized concealment config."""
        name_lower = raw_class_name.lower().replace("-", "_").replace(" ", "_")

        # Direct match or substring matching
        for key, info in self.classes_cfg.items():
            if key in name_lower or name_lower in key:
                return {
                    "key": key,
                    "display_name": info.get("display_name", key),
                    "threat_level": info.get("threat_level", "NORMAL"),
                    "color_bgr": info.get("color_bgr", [0, 255, 0]),
                    "conf_threshold": info.get("conf_threshold", self.conf_threshold)
                }

        # Fallback heuristic for generic YOLO person/face models
        if any(w in name_lower for w in ["balaclava", "ski_mask", "ski"]):
            return {"key": "balaclava_ski_mask", "display_name": "Balaclava / Ski Mask", "threat_level": "CRITICAL", "color_bgr": [0, 0, 255], "conf_threshold": 0.4}
        elif any(w in name_lower for w in ["helmet", "full_face"]):
            return {"key": "full_face_helmet", "display_name": "Full-Face Helmet", "threat_level": "HIGH", "color_bgr": [0, 69, 255], "conf_threshold": 0.45}
        elif any(w in name_lower for w in ["scarf", "bandana", "cloth", "gamcha"]):
            return {"key": "scarf_bandana", "display_name": "Scarf / Cloth Masking", "threat_level": "HIGH", "color_bgr": [0, 140, 255], "conf_threshold": 0.45}
        elif any(w in name_lower for w in ["mask", "surgical", "n95", "facemask"]):
            return {"key": "surgical_mask", "display_name": "Surgical / Cloth Mask", "threat_level": "MEDIUM", "color_bgr": [0, 215, 255], "conf_threshold": 0.45}
        elif any(w in name_lower for w in ["glasses", "sunglasses", "cap", "hoodie"]):
            return {"key": "sunglasses_cap_combo", "display_name": "Sunglasses + Cap Combo", "threat_level": "LOW", "color_bgr": [0, 255, 255], "conf_threshold": 0.5}

        # Default fallback
        return {
            "key": "clear_face",
            "display_name": raw_class_name.title(),
            "threat_level": "NORMAL",
            "color_bgr": [0, 255, 0],
            "conf_threshold": self.conf_threshold
        }

    def process_frame(self, frame: np.ndarray, use_tracker: bool = True) -> List[Dict[str, Any]]:
        """Runs inference, face detection, and occlusion analysis on the input video frame."""
        # 1. Detect faces and concealment via keypoint & occlusion analyzer
        face_detections = self.occlusion_detector.detect_and_classify(frame)
        if face_detections:
            for det in face_detections:
                track_id = det["track_id"]
                threat_level = det["threat_level"]
                if threat_level in ["MEDIUM", "HIGH", "CRITICAL"]:
                    self.track_persistence[track_id] = self.track_persistence.get(track_id, 0) + 1
                else:
                    self.track_persistence[track_id] = max(0, self.track_persistence.get(track_id, 0) - 1)
                det["is_confirmed"] = (self.track_persistence.get(track_id, 0) >= max(1, self.persistence_frames - 1))
            return face_detections

        # 2. Fallback to YOLO model prediction/tracking
        tracker_type = self.model_cfg.get("tracker", "bytetrack.yaml")
        if use_tracker:
            results = self.model.track(
                source=frame,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                imgsz=self.imgsz,
                half=self.half,
                device=self.device.type,
                tracker=tracker_type,
                verbose=False,
                persist=True
            )
        else:
            results = self.model.predict(
                source=frame,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                imgsz=self.imgsz,
                half=self.half,
                device=self.device.type,
                verbose=False
            )

        detections = []
        if not results or len(results) == 0 or results[0].boxes is None:
            return detections

        r = results[0]
        boxes = r.boxes
        current_track_ids = set()

        for i, box in enumerate(boxes):
            coords = box.xyxy[0].cpu().numpy().tolist() # [x1, y1, x2, y2]
            conf = float(box.conf[0].cpu().item())
            cls_id = int(box.cls[0].cpu().item())
            raw_name = r.names.get(cls_id, f"class_{cls_id}")
            track_id = int(box.id[0].cpu().item()) if box.id is not None else (i + 1)
            current_track_ids.add(track_id)

            cls_meta = self._match_class_config(raw_name)
            
            # Apply per-class confidence threshold
            if conf < cls_meta["conf_threshold"]:
                continue

            threat_level = cls_meta["threat_level"]

            # Update persistence filter for concealing threats
            if threat_level in ["MEDIUM", "HIGH", "CRITICAL"]:
                self.track_persistence[track_id] = self.track_persistence.get(track_id, 0) + 1
            else:
                self.track_persistence[track_id] = max(0, self.track_persistence.get(track_id, 0) - 1)

            # Mark threat confirmed if persistent or if persistence threshold met
            is_confirmed_threat = (self.track_persistence.get(track_id, 0) >= self.persistence_frames)

            det_dict = {
                "track_id": track_id,
                "class_id": cls_id,
                "class_name": cls_meta["key"],
                "display_name": cls_meta["display_name"],
                "raw_name": raw_name,
                "confidence": conf,
                "bbox": coords,
                "threat_level": threat_level if is_confirmed_threat or threat_level in ["NORMAL", "LOW"] else "LOW",
                "color_bgr": cls_meta["color_bgr"],
                "is_confirmed": is_confirmed_threat
            }
            detections.append(det_dict)

        # Cleanup lost tracks
        stale_tracks = [tid for tid in self.track_persistence.keys() if tid not in current_track_ids]
        for tid in stale_tracks:
            del self.track_persistence[tid]

        return detections
