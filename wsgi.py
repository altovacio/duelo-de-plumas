from run import app

# Rename the app variable to application for Gunicorn
application = app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
