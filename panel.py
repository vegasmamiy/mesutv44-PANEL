import subprocess
import sys
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import requests
import json
import os
import time
import threading
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "cappybeam_premium_secret_key_2023"
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

USERS_FILE = "users.json"
SMS_APIS_FILE = "sms_apis.json"
QUERY_LOGS_FILE = "query_logs.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def load_sms_apis():
    if not os.path.exists(SMS_APIS_FILE):
        default_apis = [
            {"name": "Service 1", "url": "https://api.example1.com/sms?number={phone}&message={message}"},
            {"name": "Service 2", "url": "https://api.example2.com/send?to={phone}&text={message}"},
            {"name": "Service 3", "url": "https://api.example3.com/api?phone={phone}&sms={message}"}
        ]
        with open(SMS_APIS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_apis, f, indent=2, ensure_ascii=False)
        return default_apis
    try:
        with open(SMS_APIS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_sms_apis(apis):
    with open(SMS_APIS_FILE, "w", encoding="utf-8") as f:
        json.dump(apis, f, indent=2, ensure_ascii=False)

def load_query_logs():
    if not os.path.exists(QUERY_LOGS_FILE):
        return []
    try:
        with open(QUERY_LOGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_query_logs(logs):
    if len(logs) > 1000:
        logs = logs[-1000:]
    with open(QUERY_LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

def log_query(username, query_type, parameters, result_status):
    logs = load_query_logs()
    logs.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "username": username,
        "query_type": query_type,
        "parameters": parameters,
        "result_status": result_status
    })
    save_query_logs(logs)

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper

API_URLS = {
    "telegram": lambda username, _: f"https://api.hexnox.pro/sowixapi/telegram_sorgu.php?username={username}",
    "isyeri": lambda tc, _: f"https://api.hexnox.pro/sowixapi/isyeri.php?tc={tc}",
    "hane": lambda tc, _: f"https://api.hexnox.pro/sowixapi/hane.php?tc={tc}",
    "baba": lambda tc, _: f"https://api.hexnox.pro/sowixapi/baba.php?tc={tc}",
    "anne": lambda tc, _: f"https://api.hexnox.pro/sowixapi/anne.php?tc={tc}",
    "ayak": lambda tc, _: f"http://api.hexnox.pro/sowixapi/ayak.php?tc={tc}",
    "boy": lambda tc, _: f"http://api.hexnox.pro/sowixapi/boy.php?tc={tc}",
    "burc": lambda tc, _: f"http://api.hexnox.pro/sowixapi/burc.php?tc={tc}",
    "cm": lambda tc, _: f"http://api.hexnox.pro/sowixapi/cm.php?tc={tc}",
    "cocuk": lambda tc, _: f"http://api.hexnox.pro/sowixapi/cocuk.php?tc={tc}",
    "ehlt": lambda tc, _: f"http://api.hexnox.pro/sowixapi/ehlt.php?tc={tc}",
    "email_sorgu": lambda email, _: f"http://api.hexnox.pro/sowixapi/email_sorgu.php?email={email}",
    "havadurumu": lambda sehir, _: f"http://api.hexnox.pro/sow极速飞艇开奖直播api/havadurumu.php?sehir={sehir}",
    "imei": lambda imei, _: f"https://api.hexnox.pro/sowixapi/imei.php?imei={imei}",
    "operator": lambda gsm, _: f"https://api.hexnox.pro/sowixapi/operator.php?gsm={gsm}",
    "hikaye": lambda tc, _: f"https://api.hexnox.pro/sowixapi/hikaye.php?tc={tc}",
    "hanep极速飞艇开奖直播": lambda tc, _: f"https://api.hexnox.pro/sowixapi/hanepro.php?tc={tc}",
    "muhallev": lambda tc, _: f"https://api.hexnox.pro/sowixapi/muhallev.php?tc={tc}",
    "lgs": lambda tc, _: f"http://hexnox.pro/sowixfree/lgs/lgs极速飞艇开奖直播?tc={tc}",
    "plaka": lambda plaka, _: f"http://hexnox.pro/sowixfree/plaka.php?plaka={plaka}",
    "nude": lambda _, __: f"http://hexnox.pro/sowixfree/nude.php",
    "sertifika": lambda tc, _: f"http://hexnox.pro/sowixfree/sertifika.php?tc={tc}",
    "aracparca": lambda plaka, _: f"https://hexnox.pro/sowixfree/aracparca.php?plaka={plaka}",
    "şehit": lambda ad_soyad, _: f"https://hexnox.pro/sowixfree/şehit.php?Ad={ad_soyad.split(' ')[0] if ad_soyad else ''}&Soyad={ad_soyad.split(' ')[1] if ad_soyad and ' ' in ad_soyad else ''}",
    "interpol": lambda ad_soyad, _: f"https://hexnox.pro/sowixfree/interpol.php?ad={ad_soyad.split(' ')[0] if ad_soyad else ''}&soyad={ad_soyad.split(' ')[1] if ad_soyad and ' ' in ad_soyad else ''}",
    "personel": lambda tc, _: f"https://hexnox.pro/sowixfree/personel.php?tc={tc}",
    "internet": lambda tc, _: f"https://hexnox.pro/sowixfree/internet.php?tc={tc}",
    "nvi": lambda tc, _: f"https://hexnox.pro/sowixfree/nvi.php?tc={tc}",
    "nezcane": lambda il_ilce, _: f"https://hexnox.pro/sowixfree/nezcane.php?il={il_ilce.split(' ')[0] if il_ilce else ''}&ilce={il_ilce.split(' ')[1] if il_ilce and ' ' in il_ilce else ''}",
    "basvuru": lambda tc, _: f"https://hexnox.pro/sowixfree/basvuru/basvuru.php?tc={tc}",
    "diploma": lambda tc, _: f"https://hexnox.pro/sowixfree/diploma/diploma.php?tc={tc}",
    "facebook": lambda numara, _: f"极速飞艇开奖直播://hexnox.pro/sowixfree/facebook.php?numara={numara}",
    "vergi": lambda tc, _: f"https://hexnox.pro/sowixfree/vergi/vergi.php?tc={tc}",
    "premadres": lambda tc, _: f"https://hexnox.pro/sowixfree/premadres.php?tc={tc}",
    "sgkpro": lambda tc, _: f"https://api.hexnox.pro/sowixapi/sgkpro.php?tc={tc}",
    "mhrs": lambda tc, _: f"https://hexnox.pro/sowixfree/mhrs/mhrs.php?tc={tc}",
    "premad": lambda ad_il_ilce, _: f"https://api.hexnox.pro/sowixapi/premad.php?ad={ad_il_ilce.split(' ')[0] if ad_il_ilce else ''}&il={ad_il_ilce.split(' ')[1] if ad_il_ilce and len(ad_il_ilce.split(' ')) > 1 else ''}&ilce={ad_il_ilce.split(' ')[2] if ad_il_ilce and len(ad_il_ilce.split(' ')) > 2 else ''}",
    "fatura": lambda tc, _: f"https://hexnox.pro/sowixfree/fatura.php?tc={tc}",
    "subdomain": lambda url, _: f"https://api.hexnox.pro/sowixapi/subdomain.php?url={url}",
    "sexgörsel": lambda soru, _: f"https://hexnox.pro/sowixfree/sexgörsel.php?soru={soru}",
    "meslek": lambda tc, _: f"https://api.hexnox.pro/sowixapi/meslek极速飞艇开奖直播?tc={tc}",
    "adsoyad": lambda ad, soyad: f"https://api.hexnox.pro/sowixapi/adsoyadilice.php?ad={ad}&soyad={soyad}",
    "adsoyadil": lambda ad, soyad_il: f"https://api.hexnox.pro/sowixapi/adsoyadilice.php?ad={ad}&soyad={soyad_il.split(' ')[0] if soyad_il else ''}&il={soyad_il.split(' ')[1] if soyad_il and ' ' in soyad_il else ''}",
    "tcpro": lambda tc, _: f"https://api.hexnox.pro/sowixapi/tcpro.php?tc={tc}",
    "tcgsm": lambda tc, _: f"https://api.hexnox.pro/sowixapi/tcgsm.php?tc={tc}",
    "tapu": lambda tc, _: f"https://api.hexnox.pro/sowixapi/tapu.php?tc={tc}",
    "sulale": lambda tc, _: f"https://api.hexnox.pro/sowixapi/sulale.php?tc={tc}",
    "vesika": lambda tc, _: f"http://20.122.193.203/apiservice/woxy/tc.php?tc={tc}&auth=woxynindaramcigi",
    "allvesika": lambda tc, _: f"http://84.32.15.160/apiservice/woxy/allvesika.php?tc={tc}&auth=cyberinsikimemesiamigotu",
    "okulsicil": lambda tc, _: f"https://merial.cfd/Daimon/freePeker/okulsicil.php?tc={tc}",
    "kizlik": lambda tc, _: f"http://212.68.34.148/apiservices/kizlik?tc={tc}",
    "okulno": lambda tc, _: f"https://api.hexnox.pro/sowixapi/okulno.php?tc={tc}",
    "isyeriyetkili": lambda tc, _: f"https://api.hexnox.pro/sowixapi/isyeriyetkili.php?tc={tc}",
    "gsmdetay": lambda gsm, _: f"https://api.hexnox.pro/sowixapi/gsmdetay.php?gsm={gsm}",
    "gsm": lambda gsm, _: f"https://api.hexnox.pro/sowixapi/gsm.php?gsm={gsm}",
    "adres": lambda tc, _: f"https://api.hexnox.pro/sowixapi/adres.php?tc={tc}",
    "insta": lambda username, _: f"https://keneviznewapi.onrender.com/api/insta?usr={username}",
    "facebook_hanedan": lambda ad, soyad: f"https://keneviznewapi.onrender.com/api/facebook_hanedan?ad={ad}&soyad={soyad}",
    "uni": lambda tc, _: f"https://keneviznewapi.onrender.com/api/uni?tc={tc}",
    "akp": lambda ad, soyad: f"https://keneviznewapi.onrender.com/api/akp?ad={ad}&soyad={soyad}",
    "aifoto": lambda img_url, _: f"https://keneviznewapi.onrender.com/api/aifoto?img={img_url}",
    "papara": lambda numara, _: f"https://keneviznewapi.onrender.com/api/papara?paparano={numara}",
    "ininal": lambda numara, _: f"https://keneviznewapi.onrender.com/api/ininal?ininal_no={numara}",
    "smsbomber": lambda number, _: f"https://keneviznewapi.onrender.com/api/smsbomber?number={number}"
}

QUERY_LABELS = {
    "telegram": ["Kullanıcı Adı", ""],
    "isyeri": ["TC Kimlik No", ""],
    "hane": ["TC Kimlik No", ""],
    "baba": ["TC Kimlik No", ""],
    "anne": ["TC Kimlik No", ""],
    "ayak": ["TC Kimlik No", ""],
    "boy": ["TC Kimlik No", ""],
    "burc": ["TC Kimlik No", ""],
    "cm": ["TC Kimlik No", ""],
    "cocuk": ["TC Kimlik No", ""],
    "ehlt": ["TC Kimlik No", ""],
    "email_sorgu": ["Email Adresi", ""],
    "havadurumu": ["Şehir", ""],
    "imei": ["IMEI Numarası", ""],
    "operator": ["GSM Numarası", ""],
    "hikaye": ["TC Kimlik No", ""],
    "hanepro": ["TC Kimlik No", ""],
    "muhallev": ["TC Kimlik No", ""],
    "lgs": ["TC Kimlik No", ""],
    "plaka": ["Plaka", ""],
    "nude": ["", ""],
    "sertifika": ["TC Kimlik No", ""],
    "aracparca": ["Plaka", ""],
    "şehit": ["Ad Soyad", ""],
    "interpol": ["Ad Soyad", ""],
    "personel": ["TC Kimlik No", ""],
    "internet": ["TC Kimlik No", ""],
    "nvi": ["TC Kimlik No", ""],
    "nezcane": ["İl İlçe", ""],
    "basvuru": ["TC Kimlik No", ""],
    "hanepro": ["TC Kimlik No", ""],
    "facebook": ["Telefon Numarası", ""],
    "vergi": ["TC Kimlik No", ""],
    "premadres": ["TC Kimlik No", ""],
    "sgkpro": ["TC Kimlik No", ""],
    "mhrs": ["TC Kimlik No", ""],
    "premad": ["Ad İl İlçe", ""],
    "fatura": ["TC Kimlik No", ""],
    "subdomain": ["URL", ""],
    "sexgörsel": ["Soru", ""],
    "meslek": ["TC Kimlik No", ""],
    "adsoyad": ["Ad", "Soyad"],
    "adsoyadil": ["Ad", "Soyad veya Soyad+İl"],
    "tcpro": ["TC Kimlik No", ""],
    "tcgsm": ["TC Kimlik No", ""],
    "tapu": ["TC Kimlik No", ""],
    "sulale": ["TC Kimlik No", ""],
    "vesika": ["TC Kimlik No", ""],
    "allvesika": ["TC Kimlik No", ""],
    "okulsicil": ["TC Kimlik No", ""],
    "kizlik": ["TC Kimlik No", ""],
    "okulno": ["TC Kimlik No", ""],
    "isyeriyetkili": ["TC Kimlik No", ""],
    "gsmdetay": ["GSM Numarası", ""],
    "gsm": ["GSM Numarası", ""],
    "adres": ["TC Kimlik No", ""],
    "insta": ["kullanıcı adı", ""],
    "facebook hanedan": ["ad", "soyad"],
    "uni": ["TC Kimlik No", ""],
    "ai foto": ["ımg url", ""],
    "papara": ["papara no", ""],
    "ininal": ["ininal no", ""],
    "sms bomber": ["numara", ""]




} 

QUERY_DESCRIPTIONS = {
    "telegram": "Telegram kullanıcı adı sorgulama",
    "isyeri": "İşyeri bilgileri sorgulama",
    "hane": "Hane bilgileri sorgulama",
    "baba": "Baba bilgisi sorgulama",
    "anne": "Anne bilgisi sorgulama",
    "ayak": "Ayak numarası sorgulama",
    "boy": "Boy bilgisi sorgulama",
    "burc": "Burç sorgulama",
    "cm": "CM sorgulama",
    "cocuk": "Çocuk bilgileri sorgulama",
    "ehlt": "EHLT sorgulama",
    "email_sorgu": "E-posta adresi sorgulama",
    "havadurumu": "Hava durumu sorgulama",
    "imei": "IMEI sorgulama",
    "operator": "Operatör sorgulama",
    "hikaye": "Hikaye sorgulama",
    "hanepro": "Hane Pro sorgulama",
    "muhallev": "Muhallev sorgulama",
    "lgs": "LGS sorgulama",
    "plaka": "Plaka sorgulama",
    "nude": "Nude sorgulama",
    "sertifika": "Sertifika sorgulama",
    "aracparca": "Araç parça sorgulama",
    "şehit": "Şehit sorgulama",
    "interpol": "Interpol sorgulama",
    "personel": "Personel sorgulama",
    "internet": "Internet sorgulama",
    "nvi": "NVI sorgulama",
    "nezcane": "Nezcane sorgulama",
    "basvuru": "Başvuru sorgulama",
    "diploma": "Diploma sorgulama",
    "facebook": "Facebook sorgulama",
    "vergi": "Vergi sorgulama",
    "premadres": "Premadres sorgulama",
    "sgkpro": "SGK Pro sorgulama",
    "mhrs": "MHRS sorgulama",
    "premad": "Premad sorgulama",
    "fatura": "Fatura sorgulama",
    "subdomain": "Subdomain sorgulama",
    "sexgörsel": "Sex görsel sorgulama",
    "meslek": "Meslek sorgulama",
    "adsoyad": "Ad Soyad sorgulama",
    "adsoyadil": "Ad Soyad İl sorgulama",
    "tcpro": "TC Kimlik sorgulama",
    "tcgsm": "TC GSM sorgulama",
    "tapu": "Tapu sorgulama",
    "sulale": "Sülale sorgulama",
    "vesika": "Vesika sorgulama",
    "allvesika": "Tüm vesika sorgulama",
    "okulsicil": "Okul sicil sorgulama",
    "kizlik": "Kızlık soyadı sorgulama",
    "okulno": "Okul numarası sorgulama",
    "isyeriyetkili": "İşyeri yetkili sorgulama",
    "gsmdetay": "GSM detay sorgulama",
    "gsm": "GSM sorgulama",
    "adres": "Adres sorgulama",
    "insta": "Instagram kullanıcı adı sorgulama",
    "facebook_hanedan": "Ad ve soyad ile Facebook hanedan sorgulama",
    "uni": "Üniversite sorgulama",
    "akp": "Ad ve soyad ile AKP sorgulama",
    "aifoto": "Resim URL’si ile yapay zeka fotoğraf sorgulama",
    "papara": "Papara numarası ile sorgulama",
    "ininal": "İninal kart numarası ile sorgulama",
    "turknet": "TurkNet sorgulama",
    "smsbomber": "SMS Bomber aracı - Telefon numarasına SMS gönderin"

}

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MESUTV44 | Giriş Yap</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #6c5ce7;
      --primary-dark: #5649c9;
      --secondary: #a29bfe;
      --accent: #fd79a8;
      --dark: #2d3436;
      --darker: #1e272e;
      --light: #dfe6e9;
      --success: #00b894;
      --warning: #fdcb6e;
      --danger: #d63031;
      --gray: #636e72;
      --light-gray: #b2bec3;
    }
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      font-family: 'Poppins', sans-serif;
    }
    
    body {
      background: linear-gradient(135deg, var(--darker) 0%, var(--dark) 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      color: var(--light);
    }
    
    .login-container {
      background: rgba(45, 52, 54, 0.8);
      backdrop-filter: blur(10px);
      border-radius: 20px;
      box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
      width: 100%;
      max-width: 440px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .login-header {
      background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
      padding: 30px 20px;
      text-align: center;
      position: relative;
    }
    
    .login-header::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100" opacity="0.1"><circle cx="50" cy="50" r="40" stroke="white" stroke-width="10" fill="none" /></svg>');
      background-size: 200px;
      opacity: 0.1;
    }
    
    .logo {
      width: 80px;
      height: 80px;
      margin: 0 auto 15px;
      background: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    }
    
    .logo i {
      font-size: 40px;
      color: var(--primary);
    }
    
    .login-header h1 {
      font-size: 28px;
      font-weight: 700;
      margin-bottom: 5px;
      background: linear-gradient(45deg, #fff, #e0e0e0);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    
    .login-header p {
      font-size: 14px;
      opacity: 0.8;
    }
    
    .login-form {
      padding: 30px;
    }
    
    .form-group {
      margin-bottom: 20px;
      position: relative;
    }
    
    .form-group label {
      display: block;
      margin-bottom: 8px;
      font-weight: 500;
      font-size: 14px;
      color: var(--light-gray);
    }
    
    .input-with-icon {
      position: relative;
    }
    
    .input-with-icon i {
      position: absolute;
      left: 15px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--light-gray);
      font-size: 18px;
    }
    
    .input-with-icon input {
      width: 100%;
      padding: 15px 15px 15px 50px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      background: rgba(0, 0, 0, 0.2);
      color: var(--light);
      font-size: 16px;
      transition: all 0.3s ease;
    }
    
    .input-with-icon input:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.3);
    }
    
    .input-with-icon input::placeholder {
      color: var(--light-gray);
    }
    
    .btn-login {
      width: 100%;
      padding: 15px;
      background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
      border: none;
      border-radius: 12px;
      color: white;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      box-shadow: 0 5px 15px rgba(108, 92, 231, 0.4);
    }
    
    .btn-login:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(108, 92, 231, 0.6);
    }
    
    .btn-login:active {
      transform: translateY(0);
    }
    
    .login-footer {
      text-align: center;
      margin-top: 20px;
      font-size: 14px;
      color: var(--light-gray);
    }
    
    .login-footer a {
      color: var(--secondary);
      text-decoration: none;
      font-weight: 500;
    }
    
    .login-footer a:hover {
      text-decoration: underline;
    }
    
    .alert {
      padding: 12px 15px;
      border-radius: 10px;
      margin-bottom: 20px;
      font-size: 14px;
      display: flex;
      align-items: center;
    }
    
    .alert-error {
      background: rgba(214, 48, 49, 0.2);
      border: 1px solid rgba(214, 48, 49, 0.3);
      color: #ff7675;
    }
    
    .alert i {
      margin-right: 10px;
      font-size: 18px;
    }
    
    @media (max-width: 480px) {
      .login-container {
        border-radius: 15px;
      }
      
      .login-header {
        padding: 25px 15px;
      }
      
      .login-form {
        padding: 25px 20px;
      }
    }
  </style>
