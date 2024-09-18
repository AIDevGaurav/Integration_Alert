from flask import Blueprint, request, jsonify

from app.Armed import armed_detection_stop, armed_detection_start
from app.Pet_detect import pet_start, pet_stop
from app.Zipline import zipline_start, zipline_stop
from app.fall import fall_stop, fall_start
from app.motion_detector import motion_stop, motion_start
from app.exceptions import CustomError, handle_exception
from app.config import logger
from app.people_count import start_pc, stop_pc
from app.fire import fire_stop, fire_start

api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/motion-detection-start', methods=['POST'])
def motion():
    try:
        tasks = request.json
        if not tasks or not isinstance(tasks, list):
            raise CustomError("Invalid input data. 'tasks' should be a list.")

        for task in tasks:
            motion_start(task)

        logger.info("Motion detection tasks started successfully.")
        return jsonify({"success": True, "message": "Motion detection tasks started"}), 200
    except CustomError as e:
        return jsonify({"success": False, "error": str(e), "message": "Failed to start motion detection tasks."}), 400
    except Exception as e:
        return handle_exception(e)

@api_blueprint.route('/pet-detection-start', methods=['POST'])
def pet():
    try:
        tasks = request.json
        if not tasks or not isinstance(tasks, list):
            raise CustomError("Invalid input data. 'tasks' should be a list.")

        for task in tasks:
            pet_start(task)

        logger.info("Pet detection tasks started successfully.")
        return jsonify({"success": True, "message": "Pet detection tasks started"}), 200
    except CustomError as e:
        return jsonify({"success": False, "error": str(e), "message": "Failed to start pet detection tasks."}), 400
    except Exception as e:
        return handle_exception(e)


@api_blueprint.route('/people-count-start', methods=['POST'])
def pc():
    try:
        tasks = request.json
        if not tasks or not isinstance(tasks, list):
            raise CustomError("Invalid input data. 'tasks' should be a list.")

        for task in tasks:
            start_pc(task)

        logger.info("PC detection tasks started successfully.")
        return jsonify({"success": True, "message": "PC detection tasks started"}), 200
    except CustomError as e:
        return jsonify({"success": False, "error": str(e), "message": "Failed to start PC detection tasks."}), 400
    except Exception as e:
        return handle_exception(e)


@api_blueprint.route('/fire-start', methods=['POST'])
def fire():
    try:
        tasks = request.json
        if not tasks or not isinstance(tasks, list):
            raise CustomError("Invalid input data. 'tasks' should be a list.")

        for task in tasks:
            fire_start(task)

        logger.info("Fire detection tasks started successfully.")
        return jsonify({"success": True, "message": "Fire detection tasks started"}), 200
    except CustomError as e:
        return jsonify({"success": False, "error": str(e), "message": "Failed to start Fire detection tasks."}), 400
    except Exception as e:
        return handle_exception(e)

@api_blueprint.route('/fall-detection-start', methods=['POST'])
def fall():
    try:
        tasks = request.json
        if not tasks or not isinstance(tasks, list):
            raise CustomError("Invalid input data. 'tasks' should be a list.")

        for task in tasks:
            fall_start(task)

        logger.info("Fall detection tasks started successfully.")
        return jsonify({"success": True, "message": "Fall detection tasks started"}), 200
    except CustomError as e:
        return jsonify({"success": False, "error": str(e), "message": "Failed to start Fall detection tasks."}), 400
    except Exception as e:
        return handle_exception(e)

@api_blueprint.route('/zipline-start', methods=['POST'])
def zip():
    try:
        tasks = request.json
        if not tasks or not isinstance(tasks, list):
            raise CustomError("Invalid input data. 'tasks' should be a list.")

        for task in tasks:
            zipline_start(task)

        logger.info("Zipline detection tasks started successfully.")
        return jsonify({"success": True, "message": "Zipline detection tasks started"}), 200
    except CustomError as e:
        return jsonify({"success": False, "error": str(e), "message": "Failed to start Zipline detection tasks."}), 400
    except Exception as e:
        return handle_exception(e)

@api_blueprint.route('/arm-detection-start', methods=['POST'])
def arm():
    try:
        tasks = request.json
        if not tasks or not isinstance(tasks, list):
            raise CustomError("Invalid input data. 'tasks' should be a list.")

        for task in tasks:
            armed_detection_start(task)

        logger.info("Armed detection tasks started successfully.")
        return jsonify({"success": True, "message": "Armed detection tasks started"}), 200
    except CustomError as e:
        return jsonify({"success": False, "error": str(e), "message": "Failed to start Armed detection tasks."}), 400
    except Exception as e:
        return handle_exception(e)


@api_blueprint.route('/stop', methods=['POST'])
def stop_motion_detection():
    try:
        camera_ids = request.json.get('camera_ids', [])
        typ = request.json.get('type')
        if not isinstance(camera_ids, list):
            raise CustomError("'cameraIds' should be an array.")

        if typ == "MOTION_DETECTION":
            response = motion_stop(camera_ids)
        elif typ == "PET_DETECTION":
            response = pet_stop(camera_ids)
        elif typ == "PEOPLE_COUNT":
            response = stop_pc(camera_ids)
        elif typ == "FIRE_DETECTION":
            response = fire_stop(camera_ids)
        elif typ == "FALL_DETECTION":
            response = fall_stop(camera_ids)
        elif typ == "ZIP_LINE_CROSSING":
            response = zipline_stop(camera_ids)
        elif typ == "ARM_DETECTION":
            response = armed_detection_stop(camera_ids)
        else:
            return jsonify({"success": False, "message": "Invaild Type"}), 400

        if response["success"]:
            logger.info(f"Detection stopped for cameras: {response['stopped']}")
        else:
            logger.warning(f"No active detection found for cameras: {response['not_found']}")

        return jsonify(response), 200

    except CustomError as e:
        return jsonify({"success": False, "error": str(e), "message": "Failed to stop detection tasks."}), 400
    except Exception as e:
        return handle_exception(e)
