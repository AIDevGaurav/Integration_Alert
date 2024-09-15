from flask import jsonify
from app.config import logger

class CustomError(Exception):
    """Base class for custom exceptions."""
    def __init__(self, message):
        super().__init__(message)
        logger.error(f"Error: {message}")


class MotionDetectionError(CustomError):
    """Exception raised for motion detection errors."""
    pass


def handle_exception(e):
    """Handles generic exceptions and returns a JSON response."""
    logger.error(f"Exception occurred: {str(e)}", exc_info=True)
    response = jsonify({
        "success": False,
        "error": str(e),
        "message": "An error occurred while processing your request."
    })
    response.status_code = 500
    return response
