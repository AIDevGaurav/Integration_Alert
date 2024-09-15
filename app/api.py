from flask import Blueprint, request, jsonify
from app.motion_detector import start_detection_process, stop_detection_process
from app.exceptions import CustomError, handle_exception
from app.config import logger

api_blueprint = Blueprint('api', __name__)


@api_blueprint.route('/start', methods=['POST'])
def detect_motion_endpoint():
    try:
        tasks = request.json
        if not tasks or not isinstance(tasks, list):
            raise CustomError("Invalid input data. 'tasks' should be a list.")

        for task in tasks:
            start_detection_process(task)

        logger.info("Motion detection tasks started successfully.")
        return jsonify({"success": True, "message": "Motion detection tasks started"}), 200
    except CustomError as e:
        return jsonify({"success": False, "error": str(e), "message": "Failed to start motion detection tasks."}), 400
    except Exception as e:
        return handle_exception(e)


@api_blueprint.route('/stop', methods=['POST'])
def stop_motion_detection():
    try:
        camera_ids = request.json.get('cameraIds', [])
        if not isinstance(camera_ids, list):
            raise CustomError("'cameraIds' should be an array.")

        response = stop_detection_process(camera_ids)

        if response["success"]:
            logger.info(f"Motion detection stopped for cameras: {response['stopped']}")
        else:
            logger.warning(f"No active motion detection found for cameras: {response['not_found']}")

        return jsonify({"data": response}), 200
    except CustomError as e:
        return jsonify({"success": False, "error": str(e), "message": "Failed to stop motion detection tasks."}), 400
    except Exception as e:
        return handle_exception(e)
