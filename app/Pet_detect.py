import cv2
import multiprocessing
import time
import json
from ultralytics import YOLO
from app.utils import capture_image, capture_video
from app.mqtt_handler import publish_message_mqtt as pub
from app.config import logger
from app.exceptions import PetError

# Animal class indices in COCO dataset
animal_classes = [15, 16, 17, 18, 19, 20, 21, 22, 23]  # Cat, Dog, etc.

# COCO class names
classnames = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
    'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
    'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
    'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
    'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
    'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]

# Global dictionary to keep track of processes
tasks_processes = {}


def detect_animal(rtsp_url, camera_id, site_id, display_width, display_height, type, co_ordinate, stop_event):
    """
    :tasks: take the rtsp url and start stream to detect animals inside stream through YOLO v8
    :return: Capture Image, Video and Publish Mqtt message
    """
    try:
        model = YOLO('Model/yolov8l.pt')
        cap = cv2.VideoCapture(rtsp_url)
        if not cap.isOpened():
            raise PetError(f"Failed to open Camera: {camera_id}")

        window_name = f'Animal Detection - Camera {camera_id}'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)  # Create a window that can be resized

        last_detection_time = 0

        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                logger.warning(f"Camera failed id: {camera_id}")
                break

            frame = cv2.resize(frame, (display_width, display_height))

            # Run YOLO detection
            results = model(frame)

            for info in results:
                parameters = info.boxes
                for box in parameters:
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    confidence = box.conf[0]
                    class_detect = int(box.cls[0])

                    current_time = time.time()
                    if class_detect in animal_classes and (current_time - last_detection_time > 10):
                        class_name = classnames[class_detect]
                        conf = confidence * 100

                        # Draw bounding box and label
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, "Animal-Detected",(x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                        frame_copy = frame.copy()
                        image_filename = capture_image(frame_copy)
                        video_filename = "testing" # capture_video(rtsp_url)

                        # Publish MQTT message
                        message = {
                            "cameraId": camera_id,
                            "class": class_name,
                            "siteId": site_id,
                            "type": type,
                            "image": image_filename,
                            "video": video_filename
                        }
                        pub("pet/detection", message)
                        # print(f"Published message: {json.dumps(message)}")
                        last_detection_time = current_time

            # Display the frame
            cv2.imshow(window_name, frame)

            # Break loop on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyWindow(window_name)

    except Exception as e:
        logger.error(f"Error for camera:{camera_id} in Pet Detection")
        raise PetError(f"Error in Pet Detection for camera id {camera_id}")

def pet_start(task):
    """
    :param task: Json Array
    tasks: Format the input data and start the pet detection with multi_processing for multiple cameras
    :return: True or false
    """
    try:
        camera_id = task["cameraId"]
        site_id = task["siteId"]
        display_width = task["display_width"]
        display_height = task["display_height"]
        types = task["type"]
        rtsp_url = task["rtsp_link"]
        co_ordinate = task["co_ordinates"]
        if camera_id not in tasks_processes:
            stop_event = multiprocessing.Event()
            tasks_processes[camera_id] = stop_event

            # Start PC detection in a new process
            process = multiprocessing.Process(target=detect_animal, args=(
                rtsp_url, camera_id, site_id, display_width, display_height, types, co_ordinate, stop_event))
            tasks_processes[camera_id] = process
            process.start()
            logger.info(f"Started PC detection for camera {camera_id}.")
        else:
            logger.warning(f"PC detection already running for camera {camera_id}.")
            return False
    except Exception as e:
        logger.error(f"Failed to start detection process for camera {camera_id}: {str(e)}", exc_info=True)
        return False
    return True

def pet_stop(camera_ids):
    """
    Stop-pet detection for the given camera IDs.
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
                logger.info(f"Stopped Pet detection for camera {camera_id}.")
            except Exception as e:
                logger.error(f"Failed to stop Pet detection for camera {camera_id}: {str(e)}", exc_info=True)
        else:
            not_found_tasks.append(camera_id)

    return {
        "success": len(stopped_tasks) > 0,
        "stopped": stopped_tasks,
        "not_found": not_found_tasks
    }