</head>
<body>
  <div class="login-container">
    <div class="login-header">
      <div class="logo">
        <i class="fas fa-shield-alt"></i>
      </div>
      <h1>MESUTV44</h1>
      <p>Premium Sorgu Sistemi</p>
    </div>
    
    <div class="login-form">
      {% if error %}
      <div class="alert alert-error">
        <i class="fas fa-exclamation-circle"></i> {{ error }}
      </div>
      {% endif %}
      
      <form method="POST" action="{{ url_for('login') }}">
        <div class="form-group">
          <label for="username">Kullanıcı Adı</label>
          <div class="input-with-icon">
            <i class="fas fa-user"></i>
            <input type="text" id="username" name="username" placeholder="Kullanıcı adınız" required autocomplete="username">
          </div>
        </div>
        
        <div class="form-group">
          <label for="password">Şifre</label>
          <div class="input-with-icon">
            <i class="fas fa-lock"></i>
            <input type="password" id="password" name="password" placeholder="Şifreniz" required autocomplete="current-password">
          </div>
        </div>
        
        <button type="submit" class="btn-login">Giriş Yap</button>
      </form>
      
      <div class="login-footer">
        Hesabınız yok mu? <a href="{{ url_for('register') }}">Kayıt Ol</a>
      </div>
    </div>
  </div>
