from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)
USER_DIR = "server"

# Login sayfası
@app.route('/')
def login():
    return render_template('login.html')

# Register sayfası
@app.route('/register')
def register():
    return render_template('register.html')

# Login kontrol
@app.route('/login', methods=['POST'])
def do_login():
    username = request.form.get('username')
    password = request.form.get('password')
    user_file = os.path.join(USER_DIR, f"{username}.txt")

    if os.path.exists(user_file):
        with open(user_file) as f:
            data = f.read()
            if f"password: {password}" in data:
                return redirect(url_for('panel'))
    return "Hatalı giriş!"

# Register kontrol
@app.route('/do_register', methods=['POST'])
def do_register():
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')
    user_file = os.path.join(USER_DIR, f"{username}.txt")

    if os.path.exists(user_file):
        return "Bu kullanıcı zaten kayıtlı!"
    with open(user_file, "w") as f:
        f.write(f"email: {email}\nusername: {username}\npassword: {password}")
    return redirect(url_for('login'))

# Panel
@app.route('/panel')
def panel():
    return render_template('panel.html')

if __name__ == '__main__':
    if not os.path.exists(USER_DIR):
        os.makedirs(USER_DIR)
    app.run(host='0.0.0.0', port=5000)
