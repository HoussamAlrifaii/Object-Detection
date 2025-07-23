import argparse
import cv2
import numpy as np
from ultralytics import YOLO
from filterpy.kalman import KalmanFilter

class KalmanBoxTracker:
    count = 0
    def __init__(self, bbox):
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.F = np.array([[1, 0, 0, 0, 1, 0, 0],
                              [0, 1, 0, 0, 0, 1, 0],
                              [0, 0, 1, 0, 0, 0, 1],
                              [0, 0, 0, 1, 0, 0, 0],
                              [0, 0, 0, 0, 1, 0, 0],
                              [0, 0, 0, 0, 0, 1, 0],
                              [0, 0, 0, 0, 0, 0, 1]])
        self.kf.H = np.array([[1, 0, 0, 0, 0, 0, 0],
                              [0, 1, 0, 0, 0, 0, 0],
                              [0, 0, 1, 0, 0, 0, 0],
                              [0, 0, 0, 1, 0, 0, 0]])
        self.kf.R[2:, 2:] *= 10.
        self.kf.P[4:, 4:] *= 1000.
        self.kf.P *= 10.
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01
        self.kf.x[:4] = self._convert_bbox_to_z(bbox)
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1

    def update(self, bbox):
        self.time_since_update = 0
        self.kf.update(self._convert_bbox_to_z(bbox))

    def predict(self):
        self.kf.predict()
        self.time_since_update += 1
        return self._convert_x_to_bbox(self.kf.x)

    def get_state(self):
        return self._convert_x_to_bbox(self.kf.x)

    @staticmethod
    def _convert_bbox_to_z(bbox):
        x1, y1, x2, y2 = bbox
        w = x2 - x1
        h = y2 - y1
        x = x1 + w / 2.
        y = y1 + h / 2.
        s = w * h
        r = w / float(h)
        return np.array([[x], [y], [s], [r]])

    @staticmethod
    def _convert_x_to_bbox(x):
        w = np.sqrt(x[2] * x[3])
        h = x[2] / w
        x1 = x[0] - w / 2.
        y1 = x[1] - h / 2.
        x2 = x[0] + w / 2.
        y2 = x[1] + h / 2.
        return [x1[0], y1[0], x2[0], y2[0]]

class KalmanTrackerManager:
    def __init__(self, iou_thresh=0.5, max_age=30):
        self.trackers = []
        self.iou_thresh = iou_thresh
        self.max_age = max_age
        self.frame_count = 0

    def update(self, detections):
        self.frame_count += 1
        updated_tracks = []
        # Predict all trackers
        for tracker in self.trackers:
            tracker.predict()

        unmatched_dets = []
        for i, det in enumerate(detections):
            matched = False
            best_iou = -1
            best_tracker = None
            for tracker in self.trackers:
                iou = self._iou(det[:4], tracker.get_state())
                if iou >= self.iou_thresh and iou > best_iou:
                    best_iou = iou
                    best_tracker = tracker
            
            if best_tracker:
                best_tracker.update(det[:4])
                updated_tracks.append((*best_tracker.get_state(), best_tracker.id, det[5]))
                matched = True
            else:
                unmatched_dets.append(det)

        # Create new trackers for unmatched detections
        for det in unmatched_dets:
            tracker = KalmanBoxTracker(det[:4])
            updated_tracks.append((*tracker.get_state(), tracker.id, det[5]))
            self.trackers.append(tracker)

        # Clean up old trackers
        self.trackers = [t for t in self.trackers if t.time_since_update <= self.max_age]
        return updated_tracks

    @staticmethod
    def _iou(bb1, bb2):
        x1 = max(bb1[0], bb2[0])
        y1 = max(bb1[1], bb2[1])
        x2 = min(bb1[2], bb2[2])
        y2 = min(bb1[3], bb2[3])
        inter_area = max(0, x2 - x1) * max(0, y2 - y1)
        bb1_area = (bb1[2] - bb1[0]) * (bb1[3] - bb1[1])
        bb2_area = (bb2[2] - bb2[0]) * (bb2[3] - bb2[1])
        return inter_area / float(bb1_area + bb2_area - inter_area + 1e-6)

