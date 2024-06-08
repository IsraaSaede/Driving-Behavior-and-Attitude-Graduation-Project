import cv2
import torch
import numpy as np
from tracker import Tracker


# Load the YOLOv5 model from torch hub
def load_model():
    try:
        model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        exit()


# Draw predefined polygons on the frame for visualization
def draw_polygons(frame, areas):
    colors = [(0, 255, 0), (0, 0, 0), (0, 0, 255)]
    for area, color in zip(areas, colors):
        cv2.polylines(frame, [np.array(area, np.int32)], True, color, 2)


# Process detection results to extract bounding boxes for cars
def process_detections(results, target_class='car'):
    points = []
    for index, row in results.pandas().xyxy[0].iterrows():
        if target_class in row['name']:
            x1, y1 = int(row['xmin']), int(row['ymin'])
            x2, y2 = int(row['xmax']), int(row['ymax'])
            points.append([x1, y1, x2, y2])
    return points


# Update tracker with new bounding boxes and draw results on the frame
def update_and_draw_tracker(frame, boxes_id, areas, counters):
    for box_id in boxes_id:
        x, y, w, h, idd = box_id
        # Draw bounding box and ID
        cv2.rectangle(frame, (x, y), (w, h), (255, 0, 255), 2)
        cv2.putText(frame, str(idd), (x, y), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 2)
        cv2.circle(frame, (w, h), 4, (0, 255, 0), -1)

        # Check if the detected object is within any of the predefined areas
        for i, area in enumerate(areas):
            if cv2.pointPolygonTest(np.array(area, np.int32), (w, h), False) >= 0:
                counters[i].add(idd)


# Display the count of cars in each lane on the frame
def display_counters(frame, counters):
    labels = [
        'Number of cars in the First lane: ',
        'Number of cars in the Second lane: ',
        'Number of cars in the Third lane: '
    ]
    colors = [(0, 255, 0), (0, 0, 0), (0, 0, 255)]
    for i, count_set in enumerate(counters):
        cv2.putText(frame, f"{labels[i]} {len(count_set)}", (50, 65 + 25 * i), cv2.FONT_HERSHEY_PLAIN, 2, colors[i], 2)


# Main function to run the vehicle tracking system
def main(video_path):
    model = load_model()
    tracker = Tracker()

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        exit()

    # Define areas for lane detection (adjust based on your video)
    areas = [
        [(990, 415), (1025, 415), (1370, 890), (1130, 890)],
        [(1025, 415), (1060, 415), (1610, 890), (1370, 890)],
        [(1060, 415), (1090, 415), (1830, 890), (1610, 890)]
    ]

    # Sets to keep track of unique car IDs in each lane
    counters = [set(), set(), set()]

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Draw polygons for the defined areas
        draw_polygons(frame, areas)

        # Perform object detection
        results = model(frame)
        points = process_detections(results)

        # Update the tracker with the detected bounding boxes
        boxes_id = tracker.update(points)

        # Update and draw tracker results on the frame
        update_and_draw_tracker(frame, boxes_id, areas, counters)

        # Display the number of cars in each lane
        display_counters(frame, counters)

        # Display the frame with annotations
        cv2.imshow("FRAME", frame)

        # Break the loop if the 'Esc' key is pressed
        if cv2.waitKey(1) & 0xFF == 27:
            break

    # Release video capture and destroy all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()


# Entry point of the script
if __name__ == "__main__":
    video_path = 'M6 Motorway Traffic.mp4'  # Path to the video file
    main(video_path)