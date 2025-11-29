from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import os
import subprocess
import threading
import time
from datetime import datetime
import shutil

app = Flask(__name__)
app.secret_key = 'supersecretkey123'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

USER_DIR = "server"
PROJECTS_DIR = "projects"

# Kullanıcı session yönetimi
@app.before_request
def require_login():
    if request.endpoint not in ['login', 'do_login', 'register', 'do_register'] and 'username' not in session:
        return redirect(url_for('login'))

# Login işlemleri
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form.get('username')
    password = request.form.get('password')
    user_file = os.path.join(USER_DIR, f"{username}.txt")

    if os.path.exists(user_file):
        with open(user_file) as f:
            data = f.read()
            if f"password: {password}" in data:
                session['username'] = username
                flash("Başarıyla giriş yapıldı!", "success")
                return redirect(url_for('panel'))
    
    flash("Hatalı kullanıcı adı veya şifre!", "error")
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/do_register', methods=['POST'])
def do_register():
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')
    user_file = os.path.join(USER_DIR, f"{username}.txt")

    if os.path.exists(user_file):
        flash("Bu kullanıcı zaten kayıtlı!", "error")
        return render_template('register.html')
    
    with open(user_file, "w") as f:
        f.write(f"email: {email}\nusername: {username}\npassword: {password}")
    
    flash("Kayıt başarılı! Giriş yapabilirsiniz.", "success")
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Çıkış yapıldı!", "info")
    return redirect(url_for('login'))

# Panel ve proje yönetimi
@app.route('/panel')
def panel():
    username = session.get('username')
    user_projects_dir = os.path.join(PROJECTS_DIR, username)
    
    projects = []
    if os.path.exists(user_projects_dir):
        for project in os.listdir(user_projects_dir):
            project_path = os.path.join(user_projects_dir, project)
            if os.path.isdir(project_path):
                # Proje bilgilerini topla
                python_files = [f for f in os.listdir(project_path) if f.endswith('.py')]
                created_time = os.path.getctime(project_path)
                
                projects.append({
                    'name': project,
                    'created': datetime.fromtimestamp(created_time).strftime('%d.%m.%Y %H:%M'),
                    'python_files': python_files,
                    'file_count': len(python_files),
                    'is_running': is_process_running(username, project)
                })
    
    return render_template('panel.html', 
                         username=username, 
                         projects=projects,
                         active_tab=request.args.get('tab', 'projects'))

# Python dosyası yükleme
@app.route('/upload_python', methods=['POST'])
def upload_python():
    username = session.get('username')
    project_name = request.form.get('project_name')
    
    if 'python_files' not in request.files:
        flash("Dosya seçilmedi!", "error")
        return redirect(url_for('panel'))
    
    files = request.files.getlist('python_files')
    user_project_dir = os.path.join(PROJECTS_DIR, username, project_name)
    
    # Proje dizinini oluştur
    os.makedirs(user_project_dir, exist_ok=True)
    
    uploaded_files = []
    for file in files:
        if file.filename.endswith('.py'):
            file_path = os.path.join(user_project_dir, file.filename)
            file.save(file_path)
            uploaded_files.append(file.filename)
    
    if uploaded_files:
        flash(f"✅ {len(uploaded_files)} Python dosyası başarıyla yüklendi!", "success")
    else:
        flash("❌ Geçerli Python dosyası bulunamadı!", "error")
    
    return redirect(url_for('panel'))

# Proje çalıştırma
processes = {}

def is_process_running(username, project_name):
    return processes.get(f"{username}_{project_name}") is not None

@app.route('/run_project/<project_name>')
def run_project(project_name):
    username = session.get('username')
    project_key = f"{username}_{project_name}"
    user_project_dir = os.path.join(PROJECTS_DIR, username, project_name)
    
    if project_key in processes:
        flash("❌ Proje zaten çalışıyor!", "error")
        return redirect(url_for('panel'))
    
    # Python dosyalarını bul
    python_files = [f for f in os.listdir(user_project_dir) if f.endswith('.py')]
    
    if not python_files:
        flash("❌ Çalıştırılacak Python dosyası bulunamadı!", "error")
        return redirect(url_for('panel'))
    
    # Ana dosyayı bul (öncelik: main.py, app.py, bot.py)
    main_file = None
    for preferred in ['main.py', 'app.py', 'bot.py', 'run.py']:
        if preferred in python_files:
            main_file = preferred
            break
    
    if not main_file:
        main_file = python_files[0]  # İlk Python dosyasını kullan
    
    try:
        # Prosesi başlat
        process = subprocess.Popen(
            ['python', main_file],
            cwd=user_project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        processes[project_key] = {
            'process': process,
            'start_time': datetime.now(),
            'log': []
        }
        
        # Logları topla (thread ile)
        def collect_logs():
            while process.poll() is None:
                output = process.stdout.readline()
                if output:
                    processes[project_key]['log'].append({
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'message': output.strip()
                    })
                time.sleep(0.1)
        
        thread = threading.Thread(target=collect_logs)
        thread.daemon = True
        thread.start()
        
        flash(f"✅ {project_name} başlatıldı!", "success")
        
    except Exception as e:
        flash(f"❌ Hata: {str(e)}", "error")
    
    return redirect(url_for('panel'))

# Proje durdurma
@app.route('/stop_project/<project_name>')
def stop_project(project_name):
    username = session.get('username')
    project_key = f"{username}_{project_name}"
    
    if project_key in processes:
        processes[project_key]['process'].terminate()
        processes.pop(project_key)
        flash(f"✅ {project_name} durduruldu!", "success")
    else:
        flash("❌ Proje zaten çalışmıyor!", "error")
    
    return redirect(url_for('panel'))

# Logları getir
@app.route('/get_logs/<project_name>')
def get_logs(project_name):
    username = session.get('username')
    project_key = f"{username}_{project_name}"
    
    if project_key in processes:
        return jsonify({'logs': processes[project_key]['log']})
    else:
        return jsonify({'logs': []})

# Proje silme
@app.route('/delete_project/<project_name>')
def delete_project(project_name):
    username = session.get('username')
    project_key = f"{username}_{project_name}"
    user_project_dir = os.path.join(PROJECTS_DIR, username, project_name)
    
    # Çalışıyorsa durdur
    if project_key in processes:
        processes[project_key]['process'].terminate()
        processes.pop(project_key)
    
    # Dizini sil
    if os.path.exists(user_project_dir):
        shutil.rmtree(user_project_dir)
        flash("✅ Proje silindi!", "success")
    else:
        flash("❌ Proje bulunamadı!", "error")
    
    return redirect(url_for('panel'))

if __name__ == '__main__':
    if not os.path.exists(USER_DIR):
        os.makedirs(USER_DIR)
    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)
    
    print("🚀 Vision Bot Panel Başlatılıyor...")
    app.run(host='0.0.0.0', port=5000, debug=True)
