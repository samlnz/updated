# File: run_admin.py
from app import create_app
from config import FLASK_HOST, ADMIN_PORT

app = create_app()

if __name__ == '__main__':
    print(f"Starting Admin Panel on {FLASK_HOST}:{ADMIN_PORT}")
    print(f"Admin URL: http://{FLASK_HOST}:{ADMIN_PORT}/admin")
    app.run(host=FLASK_HOST, port=ADMIN_PORT, debug=False)