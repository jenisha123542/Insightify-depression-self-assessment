from flask import Flask
from user_routes import user_bp
from admin_routes import admin_bp

app=Flask(__name__)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp,url_prefix="/admin")
app.secret_key = 'your-secret-key-123'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)