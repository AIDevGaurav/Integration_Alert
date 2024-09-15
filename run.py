from waitress import serve
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Run the app using Waitress (or Gunicorn in production)
    serve(app, host="0.0.0.0", port=5000)