def main(input_path, output_path):
    # Load YOLOv8 model
    model = YOLO("cityscapes_yolo/yolov8s_results/weights/last.pt")
    tracker = KalmanTrackerManager()
    # Video I/O
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error opening video file {input_path}")
        return
    # Get video properties for output writer
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # --- CRITICAL CHANGE HERE ---
    # Use a more browser-compatible codec for MP4
    # 'mp4v' is MPEG-4 Part 2, often not supported by browsers for streaming.
    # 'avc1' or 'H264' are common for H.264. 'XVID' is also often playable.
    # The best choice depends on your OpenCV build and system codecs.
    # Try 'avc1' first, if it doesn't work, try 'XVID'.
    fourcc = cv2.VideoWriter_fourcc(*"avc1") # Changed codec to avc1 for better browser compatibility
    # If 'avc1' doesn't work, try:
    # fourcc = cv2.VideoWriter_fourcc(*"XVID")
    # If you want to output to WebM (requires changing output_filename extension in app.py to .webm):
    # fourcc = cv2.VideoWriter_fourcc(*"VP80")

    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    # Define a horizontal counting line (e.g., at 60% of the frame height)
    counting_line_y = int(frame_height * 0.6)
    # Initialize counters
    up_count = 0
    down_count = 0
    # Store the previous centroid y-coordinate for each track to detect crossings
    track_previous_y = {}
    # Define class names for visualization (based on your Cityscapes mapping)
    class_names = {
        0: "person", 1: "rider", 2: "car", 3: "truck", 4: "bus",
        5: "motorcycle", 6: "bicycle", 7: "train", 8: "traffic light", 9: "traffic sign"
    }
    # Define a color map for each class (BGR format for OpenCV)
    class_colors = {
        0: (0, 255, 255),    # Yellow for person
        1: (255, 0, 255),    # Magenta for rider
        2: (255, 0, 0),      # Blue for car
        3: (0, 0, 255),      # Red for truck
        4: (0, 255, 0),      # Green for bus
        5: (255, 255, 0),    # Cyan for motorcycle
        6: (128, 0, 128),    # Purple for bicycle
        7: (0, 128, 255),    # Orange for train
        8: (0, 165, 255),    # Orange-Red for traffic light
        9: (255, 128, 0)     # Light Blue for traffic sign
    }
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            results = model(frame, verbose=False)[0]
            detections = [
                [*box.xyxy[0].tolist(), box.conf.item(), box.cls.item()]
                for box in results.boxes
            ]
            tracked = tracker.update(detections)
            # Process tracked objects for counting
            current_active_ids = set()
            for x1, y1, x2, y2, obj_id, cls_id in tracked:
                current_active_ids.add(obj_id)
                # Calculate current centroid y-coordinate
                current_cy = (y1 + y2) / 2
                # Get previous centroid y-coordinate
                previous_cy = track_previous_y.get(obj_id)
                if previous_cy is not None:
                    # Check for crossing the line
                    if previous_cy < counting_line_y and current_cy >= counting_line_y:
                        down_count += 1
                        print(f"Object ID {obj_id} crossed DOWN. Total down: {down_count}")
                    elif previous_cy > counting_line_y and current_cy <= counting_line_y:
                        up_count += 1
                        print(f"Object ID {obj_id} crossed UP. Total up: {up_count}")
                # Update the previous y-coordinate for the next frame
                track_previous_y[obj_id] = current_cy
            # Clean up track_previous_y for objects that are no longer tracked
            keys_to_delete = [obj_id for obj_id in track_previous_y if obj_id not in current_active_ids]
            for obj_id in keys_to_delete:
                del track_previous_y[obj_id]
            for x1, y1, x2, y2, obj_id, cls_id in tracked:
                # Get the color for the current class ID
                color = class_colors.get(int(cls_id), (255, 255, 255)) # Default to white if class ID not found
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                # Get class name
                class_name = class_names.get(int(cls_id), "unknown")
                # Display ID and Class Name with the assigned color
                label = f'ID:{obj_id} {class_name}'
                cv2.putText(frame, label, (int(x1), int(y1) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            # Draw the counting line
            cv2.line(frame, (0, counting_line_y), (frame_width, counting_line_y), (0, 255, 255), 2) # Yellow line
            # Display counts
            cv2.putText(frame, f'Up: {up_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.putText(frame, f'Down: {down_count}', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            out.write(frame)
    finally:
        cap.release()
        out.release()
        print(f"✅ Tracking completed. Saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run YOLOv8 tracking on a video file")
    parser.add_argument('--input', type=str, required=True, help='Path to input video file')
    parser.add_argument('--output', type=str, required=True, help='Path to save output video file')
    args = parser.parse_args()
    main(args.input, args.output)
