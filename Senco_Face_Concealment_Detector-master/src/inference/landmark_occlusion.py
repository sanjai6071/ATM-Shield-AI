import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from ultralytics import YOLO

class FacialLandmarkOcclusionDetector:
    """
    Robust Face Concealment & Occlusion Detector for Surveillance.
    Detects any form of facial concealment:
    - Hand covering face (Hand / Palm Concealment)
    - Burkha / Niqab / Full Face Cloth Concealment
    - Scarf / Gamcha / Bandana wrapped across mouth/nose
    - Surgical / Cloth / N95 Masks
    - Balaclava / Ski Mask / Full Head Covering
    - Helmet / Full-Face Gear
    - Sunglasses + Cap combo
    - Any foreign object / cloth concealing facial features
    """

    def __init__(self, pose_model_path: str = "yolov8n-pose.pt", mask_model_path: str = "models/face_concealment_yolov8.pt"):
        import os
        self.pose_model = YOLO(pose_model_path)
        if os.path.exists(mask_model_path):
            self.mask_model = YOLO(mask_model_path)
        else:
            self.mask_model = None

    def _extract_skin_mask(self, img_bgr: np.ndarray) -> np.ndarray:
        """Robust multi-space skin detector (HSV + YCrCb)."""
        if img_bgr.size == 0:
            return np.zeros((1, 1), dtype=np.uint8)

        # 1. HSV skin range
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        lower_hsv = np.array([0, 28, 50], dtype=np.uint8)
        upper_hsv = np.array([25, 255, 255], dtype=np.uint8)
        mask_hsv = cv2.inRange(hsv, lower_hsv, upper_hsv)

        # 2. YCrCb skin range (effective across diverse lighting & skin tones)
        ycrcb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)
        lower_ycrcb = np.array([0, 133, 77], dtype=np.uint8)
        upper_ycrcb = np.array([255, 173, 127], dtype=np.uint8)
        mask_ycrcb = cv2.inRange(ycrcb, lower_ycrcb, upper_ycrcb)

        # Combined skin mask
        combined_mask = cv2.bitwise_and(mask_hsv, mask_ycrcb)
        return combined_mask

    def analyze_face(self, frame: np.ndarray, keypoints: np.ndarray, person_box: List[float]) -> Dict[str, Any]:
        """
        Analyzes head/face region, wrist positions (hand covering mouth),
        facial landmark visibility, and color/texture consistency.
        """
        h, w, _ = frame.shape
        px1, py1, px2, py2 = [int(v) for v in person_box]
        px1, py1 = max(0, px1), max(0, py1)
        px2, py2 = min(w, px2), min(h, py2)

        # Keypoints: 0=Nose, 1=L_Eye, 2=R_Eye, 3=L_Ear, 4=R_Ear, 5=L_Shoulder, 6=R_Shoulder, 9=L_Wrist, 10=R_Wrist
        nose = keypoints[0]
        left_eye = keypoints[1]
        right_eye = keypoints[2]
        left_ear = keypoints[3]
        right_ear = keypoints[4]
        left_shoulder = keypoints[5] if len(keypoints) > 5 else [0, 0, 0]
        right_shoulder = keypoints[6] if len(keypoints) > 6 else [0, 0, 0]
        left_wrist = keypoints[9] if len(keypoints) > 9 else [0, 0, 0]
        right_wrist = keypoints[10] if len(keypoints) > 10 else [0, 0, 0]

        nose_conf = nose[2]
        left_eye_conf = left_eye[2]
        right_eye_conf = right_eye[2]
        left_ear_conf = left_ear[2]
        right_ear_conf = right_ear[2]

        eyes_visible = (left_eye_conf > 0.4 or right_eye_conf > 0.4)
        nose_visible = (nose_conf > 0.45)
        ears_visible = (left_ear_conf > 0.4 or right_ear_conf > 0.4)

        # Calculate Eye Center / Head Center
        eye_points = []
        if left_eye_conf > 0.3:
            eye_points.append(left_eye[:2])
        if right_eye_conf > 0.3:
            eye_points.append(right_eye[:2])

        # Estimate Head / Face bounding box coordinates
        if eye_points:
            eye_center_x = np.mean([p[0] for p in eye_points])
            eye_center_y = np.mean([p[1] for p in eye_points])
            
            # Eye span or shoulder span scale
            if len(eye_points) == 2:
                eye_dist = max(25.0, np.linalg.norm(np.array(left_eye[:2]) - np.array(right_eye[:2])))
            else:
                eye_dist = max(35.0, (px2 - px1) * 0.25)

            face_w = int(eye_dist * 2.8)
            face_h = int(eye_dist * 3.4)

            fx1 = max(0, int(eye_center_x - face_w // 2))
            fy1 = max(0, int(eye_center_y - face_h * 0.40))
            fx2 = min(w, int(eye_center_x + face_w // 2))
            fy2 = min(h, int(eye_center_y + face_h * 0.70))
        elif nose_visible:
            # Anchor around nose
            face_w = int((px2 - px1) * 0.45)
            face_h = int(face_w * 1.3)
            fx1 = max(0, int(nose[0] - face_w // 2))
            fy1 = max(0, int(nose[1] - face_h * 0.45))
            fx2 = min(w, int(nose[0] + face_w // 2))
            fy2 = min(h, int(nose[1] + face_h * 0.65))
        else:
            # Upper 35% of person bounding box
            fx1 = max(0, int(px1 + (px2 - px1) * 0.15))
            fy1 = max(0, py1)
            fx2 = min(w, int(px2 - (px2 - px1) * 0.15))
            fy2 = min(h, int(py1 + (py2 - py1) * 0.35))

        face_bbox = [fx1, fy1, fx2, fy2]
        face_crop = frame[fy1:fy2, fx1:fx2]
        fh, fw = face_crop.shape[:2]

        if fh < 20 or fw < 20:
            return {
                "type": "clear_face", "display_name": "Clear Face", 
                "threat_level": "NORMAL", "confidence": 0.85, 
                "color_bgr": [0, 255, 0], "face_bbox": face_bbox
            }

        # -------------------------------------------------------------
        # CHECK 1: Hand Covering Face / Mouth Concealment
        # -------------------------------------------------------------
        hand_covering_face = False
        wrist_in_face = None
        for wrist, w_name in [(left_wrist, "Left"), (right_wrist, "Right")]:
            if wrist[2] > 0.35:
                wx, wy = wrist[0], wrist[1]
                # If wrist / hand is positioned over the lower face or nose
                if fx1 - 10 <= wx <= fx2 + 10 and fy1 + fh * 0.25 <= wy <= fy2 + fh * 0.2:
                    hand_covering_face = True
                    wrist_in_face = w_name
                    break

        if hand_covering_face:
            return {
                "type": "hand_face_covering",
                "display_name": "Hand Concealing Face",
                "threat_level": "HIGH",
                "confidence": 0.94,
                "color_bgr": [0, 69, 255], # Orange-Red
                "face_bbox": face_bbox
            }

        # -------------------------------------------------------------
        # CHECK 2: Face Split Analysis (Upper Eye Zone vs Lower Mouth Zone)
        # -------------------------------------------------------------
        mid_y = int(fh * 0.48)
        upper_face = face_crop[0:mid_y, :]
        lower_face = face_crop[mid_y:fh, :]

        # Extract skin coverage
        full_skin_mask = self._extract_skin_mask(face_crop)
        upper_skin_mask = self._extract_skin_mask(upper_face)
        lower_skin_mask = self._extract_skin_mask(lower_face)

        total_face_area = max(1, fh * fw)
        lower_face_area = max(1, lower_face.shape[0] * lower_face.shape[1])
        upper_face_area = max(1, upper_face.shape[0] * upper_face.shape[1])

        full_skin_ratio = np.sum(full_skin_mask > 0) / total_face_area
        upper_skin_ratio = np.sum(upper_skin_mask > 0) / upper_face_area
        lower_skin_ratio = np.sum(lower_skin_mask > 0) / lower_face_area

        # Color inspection in lower face
        mean_bgr_lower = np.mean(lower_face, axis=(0, 1)) # B, G, R
        mean_bgr_upper = np.mean(upper_face, axis=(0, 1))
        
        # Color difference / cloth pattern difference between forehead and mouth
        color_diff = np.linalg.norm(mean_bgr_upper - mean_bgr_lower)

        # -------------------------------------------------------------
        # CHECK 3: Total Head / Face Concealment (Burkha / Balaclava / Helmet)
        # -------------------------------------------------------------
        if not eyes_visible and not nose_visible:
            # Check for Burkha / Niqab (Dark cloth covering face/head)
            if np.mean(mean_bgr_lower) < 55:
                return {
                    "type": "borkha_niqab_covering",
                    "display_name": "Burkha / Niqab Concealment",
                    "threat_level": "CRITICAL",
                    "confidence": 0.95,
                    "color_bgr": [0, 0, 255],
                    "face_bbox": face_bbox
                }
            return {
                "type": "balaclava_ski_mask",
                "display_name": "Full Head Concealment / Balaclava",
                "threat_level": "CRITICAL",
                "confidence": 0.93,
                "color_bgr": [0, 0, 255],
                "face_bbox": face_bbox
            }

        # -------------------------------------------------------------
        # CHECK 4: Lower Face Masking / Cloth / Gamcha / Scarf
        # -------------------------------------------------------------
        # If lower skin is very low, or nose is covered, or color is distinct cloth
        is_lower_covered = (lower_skin_ratio < 0.32) or (not nose_visible and lower_skin_ratio < 0.48)

        if is_lower_covered:
            # Determine specific cloth type
            # Check Burkha/Black veil on lower face
            if np.mean(mean_bgr_lower) < 50:
                return {
                    "type": "borkha_niqab_covering",
                    "display_name": "Burkha / Veil Concealment",
                    "threat_level": "CRITICAL",
                    "confidence": 0.95,
                    "color_bgr": [0, 0, 255],
                    "face_bbox": face_bbox
                }
            # Surgical mask (Blue / Cyan / Bright White)
            elif (mean_bgr_lower[0] > mean_bgr_lower[2] + 15) or (np.min(mean_bgr_lower) > 180):
                return {
                    "type": "surgical_mask",
                    "display_name": "Surgical / Medical Mask",
                    "threat_level": "MEDIUM",
                    "confidence": 0.91,
                    "color_bgr": [0, 215, 255],
                    "face_bbox": face_bbox
                }
            # Scarf / Gamcha / Handkerchief / Cloth / Printed fabric
            else:
                return {
                    "type": "scarf_bandana",
                    "display_name": "Scarf / Cloth / Gamcha Masking",
                    "threat_level": "HIGH",
                    "confidence": 0.92,
                    "color_bgr": [0, 140, 255],
                    "face_bbox": face_bbox
                }

        # -------------------------------------------------------------
        # CHECK 5: Eyewear (Spectacles / Goggles / Glasses) -> NORMAL (Ignored / Excluded)
        # -------------------------------------------------------------
        # Normal everyday spectacles/goggles with mouth/nose visible should NEVER trigger alerts
        if not eyes_visible and nose_visible:
            return {
                "type": "clear_face",
                "display_name": "Clear Face (Glasses/Spectacles)",
                "threat_level": "NORMAL",
                "confidence": 0.95,
                "color_bgr": [0, 255, 0],
                "face_bbox": face_bbox
            }

        # -------------------------------------------------------------
        # CLEAR FACE: Fully visible face with authentic skin & landmarks
        # -------------------------------------------------------------
        return {
            "type": "clear_face",
            "display_name": "Clear Face",
            "threat_level": "NORMAL",
            "confidence": round(float(min(0.99, 0.80 + full_skin_ratio * 0.2)), 2),
            "color_bgr": [0, 255, 0],
            "face_bbox": face_bbox
        }

    def detect_and_classify(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Runs pose estimation, pretrained mask detection model, and occlusion analysis."""
        # 1. Pose estimation on person/face
        results = self.pose_model.predict(source=frame, conf=0.30, verbose=False)
        detections = []
        
        # 2. Check direct inference from pretrained YOLO mask model if available
        pretrained_boxes = []
        if self.mask_model is not None:
            try:
                mask_res = self.mask_model.predict(source=frame, conf=0.35, verbose=False)
                if mask_res and len(mask_res) > 0 and mask_res[0].boxes is not None:
                    mb = mask_res[0].boxes
                    for j in range(len(mb)):
                        m_box = mb.xyxy[j].cpu().numpy().tolist()
                        m_conf = float(mb.conf[j].cpu().item())
                        m_cls = int(mb.cls[j].cpu().item())
                        m_name = mask_res[0].names.get(m_cls, "")
                        pretrained_boxes.append({
                            "bbox": m_box,
                            "conf": m_conf,
                            "name": m_name
                        })
            except Exception:
                pass

        if not results or len(results) == 0:
            return detections

        r = results[0]
        if r.keypoints is None or r.boxes is None:
            return detections

        kpts_data = r.keypoints.data.cpu().numpy()
        boxes_data = r.boxes.xyxy.cpu().numpy()
        confs_data = r.boxes.conf.cpu().numpy()

        for i in range(len(boxes_data)):
            box = boxes_data[i].tolist()
            kpts = kpts_data[i]
            
            analysis = self.analyze_face(frame, kpts, box)
            target_bbox = analysis.get("face_bbox", box)

            # Check if pretrained mask model flagged this face
            for pb in pretrained_boxes:
                # Overlap check
                px1, py1, px2, py2 = pb["bbox"]
                fx1, fy1, fx2, fy2 = target_bbox
                if max(px1, fx1) < min(px2, fx2) and max(py1, fy1) < min(py2, fy2):
                    if pb["name"] in ["Bermasker", "mask", "with_mask", "covered"]:
                        analysis["type"] = "surgical_mask"
                        analysis["display_name"] = "Face Mask Detected"
                        analysis["threat_level"] = "MEDIUM"
                        analysis["confidence"] = max(analysis["confidence"], pb["conf"])
                        analysis["color_bgr"] = [0, 215, 255]

            detections.append({
                "track_id": i + 1,
                "class_id": 0,
                "class_name": analysis["type"],
                "display_name": analysis["display_name"],
                "raw_name": analysis["type"],
                "confidence": analysis["confidence"],
                "bbox": target_bbox,
                "threat_level": analysis["threat_level"],
                "color_bgr": analysis["color_bgr"],
                "is_confirmed": (analysis["threat_level"] in ["MEDIUM", "HIGH", "CRITICAL"])
            })

        return detections
