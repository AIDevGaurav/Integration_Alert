import json

import cv2
import time
import os
from app.config import logger
from app.mqtt_handler import publish_message_mqtt as mqtt_publish

image_dir = "images"
video_dir = "videos"
os.makedirs(image_dir, exist_ok=True)
os.makedirs(video_dir, exist_ok=True)

def capture_image(rtsp_url):
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        image_filename = os.path.join(image_dir, f"Images_{timestamp}.jpg")
        cv2.imwrite(image_filename, rtsp_url)
        logger.info(f"Image captured and saved to {image_filename}")
        return os.path.abspath(image_filename)

    except Exception as e:
        logger.error(f"Error capturing image: {e}", exc_info=True)
        raise

def capture_video(rtsp_url):
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        video_filename = os.path.join(video_dir, f"Videos_{timestamp}.mp4")

        # Use the MP4V codec for MP4 format
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        cap_video = cv2.VideoCapture(rtsp_url)
        width = int(cap_video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap_video.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Create a VideoWriter object with MP4 format
        out = cv2.VideoWriter(video_filename, fourcc, 20.0, (width, height))

        start_time = time.time()
        while int(time.time() - start_time) < 5:  # Capture for 5 seconds
            ret, frame = cap_video.read()
            if not ret:
                break
            out.write(frame)

        cap_video.release()
        out.release()
        logger.info(f"Video captured and saved to {video_filename}")
        return os.path.abspath(video_filename)

    except Exception as e:
        logger.error(f"Error capturing video: {e}", exc_info=True)
        raise

def publish_message(motion_type, rtsp_url, camera_id, image_filename, video_filename):
    try:
        message = {
            "rtsp_link": rtsp_url,
            "cameraId": camera_id,
            "type": motion_type,
            "image": image_filename,
            "video": video_filename
        }
        mqtt_publish(json.dumps(message))
        logger.info(f"Published message: {message}")
    except Exception as e:
        logger.error(f"Error publishing MQTT message: {e}", exc_info=True)
        raise