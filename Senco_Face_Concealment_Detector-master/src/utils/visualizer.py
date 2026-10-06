import cv2
import numpy as np
from typing import List, Dict, Any, Tuple

class ConcealmentVisualizer:
    """Surveillance HUD Visualizer for Face Concealment & Masking Detection."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.classes_cfg = config.get("classes", {})
        self.ui_cfg = config.get("ui", {})
        
        # Color palette for threat severity levels
        self.threat_colors = {
            "CRITICAL": (0, 0, 255),    # Red
            "HIGH": (0, 69, 255),       # Orange-Red
            "MEDIUM": (0, 215, 255),    # Amber
            "LOW": (0, 255, 255),       # Yellow
            "NORMAL": (0, 255, 0)       # Green
        }

    def draw_rounded_rectangle(self, img: np.ndarray, pt1: Tuple[int, int], pt2: Tuple[int, int], 
                               color: Tuple[int, int, int], thickness: int = 1, r: int = 10):
        """Draws a stylish rounded rectangle on the image."""
        x1, y1 = pt1
        x2, y2 = pt2
        r = min(r, abs(x2 - x1) // 2, abs(y2 - y1) // 2)
        
        # Top-left, Top-right, Bottom-right, Bottom-left curves
        cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)
        cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)
        cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)
        cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)
        
        # Lines
        cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thickness)
        cv2.line(img, (x1 + r, y2), (x2 - r, y2), color, thickness)
        cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thickness)
        cv2.line(img, (x2, y1 + r), (x2, y2 - r), color, thickness)

    def draw_glass_box(self, img: np.ndarray, pt1: Tuple[int, int], pt2: Tuple[int, int],
                       bg_color: Tuple[int, int, int] = (20, 20, 20), alpha: float = 0.6):
        """Draws a semi-transparent glass background rectangle."""
        h, w, _ = img.shape
        x1, y1 = max(0, pt1[0]), max(0, pt1[1])
        x2, y2 = min(w, pt2[0]), min(h, pt2[1])
        if x2 <= x1 or y2 <= y1:
            return
        sub_img = img[y1:y2, x1:x2]
        colored_rect = np.full(sub_img.shape, bg_color, dtype=np.uint8)
        res = cv2.addWeighted(colored_rect, alpha, sub_img, 1 - alpha, 1.0)
        img[y1:y2, x1:x2] = res

    def annotate_frame(self, frame: np.ndarray, detections: List[Dict[str, Any]], fps: float = 0.0) -> np.ndarray:
        """Annotates video frame with target boxes, badges, threat banner, and system stats."""
        annotated = frame.copy()
        h, w, _ = annotated.shape
        highest_threat = "NORMAL"
        threat_count = 0

        for det in detections:
            bbox = det["bbox"] # [x1, y1, x2, y2]
            cls_name = det["class_name"]
            conf = det["confidence"]
            track_id = det.get("track_id", None)
            threat_level = det.get("threat_level", "NORMAL")
            color = tuple(det.get("color_bgr", (0, 255, 0)))

            if threat_level in ["HIGH", "CRITICAL"]:
                highest_threat = "CRITICAL" if threat_level == "CRITICAL" or highest_threat == "CRITICAL" else "HIGH"
                threat_count += 1
            elif threat_level == "MEDIUM" and highest_threat not in ["HIGH", "CRITICAL"]:
                highest_threat = "MEDIUM"
                threat_count += 1
            elif threat_level == "LOW" and highest_threat == "NORMAL":
                highest_threat = "LOW"

            x1, y1, x2, y2 = [int(v) for v in bbox]
            
            # Corner line thickness & Box
            thickness = 2 if threat_level in ["NORMAL", "LOW"] else 3
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
            
            # Corner markers for modern security HUD look
            corner_len = min(20, (x2 - x1) // 4, (y2 - y1) // 4)
            cv2.line(annotated, (x1, y1), (x1 + corner_len, y1), color, thickness + 2)
            cv2.line(annotated, (x1, y1), (x1, y1 + corner_len), color, thickness + 2)
            cv2.line(annotated, (x2, y1), (x2 - corner_len, y1), color, thickness + 2)
            cv2.line(annotated, (x2, y1), (x2, y1 + corner_len), color, thickness + 2)
            cv2.line(annotated, (x1, y2), (x1 + corner_len, y2), color, thickness + 2)
            cv2.line(annotated, (x1, y2), (x1, y2 - corner_len), color, thickness + 2)
            cv2.line(annotated, (x2, y2), (x2 - corner_len, y2), color, thickness + 2)
            cv2.line(annotated, (x2, y2), (x2, y2 - corner_len), color, thickness + 2)

            # Label text
            display_name = det.get("display_name", cls_name)
            label = f"{display_name} {int(conf * 100)}%"
            if track_id is not None and self.ui_cfg.get("show_track_id", True):
                label = f"ID:{track_id} | " + label

            # Label badge with glass background
            (txt_w, txt_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            badge_y1 = max(0, y1 - txt_h - 10)
            badge_y2 = y1
            self.draw_glass_box(annotated, (x1, badge_y1), (x1 + txt_w + 14, badge_y2), bg_color=(15, 15, 15), alpha=0.75)
            cv2.rectangle(annotated, (x1, badge_y1), (x1 + txt_w + 14, badge_y2), color, 1)
            cv2.putText(annotated, label, (x1 + 7, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        # Top Warning Banner if Threats Detected
        if self.ui_cfg.get("show_threat_banner", True) and highest_threat in ["MEDIUM", "HIGH", "CRITICAL"]:
            banner_h = 42
            banner_bg = self.threat_colors.get(highest_threat, (0, 0, 255))
            self.draw_glass_box(annotated, (0, 0), (w, banner_h), bg_color=banner_bg, alpha=0.85)
            
            warning_text = f"SECURITY ALERT: {highest_threat} CONCEALMENT DETECTED ({threat_count} Target{'s' if threat_count > 1 else ''})"
            (tw, th), _ = cv2.getTextSize(warning_text, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
            cv2.putText(annotated, warning_text, ((w - tw) // 2, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

        # Status & Performance Overlay HUD (Top-Left)
        hud_y_start = 50 if (highest_threat in ["MEDIUM", "HIGH", "CRITICAL"] and self.ui_cfg.get("show_threat_banner", True)) else 10
        self.draw_glass_box(annotated, (10, hud_y_start), (260, hud_y_start + 65), bg_color=(20, 20, 20), alpha=0.7)
        cv2.rectangle(annotated, (10, hud_y_start), (260, hud_y_start + 65), (70, 70, 70), 1)

        fps_text = f"FPS: {fps:.1f} | Senco AI Guard"
        status_text = f"Active Concealments: {threat_count}"
        cv2.putText(annotated, fps_text, (20, hud_y_start + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(annotated, status_text, (20, hud_y_start + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                    self.threat_colors.get(highest_threat, (0, 255, 0)), 1, cv2.LINE_AA)

        return annotated