</body>
</html>
"""

REGISTER_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MESUTV44 | Kayıt Ol</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #6c5ce7;
      --primary-dark: #5649c9;
      --secondary: #a29bfe;
      --accent: #fd79a8;
      --dark: #2d3436;
      --darker: #1e272e;
      --light: #dfe6e9;
      --success: #00b894;
      --warning: #fdcb6e;
      --danger: #d63031;
      --gray: #636e72;
      --light-gray: #b2bec3;
    }
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      font-family: 'Poppins', sans-serif;
    }
    
    body {
      background: linear-gradient(135deg, var(--darker) 0%, var(--dark) 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      color: var(--light);
    }
    
    .register-container {
      background: rgba(45, 52, 54, 0.8);
      backdrop-filter: blur(10px);
      border-radius: 20px;
      box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
      width: 100%;
      max-width: 440px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .register-header {
      background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
      padding: 30px 20px;
      text-align: center;
      position: relative;
    }
    
    .register-header::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100" opacity="0.1"><circle cx="50" cy="50" r="40" stroke="white" stroke-width="10" fill="none" /></svg>');
      background-size: 200px;
      opacity: 0.1;
    }
    
    .logo {
      width: 80px;
      height: 80px;
      margin: 0 auto 15px;
      background: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    }
    
    .logo i {
      font-size: 40px;
      color: var(--primary);
    }
    
    .register-header h1 {
      font-size: 28px;
      font-weight: 700;
      margin-bottom: 5px;
      background: linear-gradient(45deg, #fff, #e0e0e0);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    
    .register-header p {
      font-size: 14px;
      opacity: 0.8;
    }
    
    .register-form {
      padding: 30px;
    }
    
    .form-group {
      margin-bottom: 20px;
      position: relative;
    }
    
    .form-group label {
      display: block;
      margin-bottom: 8px;
      font-weight: 500;
      font-size: 14px;
      color: var(--light-gray);
    }
    
    .input-with-icon {
      position: relative;
    }
    
    .input-with-icon i {
      position: absolute;
      left: 15px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--light-gray);
      font-size: 18px;
    }
    
    .input-with-icon input {
      width: 100%;
      padding: 15px 15px 15px 50px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      background: rgba(0, 0, 0, 0.2);
      color: var(--light);
      font-size: 16px;
      transition: all 0.3s ease;
    }
    
    .input-with-icon input:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.3);
    }
    
    .input-with-icon input::placeholder {
      color: var(--light-gray);
    }
    
    .btn-register {
      width: 100%;
      padding: 15px;
      background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
      border: none;
      border-radius: 12px;
      color: white;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      box-shadow: 0 5px 15px rgba(108, 92, 231, 0.4);
    }
    
    .btn-register:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(108, 92, 231, 0.6);
    }
    
    .btn-register:active {
      transform: translateY(0);
    }
    
    .register-footer {
      text-align: center;
      margin-top: 20px;
      font-size: 14px;
      color: var(--light-gray);
    }
    
    .register-footer a {
      color: var(--secondary);
      text-decoration: none;
      font-weight: 500;
    }
    
    .register-footer a:hover {
      text-decoration: underline;
    }
    
    .alert {
      padding: 12px 15px;
      border-radius: 10px;
      margin-bottom: 20px;
      font-size: 14px;
      display: flex;
      align-items: center;
    }
    
    .alert-error {
      background: rgba(214, 48, 49, 0.2);
      border: 1px solid rgba(214, 48, 49, 0.3);
      color: #ff7675;
    }
    
    .alert i {
      margin-right: 10px;
      font-size: 18px;
    }
    
    .password-strength {
      margin-top: 8px;
      height: 5px;
      border-radius: 3px;
      background: var(--gray);
      position: relative;
      overflow: hidden;
    }
    
    .password-strength::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      height: 100%;
      width: 0%;
      border-radius: 3px;
      transition: width 0.3s ease;
    }
    
    .password-strength.weak::before {
      width: 33%;
      background: var(--danger);
    }
    
    .password-strength.medium::before {
      width: 66%;
      background: var(--warning);
    }
    
    .password-strength.strong::before {
      width: 100%;
      background: var(--success);
    }
    
    @media (max-width: 480px) {
      .register-container {
        border-radius: 15px;
      }
      
      .register-header {
        padding: 25px 15px;
      }
      
      .register-form {
        padding: 25px 20px;
      }
    }
  </style>
</head>
<body>
  <div class="register-container">
    <div class="register-header">
      <div class="logo">
        <i class="fas fa-user-plus"></i>
      </div>
      <h1>Yeni Hesap</h1>
      <p>MESUTV44 Premium Sorgu Sistemi</p>
    </div>
    
    <div class="register-form">
      {% if error %}
      <div class="alert alert-error">
        <i class="fas fa-exclamation-circle"></i> {{ error }}
      </div>
      {% endif %}
      
      <form method="POST" action="{{ url_for('register') }}">
        <div class="form-group">
          <label for="username">Kullanıcı Adı</label>
          <div class="input-with-icon">
            <i class="fas fa-user"></i>
            <input type="text" id="username" name="username" placeholder="Kullanıcı adınız" required autocomplete="username">
          </div>
        </div>
        
        <div class="form-group">
          <label for="password">Şifre</label>
          <div class="input-with-icon">
            <i class="fas fa-lock"></i>
            <input type="password" id="password" name="password" placeholder="Şifreniz" required autocomplete="new-password">
          </div>
          <div class="password-strength" id="password-strength"></div>
        </div>
        
        <div class="form-group">
          <label for="password2">Şifre Tekrar</label>
          <div class="input-with-icon">
            <i class="fas fa-lock"></i>
            <input type="password" id="password2" name="password2" placeholder="Şifrenizi tekrar girin" required autocomplete="new-password">
          </div>
        </div>
        
        <button type="submit" class="btn-register">Hesap Oluştur</button>
      </form>
      
      <div class="register-footer">
        Zaten hesabınız var mı? <a href="{{ url_for('login') }}">Giriş Yap</a>
      </div>
    </div>
  </div>

  <script>
    const passwordInput = document.getElementById('password');
    const strengthBar = document.getElementById('password-strength');
    
    passwordInput.addEventListener('input', function() {
      const password = this.value;
      let strength = 0;
      
      if (password.length > 5) strength++;
      if (password.length > 8) strength++;
      if (/[A-Z]/.test(password)) strength++;
      if (/[0-9]/.test(password)) strength++;
      if (/[^A-Za-z0-9]/.test(password)) strength++;
      
      strengthBar.className = 'password-strength';
      if (password.length > 0) {
        if (strength < 2) {
          strengthBar.classList.add('weak');
        } else if (strength < 4) {
          strengthBar.classList.add('medium');
        } else {
          strengthBar.classList.add('strong');
        }
      }
    });
  </script>
</body>
</html>
"""
PANEL_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MESUTV44| Premium Sorgu Paneli</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6c5ce7;
            --primary-dark: #5649c9;
            --primary-light: #7d70e9;
            --secondary: #a29bfe;
            --accent: #fd79a8;
            --dark: #2d3436;
            --darker: #1e272e;
            --light: #dfe6e9;
            --lighter: #f5f6fa;
            --success: #00b894;
            --warning: #fdcb6e;
            --danger: #d63031;
            --info: #0984e3;
            --gray: #636e72;
            --light-gray: #b2bec3;
            --sidebar-width: 280px;
            --header-height: 70px;
            --border-radius: 12px;
            --transition: all 0.3s ease;
            --shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            --card-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Poppins', sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, var(--darker) 0%, var(--dark) 100%);
            color: var(--light);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }
        
        /* Header Styles */
        .header {
            background: rgba(45, 52, 54, 0.9);
            backdrop-filter: blur(10px);
            padding: 0 25px;
            height: var(--header-height);
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: var(--shadow);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .header-left {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .logo {
            width: 45px;
            height: 45px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 5px 15px rgba(108, 92, 231, 0.3);
        }
        
        .logo i {
            font-size: 20px;
            color: white;
        }
        
        .brand {
            font-size: 24px;
            font-weight: 700;
            background: linear-gradient(45deg, var(--light), var(--lighter));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 0.5px;
        }
        
        .header-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 15px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 30px;
            transition: var(--transition);
        }
        
        .user-info:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        
        .user-avatar {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 3px 10px rgba(108, 92, 231, 0.3);
        }
        
        .user-avatar i {
            font-size: 18px;
            color: white;
        }
        
        .user-name {
            font-weight: 500;
            font-size: 15px;
        }
        
        .btn {
            padding: 10px 18px;
            border-radius: 30px;
            border: none;
            cursor: pointer;
            font-weight: 500;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }
        
        .btn-logout {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .btn-logout:hover {
            background: rgba(255, 255, 255, 0.15);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        
        /* Main Container */
        .main-container {
            display: flex;
            flex: 1;
            margin-top: var(--header-height);
        }
        
        /* Sidebar Styles */
        .sidebar {
            width: var(--sidebar-width);
            background: rgba(45, 52, 54, 0.8);
            backdrop-filter: blur(10px);
            padding: 25px 0;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            overflow-y: auto;
            height: calc(100vh - var(--header-height));
            position: fixed;
            left: 0;
            top: var(--header-height);
            z-index: 900;
            transition: var(--transition);
        }
        
        .sidebar-section {
            margin-bottom: 30px;
        }
        
        .sidebar-title {
            padding: 0 25px 12px;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: var(--light-gray);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .sidebar-title i {
            font-size: 14px;
        }
        
        .nav-items {
            padding: 10px 15px;
        }
        
        .nav-item {
            display: flex;
            align-items: center;
            padding: 12px 20px;
            color: var(--light);
            text-decoration: none;
            transition: var(--transition);
            border-left: 3px solid transparent;
            cursor: pointer;
            border-radius: 8px;
            margin-bottom: 5px;
            font-size: 14.5px;
        }
        
        .nav-item:hover {
            background: rgba(108, 92, 231, 0.1);
            border-left-color: var(--primary);
            transform: translateX(5px);
        }
        
        .nav-item.active {
            background: linear-gradient(135deg, rgba(108, 92, 231, 0.15) 0%, rgba(86, 73, 201, 0.15) 100%);
            border-left-color: var(--primary);
            box-shadow: 0 5px 15px rgba(108, 92, 231, 0.1);
        }
        
        .nav-item i {
            margin-right: 15px;
            width: 20px;
            text-align: center;
            font-size: 16px;
        }
        
        /* Content Area */
        .content {
            flex: 1;
            padding: 30px;
            margin-left: var(--sidebar-width);
            transition: var(--transition);
        }
        
        /* Dashboard Cards */
        .dashboard-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 35px;
        }
        
        .card {
            background: rgba(45, 52, 54, 0.6);
            backdrop-filter: blur(10px);
            border-radius: var(--border-radius);
            padding: 25px;
            box-shadow: var(--card-shadow);
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: var(--transition);
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.2);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        
        .card-title {
            font-size: 16px;
            font-weight: 500;
            color: var(--light-gray);
        }
        
        .card-icon {
            width: 50px;
            height: 50px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(108, 92, 231, 0.1);
            color: var(--primary);
            font-size: 22px;
        }
        
        .card-value {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            background: linear-gradient(45deg, var(--light), var(--lighter));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .card-desc {
            font-size: 14px;
            color: var(--light-gray);
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .card-desc i {
            color: var(--success);
        }
        
        /* Query Section */
        .query-section {
            background: rgba(45, 52, 54, 0.6);
            backdrop-filter: blur(10px);
            border-radius: var(--border-radius);
            padding: 30px;
            box-shadow: var(--card-shadow);
            margin-bottom: 35px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .section-title {
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--light);
        }
        
        .section-title i {
            color: var(--primary);
            font-size: 26px;
        }
        
        .query-description {
            background: rgba(0, 0, 0, 0.15);
            padding: 18px 20px;
            border-radius: var(--border-radius);
            margin-bottom: 25px;
            font-size: 15px;
            color: var(--light-gray);
            line-height: 1.6;
            border-left: 4px solid var(--primary);
        }
        
        .query-form {
            display: grid;
            grid-template-columns: 1fr 1fr auto;
            gap: 20px;
            margin-bottom: 25px;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
        }
        
        .form-label {
            font-size: 14px;
            margin-bottom: 10px;
            color: var(--light-gray);
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .form-label i {
            color: var(--primary);
            font-size: 16px;
        }
        
        .form-input {
            padding: 15px 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: var(--border-radius);
            background: rgba(0, 0, 0, 0.15);
            color: var(--light);
            font-size: 15px;
            transition: var(--transition);
        }
        
        .form-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.2);
        }
        
        .form-input::placeholder {
            color: var(--light-gray);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            align-self: flex-end;
            height: 52px;
            font-size: 16px;
            font-weight: 600;
            box-shadow: 0 5px 15px rgba(108, 92, 231, 0.3);
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(108, 92, 231, 0.4);
        }
        
        /* Results Container */
        .results-container {
            background: rgba(45, 52, 54, 0.6);
            backdrop-filter: blur(10px);
            border-radius: var(--border-radius);
            padding: 30px;
            box-shadow: var(--card-shadow);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }
        
        .results-content {
            background: rgba(0, 0, 0, 0.15);
            border-radius: var(--border-radius);
            padding: 25px;
            min-height: 200px;
            max-height: 500px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
        }
        
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 200px;
            color: var(--light-gray);
            flex-direction: column;
            gap: 15px;
        }
        
        .loading i {
            font-size: 40px;
            color: var(--primary);
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 0.6; transform: scale(0.95); }
            50% { opacity: 1; transform: scale(1); }
            100% { opacity: 0.6; transform: scale(0.95); }
        }
        
        .result-table {
            width: 100%;
            border-collapse: collapse;
            background: rgba(0, 0, 0, 0.1);
            border-radius: var(--border-radius);
            overflow: hidden;
        }
        
        .result-table th {
            text-align: left;
            padding: 15px 20px;
            background: rgba(0, 0, 0, 0.2);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            font-weight: 600;
            color: var(--primary-light);
        }
        
        .result-table td {
            padding: 15px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .result-table tr:last-child td {
            border-bottom: none;
        }
        
        .result-table tr:hover td {
            background: rgba(255, 255, 255, 0.03);
        }
        
        /* Responsive Design */
        @media (max-width: 1200px) {
            .query-form {
                grid-template-columns: 1fr;
            }
        }
        
        @media (max-width: 968px) {
            .dashboard-cards {
                grid-template-columns: 1fr 1fr;
            }
            
            .sidebar {
                transform: translateX(-100%);
                width: 260px;
            }
            
            .sidebar.active {
                transform: translateX(0);
            }
            
            .content {
                margin-left: 0;
            }
            
            .menu-toggle {
                display: block;
            }
        }
        
        @media (max-width: 768px) {
            .dashboard-cards {
                grid-template-columns: 1fr;
            }
            
            .header {
                padding: 0 15px;
            }
            
            .brand {
                font-size: 20px;
            }
            
            .user-name {
                display: none;
            }
            
            .content {
                padding: 20px 15px;
            }
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.1);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary-dark);
        }
        
        /* Menu Toggle Button */
        .menu-toggle {
            display: none;
            background: none;
            border: none;
            color: var(--light);
            font-size: 24px;
            cursor: pointer;
            margin-right: 15px;
        }
        
        /* Search Bar */
        .search-container {
            position: relative;
            margin-bottom: 25px;
        }
        
        .search-input {
            width: 100%;
            padding: 15px 20px 15px 50px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            background: rgba(0, 0, 0, 0.15);
            color: var(--light);
            font-size: 15px;
            transition: var(--transition);
        }
        
        .search-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.2);
        }
        
        .search-icon {
            position: absolute;
            left: 20px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--light-gray);
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            <button class="menu-toggle" id="menuToggle">
                <i class="fas fa-bars"></i>
            </button>
            <div class="logo">
                <i class="fas fa-shield-alt"></i>
            </div>
            <div class="brand">/MESUTV44</div>
        </div>
        
        <div class="header-right">
            <div class="user-info">
                <div class="user-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div class="user-name">{{ session['user'] }}</div>
            </div>
            <button class="btn btn-logout" onclick="logout()">
                <i class="fas fa-sign-out-alt"></i> Çıkış
            </button>
        </div>
    </div>
    
    <div class="main-container">
        <div class="sidebar" id="sidebar">
            <div class="search-container">
                <i class="fas fa-search search-icon"></i>
                <input type="text" class="search-input" id="menuSearch" placeholder="Menüde ara..." onkeyup="filterMenu()">
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">
                    <i class="fas fa-home"></i>
                    Ana Menü
                </div>
                <div class="nav-items">
                    <a href="#" class="nav-item active" onclick="setQuery('dashboard')">
                        <i class="fas fa-home"></i>
                        <span>Dashboard</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('history')">
                        <i class="fas fa-history"></i>
                        <span>Sorgu Geçmişi</span>
                    </a>
                </div>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">
                    <i class="fas fa-id-card"></i>
                    Kişisel Sorgular
                </div>
                <div class="nav-items">
                    <a href="#" class="nav-item" onclick="setQuery('tcpro')">
                        <i class="fas fa-id-card"></i>
                        <span>TC Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('adsoyad')">
                        <i class="fas fa-user"></i>
                        <span>Ad Soyad</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('gsm')">
                        <i class="fas fa-phone"></i>
                        <span>GSM Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('adres')">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>Adres Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('vesika')">
                        <i class="fas fa-id-badge"></i>
                        <span>Vesika Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('allvesika')">
                        <i class="fas fa-id-card-alt"></i>
                        <span>Tüm Vesika Sorgu</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('anne')">
                        <i class="fas fa-female"></i>
                        <span>Anne Bilgisi</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('baba')">
                        <i class="fas fa-male"></i>
                        <span>Baba Bilgisi</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('hane')">
                        <i class="fas fa-house-user"></i>
                        <span>Hane Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('sulale')">
                        <i class="fas fa-sitemap"></i>
                        <span>Sülale Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('cocuk')">
                        <i class="fas fa-child"></i>
                        <span>Çocuk Bilgileri</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('isyeri')">
                        <i class="fas fa-building"></i>
                        <span>İşyeri Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('isyeriyetkili')">
                        <i class="fas fa-user-tie"></i>
                        <span>İşyeri Yetkili</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('tapu')">
                        <i class="fas fa-home"></i>
                        <span>Tapu Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('sgkpro')">
                        <i class="fas fa-file-medical"></i>
                        <span>SGK Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('vergi')">
                        <i class="fas fa-receipt"></i>
                        <span>Vergi Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('premadres')">
                        <i class="fas fa-address-card"></i>
                        <span>Premadres Sorgu</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('premad')">
                        <i class="fas fa-address-book"></i>
                        <span>Premad Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('nvi')">
                        <i class="fas fa-landmark"></i>
                        <span>NVI Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('muhallev')">
                        <i class="fas fa-file-contract"></i>
                        <span>Muhallev Sorgu</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('hanepro')">
                        <i class="fas fa-house-damage"></i>
                        <span>Hane Pro Sorgu</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('ehlt')">
                        <i class="fas fa-users"></i>
                        <span>EHLT Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('ayak')">
                        <i class="fas fa-shoe-prints"></i>
                        <span>Ayak No Sorgu</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('boy')">
                        <i class="fas fa-ruler-vertical"></i>
                        <span>Boy Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('burc')">
                        <i class="fas fa-star"></i>
                        <span>Burç Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('cm')">
                        <i class="fas fa-ruler"></i>
                        <span>CM Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('meslek')">
                        <i class="fas fa-briefcase"></i>
                        <span>Meslek Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('tcgsm')">
                        <i class="fas fa-phone-alt"></i>
                        <span>TC GSM Sorgu</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('adsoyadil')">
                        <i class="fas fa-user-plus"></i>
                        <span>Ad Soyad İl Sorgu</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('personel')">
                        <i class="fas fa-user-md"></i>
                        <span>Personel Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('internet')">
                        <i class="fas fa-wifi"></i>
                        <span>Internet Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('fatura')">
                        <i class="fas fa-file-invoice-dollar"></i>
                        <span>Fatura Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('mhrs')">
                        <i class="fas fa-hospital"></i>
                        <span>MHRS Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('basvuru')">
                        <i class="fas fa-file-signature"></i>
                        <span>Başvuru Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('diploma')">
                        <i class="fas fa-graduation-cap"></i>
                        <span>Diploma Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('okulno')">
                        <i class="fas fa-school"></i>
                        <span>Okul No Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('okulsicil')">
                        <i class="fas fa-user-graduate"></i>
                        <span>Okul Sicil Sorgu</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('lgs')">
                        <i class="fas fa-book"></i>
                        <span>LGS Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('sertifika')">
                        <i class="fas fa-certificate"></i>
                        <span>Sertifika Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('kizlik')">
                        <i class="fas fa-female"></i>
                        <span>Kızlık Soyadı</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('hikaye')">
                        <i class="fas fa-book-open"></i>
                        <span>Hikaye Sorgulama</span>
                    </a>
                </div>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">
                    <i class="fas fa-share-alt"></i>
                    Sosyal Medya
                </div>
                <div class="nav-items">
                    <a href="#" class="nav-item" onclick="setQuery('telegram')">
                        <i class="fab fa-telegram"></i>
                        <span>Telegram Sorgu</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('facebook')">
                        <i class="fab fa-facebook"></i>
                        <span>Facebook Sorgu</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('email_sorgu')">
                        <i class="fas fa-envelope"></i>
                        <span>Email Sorgu</span>
                    </a>
                </div>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">
                    <i class="fas fa-car"></i>
                    Araç & Araç Bilgileri
                </div>
                <div class="nav-items">
                    <a href="#" class="nav-item" onclick="setQuery('plaka')">
                        <i class="fas fa-car"></i>
                        <span>Plaka Sorgulama</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('aracparca')">
                        <i class="fas fa-tools"></i>
                        <span>Araç Parça Sorgu</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('imei')">
                        <i class="fas fa-mobile-alt"></i>
                        <span>IMEI Sorgulama</span>
                    </a>
                </div>
            </div>
            
            <div class="sidebar-section">
    <div class="sidebar-title">
        <i class="fas fa-ellipsis-h"></i>
        Diğer Sorgular
    </div>
    <div class="nav-items">
        <a href="#" class="nav-item" onclick="setQuery('operator')">
            <i class="fas fa-sim-card"></i>
            <span>Operatör Sorgulama</span>
        </a>
        <a href="#" class="nav-item" onclick="setQuery('gsmdetay')">
            <i class="fas fa-phone-square"></i>
            <span>GSM Detay Sorgu</span>
        </a>
        <a href="#" class="nav-item" onclick="setQuery('havadurumu')">
            <i class="fas fa-cloud-sun"></i>
            <span>Hava Durumu</span>
        </a>
        <a href="#" class="nav-item" onclick="setQuery('subdomain')">
            <i class="fas fa-globe"></i>
            <span>Subdomain Sorgu</span>
        </a>
        <a href="#" class="nav-item" onclick="setQuery('nezcane')">
            <i class="fas fa-map-marked-alt"></i>
            <span>Nezcane Sorgulama</span>
        </a>
        <a href="#" class="nav-item" onclick="setQuery('şehit')">
            <i class="fas fa-medal"></i>
            <span>Şehit Sorgulama</span>
        </a>
        <a href="#" class="nav-item" onclick="setQuery('interpol')">
            <i class="fas fa-globe-americas"></i>
            <span>Interpol Sorgulama</span>
        </a>
        <a href="#" class="nav-item" onclick="setQuery('sexgörsel')">
            <i class="fas fa-image"></i>
            <span>Sex Görsel Sorgu</span>
        </a>
        <a href="#" class="nav-item" onclick="setQuery('nude')">
            <i class="fas fa-ban"></i>
            <span>Nude Sorgulama</span>
        </a>
        <!-- Yeni eklenenler -->
        <a href="#" class="nav-item" onclick="setQuery('insta')">
            <i class="fab fa-instagram"></i>
            <span>Instagram Sorgulama</span>
        </a>
        <a href="#" class="nav-item" onclick="setQuery('facebook_hanedan')">
            <i class="fab fa-facebook"></i>
            <span>Facebook Hanedan</span>
        </a>
        <a href="#" class="nav-item" onclick="setQuery('uni')">
            <i class="fas fa-university"></i>
            <span>Üniversite Sorgu</span>
        </a>
        <a href="#" class="nav-item" onclick="setQuery('akp')">
            <i class="fas fa-landmark"></i>
            <span>AKP Sorgulama</span>
        </a>
        <a href="#" class="nav-item" onclick="setQuery('aifoto')">
            <i class="fas fa-robot"></i>
            <span>AI Foto</span>
        </a>
        <a href="#" class="nav-item" onclick="setQuery('papara')">
            <i class="fas fa-wallet"></i>
            <span>Papara Sorgu</span>
        </a>
        <a href="#" class="nav-item" onclick="setQuery('ininal')">
            <i class="fas fa-credit-card"></i>
            <span>İninal Sorgu</span>
        </a>
        <a href="#" class="nav-item" onclick="setQuery('turknet')">
            <i class="fas fa-wifi"></i>
            <span>TurkNet Sorgu</span>
        </a>
     </a>
        <a href="#" class="nav-item" onclick="setQuery('discord sunucu: https://discord.gg/MESUTV44')">
            <i class="fas fa-credit-card"></i>
            <span>/MESUTV44</span>
        </a>
    </div>
