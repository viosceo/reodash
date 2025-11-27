from flask import Flask, render_template, request, jsonify
import requests
from services.get import Metro, Akasya
import socket

app = Flask(__name__)

# Dummy counters (gerçek sistemde DB veya cache ile tutulur)
api_count = 2
active_users = 5
daily_ops = 12

@app.route("/")
def home():
    # Kullanıcının IP adresini al
    user_ip = request.remote_addr
    return render_template("panel.html",
                           user_ip=user_ip,
                           api_count=api_count,
                           active_users=active_users,
                           daily_ops=daily_ops)

@app.route("/send", methods=["POST"])
def send_sms():
    number = request.form.get("number")
    service = request.form.get("service")

    if service == "metro":
        success, source = Metro(number)
    elif service == "akasya":
        success, source = Akasya(number)
    else:
        success, source = False, "unknown"

    if success:
        return jsonify({"status": "success", "msg": f"{source} üzerinden SMS gönderildi"})
    else:
        return jsonify({"status": "error", "msg": f"{source} üzerinden hata oluştu"})

if __name__ == "__main__":
    app.run(debug=True)
