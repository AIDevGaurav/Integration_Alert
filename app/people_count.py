import cv2
import multiprocessing
import numpy as np
from ultralytics import YOLO
from app.mqtt_handler import publish_message_mqtt as pub
from app.exceptions import PCError
from app.config import logger
from app.utils import capture_image

# Dictionary to store the active processes
tasks_processes = {}

# Function to adjust ROI points based on provided coordinates
def set_roi_based_on_points(points, coordinates):
    x_offset = coordinates["x"]
    y_offset = coordinates["y"]

    scaled_points = []
    for point in points:
        scaled_x = int(point[0] + x_offset)
        scaled_y = int(point[1] + y_offset)
        scaled_points.append((scaled_x, scaled_y))

    return scaled_points


# Function to capture and process frames for each camera in its own process
def capture_and_process_frames(camera_id, rtsp_link, site_id, alarm_id, type, coordinates):
    try:
        model = YOLO('Model/yolov8l.pt')
        cap = cv2.VideoCapture(rtsp_link)
        if not cap.isOpened():
            return logger.error(f"Could Not Open Camera PC for {camera_id}")

        roi_points = set_roi_based_on_points(coordinates["points"], coordinates)
        roi_mask = np.zeros((coordinates["display_height"], coordinates["display_width"]), dtype=np.uint8)
        cv2.fillPoly(roi_mask, [np.array(roi_points, dtype=np.int32)], (255, 255, 255))

        previous_people_count = None  # To track the previous count

        while True:
            ret, frame = cap.read()
            if not ret:
                logger.error(f"Error: Could not read frame from RTSP stream for camera ID {camera_id}.")
                break

            # Resize the frame to the display size
            resized_frame = cv2.resize(frame, (coordinates["display_width"], coordinates["display_height"]))

            # Apply the ROI mask to the frame using bitwise AND
            imgRegion = cv2.bitwise_and(resized_frame, resized_frame, mask=roi_mask)

            # Run YOLOv8 inference on the masked frame
            results = model(imgRegion, conf=0.3, iou=0.4)

            # Initialize people count
            people_count = 0

            # Iterate through detected objects
            for box in results[0].boxes.data:
                class_id = int(box[5])
                if class_id == 0:  # Class ID 0 corresponds to 'person' in COCO
                    people_count += 1
                    # Draw bounding box
                    x1, y1, x2, y2 = map(int, box[:4])
                    cv2.rectangle(resized_frame, (x1, y1), (x2, y2), (0, 0, 0), 1)
                    # Add label
                    cv2.putText(resized_frame, "Person", (x1, y1 - 10), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.5, (0, 0, 0), 1)

            # Display the number of people detected on the frame
            cv2.putText(resized_frame, f"People count: {people_count}", (30, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Draw the selected ROI on the live stream
            if len(roi_points) > 1:
                cv2.polylines(resized_frame, [np.array(roi_points)], isClosed=True, color=(0, 255, 0), thickness=2)

            # Show the annotated frame in a separate window for each camera
            cv2.imshow(f'People Count - Camera {camera_id}', resized_frame)

            # Publish the count to MQTT and capture the frame only if the count has changed
            if previous_people_count is None or previous_people_count != people_count:
                frame_copy = frame.copy()
                image_filename = capture_image(frame_copy)
                message = {"rtsp_link": rtsp_link,
                    "siteId": site_id,
                    "cameraId": camera_id,
                    "alarmId":alarm_id,
                    "type": type,
                    "people_count": people_count,
                    "image":image_filename
                }
                pub("peoplecount/detection", message)
                # capture_image(resized_frame, cameraId, people_count)  # Capture and save the frame
                previous_people_count = people_count  # Update the previous count

            # Break the loop on 'q' key press or window close
            if (cv2.waitKey(1) & 0xFF == ord('q')) or (cv2.getWindowProperty(f'People Count - Camera {camera_id}', cv2.WND_PROP_VISIBLE) < 1):
                break

        cap.release()
        cv2.destroyAllWindows()

    except Exception as e:
        logger.error("Error During People Count")
        return PCError(f"People Count Failed for camera : {camera_id}")


def start_pc(task):
    """
    Start the motion detection process in a separate thread for the given camera task.
    """
    try:
        camera_id = task["cameraId"]
        alarm_id = task['alarmId']
        type = task["type"]
        rtsp_link = task['rtsp_link']
        x = task['x']
        y = task['y']
        display_width = task['display_width']
        display_height = task['display_height']
        points = task['points']
        site_id = task['siteId']
        coordinates = {
            "x": x,
            "y": y,
            "display_width": display_width,
            "display_height": display_height,
            "points": points
        }
        if camera_id not in tasks_processes:
            stop_event = multiprocessing.Event()
            tasks_processes[camera_id] = stop_event

            # Start motion detection in a new process
            process = multiprocessing.Process(
                target=capture_and_process_frames,
                args=(camera_id, rtsp_link, site_id, alarm_id, type, coordinates))
            tasks_processes[camera_id] = process
            process.start()
            logger.info(f"Started People Count detection for camera {camera_id}.")
        else:
            logger.warning(f"PC detection already running for camera {camera_id}.")
            return False

    except Exception as e:
        logger.error(f"Failed to start detection process for camera {camera_id}: {str(e)}", exc_info=True)
        return False
    return True


def stop_pc(camera_ids):
    """
    Stop-pc detection for the given camera IDs.
    """
    stopped_tasks = []
    not_found_tasks = []

    for camera_id in camera_ids:
        if camera_id in tasks_processes:
            try:
                tasks_processes[camera_id].terminate()  # Stop the process
                tasks_processes[camera_id].join()  # Wait for the process to stop
                del tasks_processes[camera_id]  # Remove from the dictionary
                stopped_tasks.append(camera_id)
                logger.info(f"Stopped PC detection for camera {camera_id}.")
            except Exception as e:
                logger.error(f"Failed to stop PC detection for camera {camera_id}: {str(e)}", exc_info=True)
        else:
            not_found_tasks.append(camera_id)

    return {
        "success": len(stopped_tasks) > 0,
        "stopped": stopped_tasks,
        "not_found": not_found_tasks
    }