</div>

            
            <div class="sidebar-section">
                <div class="sidebar-title">
                    <i class="fas fa-tools"></i>
                    Araçlar
                </div>
                <div class="nav-items">
                    <a href="#" class="nav-item" onclick="setQuery('smsbomber')">
                        <i class="fas fa-bomb"></i>
                        <span>SMS Bomber</span>
                    </a>
                    <a href="#" class="nav-item" onclick="setQuery('smsapi')">
                        <i class="fas fa-cog"></i>
                        <span>API Yönetimi</span>
                    </a>
                        </a>
                    <a href="#" class="nav-item" onclick="setQuery('smsapi')">
                        <i class="fas fa-cog"></i>
                        <span>API Yönetimi</span>
                    </a>
                       <a href="#" class="nav-item" onclick="setQuery('smsbomber')">
                        <i class="fas fa-cog"></i>
                        <span>smsbomberv2</span>
                    </a>
                </div>
            </div>
        </div>
        
        <div class="content" id="content">
            <div class="dashboard-cards" id="dashboard-cards">
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Toplam Sorgu</div>
                        <div class="card-icon">
                            <i class="fas fa-search"></i>
                        </div>
                    </div>
                    <div class="card-value">1,248</div>
                    <div class="card-desc">
                        <i class="fas fa-arrow-up"></i>
                        Bugün: 42 sorgu
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Başarılı Sorgu</div>
                        <div class="card-icon">
                            <i class="fas fa-check-circle"></i>
                        </div>
                    </div>
                    <div class="card-value">1,032</div>
                    <div class="card-desc">
                        <i class="fas fa-chart-line"></i>
                        %82.7 başarı oranı
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Aktif Kullanıcı</div>
                        <div class="card-icon">
                            <i class="fas fa-users"></i>
                        </div>
                    </div>
                    <div class="card-value">156</div>
                    <div class="card-desc">
                        <i class="fas fa-user-clock"></i>
                        Şu anda çevrimiçi
                    </div>
                </div>
            </div>
            
            <div class="query-section" id="query-section">
                <div class="section-title">
                    <i class="fas fa-search"></i>
                    <span id="query-title">Sorgu Merkezi</span>
                </div>
                
                <div class="query-description" id="query-description">
                    Lütfen soldaki menüden bir sorgu tipi seçin.
                </div>
                
                <div class="query-form">
                    <div class="form-group">
                        <label class="form-label" id="input1-label">
                            <i class="fas fa-tag"></i>
                            TC Kimlik No
                        </label>
                        <input type="text" class="form-input" id="input1" placeholder="TC kimlik numarası">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" id="input2-label">
                            <i class="fas fa-tags"></i>
                            Ek Parametre
                        </label>
                        <input type="text" class="form-input" id="input2" placeholder="İsteğe bağlı parametre">
                    </div>
                    
                    <button class="btn btn-primary" onclick="runQuery()">
                        <i class="fas fa-play"></i> Sorgula
                    </button>
                </div>
            </div>
            
            <div class="results-container">
                <div class="results-header">
                    <div class="section-title">
                        <i class="fas fa-list"></i>
                        <span>Sorgu Sonuçları</span>
                    </div>
                    <button class="btn btn-logout" onclick="clearResults()">
                        <i class="fas fa-trash"></i> Temizle
                    </button>
                </div>
                
                <div class="results-content" id="results">
                    <div class="loading">
                        <i class="fas fa-search"></i>
                        <span>Sorgu sonuçları burada görünecek</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentQuery = 'dashboard';
        const queryDescriptions = {
                        'dashboard': 'Ana sayfa - Sistem istatistiklerini görüntüleyin',
            'history': 'Sorgu geçmişi - Önceki sorgularınızı görüntüleyin',
            'tcpro': 'TC Kimlik numarası ile detaylı kişi sorgulama',
            'adsoyad': 'Ad ve soyad ile kişi sorgulama',
            'gsm': 'Telefon numarası sorgulama',
            'adres': 'TC Kimlik numarası ile adres sorgulama',
            'vesika': 'TC Kimlik numarası ile vesika sorgulama',
            'allvesika': 'TC Kimlik numarası ile tüm vesika bilgilerini sorgulama',
            'anne': 'TC Kimlik numarası ile anne bilgisi sorgulama',
            'baba': 'TC Kimlik numarası ile baba bilgisi sorgulama',
            'hane': 'TC Kimlik numarası ile hane bilgileri sorgulama',
            'sulale': 'TC Kimlik numarası ile sülale bilgileri sorgulama',
            'cocuk': 'TC Kimlik numarası ile çocuk bilgileri sorgulama',
            'isyeri': 'TC Kimlik numarası ile işyeri bilgileri sorgulama',
            'isyeriyetkili': 'TC Kimlik numarası ile işyeri yetkili sorgulama',
            'tapu': 'TC Kimlik numarası ile tapu bilgileri sorgulama',
            'sgkpro': 'TC Kimlik numarası ile SGK bilgileri sorgulama',
            'vergi': 'TC Kimlik numarası ile vergi bilgileri sorgulama',
            'premadres': 'TC Kimlik numarası ile premadres sorgulama',
            'premad': 'Ad, il ve ilçe bilgileri ile premad sorgulama',
            'nvi': 'TC Kimlik numarası ile NVI sorgulama',
            'muhallev': 'TC Kimlik numarası ile muhallev sorgulama',
            'hanepro': 'TC Kimlik numarası ile hane pro sorgulama',
            'ehlt': 'TC Kimlik numarası ile EHLT sorgulama',
            'ayak': 'TC Kimlik numarası ile ayak numarası sorgulama',
            'boy': 'TC Kimlik numarası ile boy bilgisi sorgulama',
            'burc': 'TC Kimlik numarası ile burç sorgulama',
            'cm': 'TC Kimlik numarası ile CM sorgulama',
            'meslek': 'TC Kimlik numarası ile meslek sorgulama',
            'tcgsm': 'TC Kimlik numarası ile GSM sorgulama',
            'adsoyadil': 'Ad, soyad ve il bilgileri ile kişi sorgulama',
            'personel': 'TC Kimlik numarası ile personel sorgulama',
            'internet': 'TC Kimlik numarası ile internet sorgulama',
            'fatura': 'TC Kimlik numarası ile fatura sorgulama',
            'mhrs': 'TC Kimlik numarası ile MHRS sorgulama',
            'basvuru': 'TC Kimlik numarası ile başvuru sorgulama',
            'diploma': 'TC Kimlik numarası ile diploma sorgulama',
            'okulno': 'TC Kimlik numarası ile okul numarası sorgulama',
            'okulsicil': 'TC Kimlik numarası ile okul sicil sorgulama',
            'lgs': 'TC Kimlik numarası ile LGS sorgulama',
            'sertifika': 'TC Kimlik numarası ile sertifika sorgulama',
            'kizlik': 'TC Kimlik numarası ile kızlık soyadı sorgulama',
            'hikaye': 'TC Kimlik numarası ile hikaye sorgulama',
            'telegram': 'Telegram kullanıcı adı sorgulama',
            'facebook': 'Facebook/Telefon numarası sorgulama',
            'email_sorgu': 'E-posta adresi sorgulama',
            'plaka': 'Plaka sorgulama',
            'aracparca': 'Plaka ile araç parça sorgulama',
            'imei': 'IMEI numarası sorgulama',
            'operator': 'GSM numarası ile operatör sorgulama',
            'gsmdetay': 'GSM numarası ile detaylı sorgulama',
            'havadurumu': 'Şehir ile hava durumu sorgulama',
            'subdomain': 'URL ile subdomain sorgulama',
            'nezcane': 'İl ve ilçe ile nezcane sorgulama',
            'şehit': 'Ad soyad ile şehit sorgulama',
            'interpol': 'Ad soyad ile interpol sorgulama',
            'sexgörsel': 'Soru ile sex görsel sorgulama',
            'nude': 'Nude sorgulama',
            'smsbomber': 'SMS Bomber aracı - Telefon numarasına SMS gönderin',
            'smsapi': 'API Yönetimi - SMS API ayarlarını yönetin',
            'insta': 'Instagram kullanıcı adı ile sorgulama',
            'facebook_hanedan': 'Ad ve soyad ile Facebook hanedan sorgulama',
            'uni': 'TC Kimlik numarası ile üniversite sorgulama',
            'akp': 'Ad ve soyad ile AKP sorgulama',
            'aifoto': 'Resim URL’si ile yapay zeka fotoğraf sorgulama',
            'papara': 'Papara numarası ile sorgulama',
            'ininal': 'İninal kart numarası ile sorgulama',
            'turknet': 'TC Kimlik numarası ile TurkNet sorgulama',
            'smsbomber': 'SMS Bomber aracı - Telefon numarasına SMS gönderin'

           
        };
        
        const queryLabels = {
            "dashboard": ["", ""],
            "history": ["", ""],
                "telegram": ["Kullanıcı Adı", ""],
            "isyeri": ["TC Kimlik No", ""],
            "hane": ["TC Kimlik No", ""],
            "baba": ["TC Kimlik No", ""],
            "anne": ["TC Kimlik No", ""],
            "ayak": ["TC Kimlik No", ""],
            "boy": ["TC Kimlik No", ""],
            "burc": ["TC Kimlik No", ""],
            "cm": ["TC Kimlik No", ""],
            "cocuk": ["TC Kimlik No", ""],
            "ehlt": ["TC Kimlik No", ""],
            "email_sorgu": ["Email Adresi", ""],
            "havadurumu": ["Şehir", ""],
            "imei": ["IMEI Numarası", ""],
            "operator": ["GSM Numarası", ""],
            "hikaye": ["TC Kimlik No", ""],
            "hanepro": ["TC Kimlik No", ""],
            "muhallev": ["TC Kimlik No", ""],
            "lgs": ["TC Kimlik No", ""],
            "plaka": ["Plaka", ""],
            "nude": ["", ""],
            "sertifika": ["TC Kimlik No", ""],
            "aracparca": ["Plaka", ""],
            "şehit": ["Ad Soyad", ""],
            "interpol": ["Ad Soyad", ""],
            "personel": ["TC Kimlik No", ""],
            "internet": ["TC Kimlik No", ""],
            "nvi": ["TC Kimlik No", ""],
            "nezcane": ["İl İlçe", ""],
            "basvuru": ["TC Kimlik No", ""],
            "hanepro": ["TC Kimlik No", ""],
            "facebook": ["Telefon Numarası", ""],
            "vergi": ["TC Kimlik No", ""],
            "premadres": ["TC Kimlik No", ""],
            "sgkpro": ["TC Kimlik No", ""],
            "mhrs": ["TC Kimlik No", ""],
            "premad": ["Ad İl İlçe", ""],
            "fatura": ["TC Kimlik No", ""],
            "subdomain": ["URL", ""],
            "sexgörsel": ["Soru", ""],
            "meslek": ["TC Kimlik No", ""],
            "adsoyad": ["Ad", "Soyad"],
            "adsoyadil": ["Ad", "Soyad veya Soyad+İl"],
            "tcpro": ["TC Kimlik No", ""],
            "tcgsm": ["TC Kimlik No", ""],
            "tapu": ["TC Kimlik No", ""],
            "sulale": ["TC Kimlik No", ""],
            "vesika": ["TC Kimlik No", ""],
            "allvesika": ["TC Kimlik No", ""],
            "okulsicil": ["TC Kimlik No", ""],
            "kizlik": ["TC Kimlik No", ""],
            "okulno": ["TC Kimlik No", ""],
            "isyeriyetkili": ["TC Kimlik No", ""],
            "gsmdetay": ["GSM Numarası", ""],
            "gsm": ["GSM Numarası", ""],
            "adres": ["TC Kimlik No", ""],
            "insta": ["kullanıcı adı", ""],
            "facebook hanedan": ["ad", "soyad"],
            "uni": ["TC Kimlik No", ""],
            "ai foto": ["ımg url", ""],
            "papara": ["papara no", ""],
            "ininal": ["ininal no", ""],
            "sms bomber": ["numara", ""],
            "smsbomber": ["Telefon Numarası", "Mesaj (Opsiyonel)"],
            "smsapi": ["API Adı", "API URL"]
        };
        
        // Menü arama fonksiyonu
        function filterMenu() {
            const input = document.getElementById('menuSearch');
            const filter = input.value.toUpperCase();
            const navItems = document.querySelectorAll('.nav-item');
            
            navItems.forEach(item => {
                const text = item.textContent || item.innerText;
                if (text.toUpperCase().indexOf(filter) > -1) {
                    item.style.display = '';
                    // Vurgulama ekle
                    if (filter) {
                        const regex = new RegExp(filter, 'gi');
                        item.innerHTML = item.innerHTML.replace(regex, match => `<span style="background-color: rgba(108, 92, 231, 0.3); border-radius: 3px; padding: 0 2px;">${match}</span>`);
                    }
                } else {
                    item.style.display = 'none';
                }
            });
        }
        
        // Menü toggle fonksiyonu
        document.getElementById('menuToggle').addEventListener('click', function() {
            document.getElementById('sidebar').classList.toggle('active');
        });
        
        function setQuery(queryType) {
            currentQuery = queryType;
            updateFormLabels();
            
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            
            event.currentTarget.classList.add('active');
            
            if (currentQuery === 'dashboard' || currentQuery === 'history') {
                document.getElementById('query-section').style.display = 'none';
                document.getElementById('dashboard-cards').style.display = 'grid';
            } else {
                document.getElementById('query-section').style.display = 'block';
                document.getElementById('dashboard-cards').style.display = 'none';
            }
        }
        
        function updateFormLabels() {
            document.getElementById('query-title').textContent = currentQuery.toUpperCase() + ' Sorgulama';
            document.getElementById('query-description').textContent = queryDescriptions[currentQuery] || 'Sorgu açıklaması';
            
            document.getElementById('input1-label').innerHTML = `<i class="fas fa-tag"></i> ${queryLabels[currentQuery][0]}`;
            document.getElementById('input2-label').innerHTML = `<i class="fas fa-tags"></i> ${queryLabels[currentQuery][1]}`;
            document.getElementById('input1').placeholder = queryLabels[currentQuery][0] + ' girin';
            document.getElementById('input2').placeholder = queryLabels[currentQuery][1] + ' girin';
            
            if (queryLabels[currentQuery][0] === '') {
                document.getElementById('input1-label').style.display = 'none';
                document.getElementById('input1').style.display = 'none';
            } else {
                document.getElementById('input1-label').style.display = 'flex';
                document.getElementById('input1').style.display = 'block';
            }
            
            if (queryLabels[currentQuery][1] === '') {
                document.getElementById('input2-label').style.display = 'none';
                document.getElementById('input2').style.display = 'none';
            } else {
                document.getElementById('input2-label').style.display = 'flex';
                document.getElementById('input2').style.display = 'block';
            }
        }
        
        function runQuery() {
            const input1 = document.getElementById('input1').value;
            const input2 = document.getElementById('input2').value;
            
            if (currentQuery === 'dashboard' || currentQuery === 'history') {
                document.getElementById('results').innerHTML = `
                    <div style="padding: 20px; text-align: center; color: var(--light-gray);">
                        <i class="fas fa-info-circle" style="font-size: 48px; margin-bottom: 15px;"></i>
                        <h3>${currentQuery === 'dashboard' ? 'Dashboard' : 'Sorgu Geçmişi'} Sayfası</h3>
                        <p>Bu sayfa henüz implemente edilmemiştir.</p>
                    </div>
                `;
                return;
            }
            
            // Özel durumlar için validasyon
            if ((currentQuery === 'adsoyad' || currentQuery === 'adsoyadil') && !input1) {
                showError('Lütfen en az bir ad bilgisi girin.');
                return;
            }
            
            if (queryLabels[currentQuery][0] !== '' && !input1) {
                showError(`Lütfen ${queryLabels[currentQuery][0]} alanını doldurun.`);
                return;
            }
            
            document.getElementById('results').innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner"></i>
                    <span>Sorgu yapılıyor, lütfen bekleyin...</span>
                </div>
            `;
            
            fetch("/api/query", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    query: currentQuery,
                    val1: input1,
                    val2: input2
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showError(data.error);
                } else {
                    displayResults(data.result);
                }
            })
            .catch(error => {
                showError('İstek hatası: ' + error.message);
            });
        }
        
        function showError(message) {
            document.getElementById('results').innerHTML = `
                <div style="color: var(--danger); padding: 20px; text-align: center;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 15px;"></i>
                    <h3>Hata</h3>
                    <p>${message}</p>
                </div>
            `;
        }
        
        function displayResults(data) {
            let html = '';
            
            if (Array.isArray(data) && data.length > 0) {
                html = '<table class="result-table">';
                html += '<tr>';
                Object.keys(data[0]).forEach(key => {
                    html += `<th>${key}</th>`;
                });
                html += '</tr>';
                
                data.forEach(row => {
                    html += '<tr>';
                    Object.values(row).forEach(value => {
                        html += `<td>${value || ''}</td>`;
                    });
                    html += '</tr>';
                });
                
                html += '</table>';
            } else if (typeof data === 'object' && data !== null) {
                html = '<table class="result-table">';
                for (const [key, value] of Object.entries(data)) {
                    html += `<tr><th>${key}</th><td>${value || ''}</td></tr>`;
                }
                html += '</table>';
            } else if (typeof data === 'string') {
                html = `<div style="white-space: pre-wrap;">${data}</div>`;
            } else {
                html = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            }
            
            document.getElementById('results').innerHTML = html;
        }
        
        function clearResults() {
            document.getElementById('results').innerHTML = `
                <div class="loading">
                    <i class="fas fa-search"></i>
                    <span>Sorgu sonuçları burada görünecek</span>
                </div>
            `;
        }
        
        function logout() {
            window.location.href = "/logout";
        }
        
        // Sayfa yüklendiğinde
        document.addEventListener('DOMContentLoaded', function() {
            updateFormLabels();
            
            // Mobil menü için dışarı tıklama kapatma
            document.addEventListener('click', function(event) {
                const sidebar = document.getElementById('sidebar');
                const menuToggle = document.getElementById('menuToggle');
                
                if (window.innerWidth <= 968 && 
                    !sidebar.contains(event.target) && 
                    !menuToggle.contains(event.target) &&
                    sidebar.classList.contains('active')) {
                    sidebar.classList.remove('active');
                }
            });
        });
    </script>
</body>
</html>
"""
@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("panel"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        users = load_users()
        if username in users and check_password_hash(users[username]["password"], password):
            session["user"] = username
            session.permanent = True
            return redirect(url_for("panel"))
        else:
            error = "Kullanıcı adı veya şifre hatalı."
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        if not username or not password or not password2:
            error = "Tüm alanları doldurun."
        elif password != password2:
            error = "Şifreler eşleşmiyor."
        elif len(password) < 6:
            error = "Şifre en az 6 karakter olmalıdır."
        else:
            users = load_users()
            if username in users:
                error = "Bu kullanıcı adı zaten alınmış."
            else:
                users[username] = {
                    "password": generate_password_hash(password),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                save_users(users)
                session["user"] = username
                session.permanent = True
                return redirect(url_for("panel"))
    return render_template_string(REGISTER_HTML, error=error)

@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/panel")
@login_required
def panel():
    return render_template_string(PANEL_HTML)

@app.route("/api/query", methods=["POST"])
@login_required
def api_query():
    data = request.get_json()
    query = data.get("query")
    val1 = data.get("val1")
    val2 = data.get("val2")

    if query not in API_URLS:
        return jsonify({"error": "Geçersiz sorgu tipi."})

    url_func = API_URLS[query]
    result_status = "error"

    try:
        if query == "nude":
            url = url_func("", "")
        elif query in ["şehit", "interpol"]:
            if val1 and ' ' in val1:
                parts = val1.split(' ')
                ad = parts[0]
                soyad = ' '.join(parts[1:])
                url = url_func(f"{ad} {soyad}", val2)
            else:
                url = url_func(val1, val2)
        elif query == "nezcane":
            if val1 and ' ' in val1:
                parts = val1.split(' ')
                il = parts[0]
                ilce = ' '.join(parts[1:])
                url = url_func(f"{il} {ilce}", val2)
            else:
                url = url_func(val1, val2)
        elif query == "premad":
            if val1 and ' ' in val1:
                parts = val1.split(' ')
                if len(parts) >= 3:
                    ad = parts[0]
                    il = parts[1]
                    ilce = ' '.join(parts[2:])
                    url = url_func(f"{ad} {il} {ilce}", val2)
                elif len(parts) == 2:
                    ad = parts[0]
                    il = parts[1]
                    url = url_func(f"{ad} {il}", val2)
                else:
                    url = url_func(val1, val2)
            else:
                url = url_func(val1, val2)
        else:
            url = url_func(val1, val2)

        r = requests.get(url, timeout=15)
        r.raise_for_status()
        result_status = "success"

        try:
            result = r.json()
            if isinstance(result, list):
                return jsonify({"result": result})
            elif isinstance(result, dict) and ("data" in result or "results" in result):
                return jsonify({"result": result.get("data", result.get("results"))})
            else:
                return jsonify({"result": result})
        except ValueError:
            return jsonify({"result": r.text})
    except Exception as e:
        return jsonify({"error": f"API sorgusu başarısız: {str(e)}"})
    finally:
        log_query(session["user"], query, {"val1": val1, "val2": val2}, result_status)

@app.route("/api/sms-bomber", methods=["POST"])
@login_required
def sms_bomber():
    data = request.get_json()
    phone = data.get("phone")
    message = data.get("message", "Test mesajı")

    if not phone:
        return jsonify({"success": False, "error": "Telefon numarası gerekli"})

    sms_apis = load_sms_apis()
    results = []

    for api in sms_apis:
        try:
            url = api["url"].replace("{{phone}}", phone).replace("{{message}}", message)
            response = requests.get(url, timeout=10)
            results.append({
                "api": api["name"],
                "status": response.status_code,
                "success": response.status_code == 200
            })
        except Exception as e:
            results.append({
                "api": api["name"],
                "error": str(e),
                "success": False
            })

    success = any(result["success"] for result in results)
    return jsonify({"success": success, "results": results})

@app.route("/api/sms-apis", methods=["GET", "POST", "DELETE"])
@login_required
def manage_sms_apis():
    if request.method == "GET":
        apis = load_sms_apis()
        return jsonify(apis)

    elif request.method == "POST":
        data = request.get_json()
        name = data.get("name")
        url = data.get("url")

        if not name or not url:
            return jsonify({"success": False, "error": "Name and URL are required"})

        if "{{phone}}" not in url or "{{message}}" not in url:
            return jsonify({"success": False, "error": "URL must contain {{phone}} and {{message}} placeholders"})

        apis = load_sms_apis()
        apis.append({"name": name, "url": url})
        save_sms_apis(apis)

        return jsonify({"success": True})

    elif request.method == "DELETE":
        data = request.get_json()
        index = data.get("index")

        if index is None:
            return jsonify({"success": False, "error": "Index is required"})

        apis = load_sms_apis()
        if 0 <= index < len(apis):
            apis.pop(index)
            save_sms_apis(apis)
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Invalid index"})

@app.route("/api/query-logs")
@login_required
def get_query_logs():
    logs = load_query_logs()
    user_logs = [log for log in logs if log["username"] == session["user"]]
    return jsonify(user_logs[-50:])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
