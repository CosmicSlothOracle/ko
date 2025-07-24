# 🚀 Deployment Checklist - KOSGE Backend

## 🔒 **SICHERHEITSKONFIGURATION**

### **1. Umgebungsvariablen setzen**
```bash
# Admin-Authentifizierung
export ADMIN_USERNAME=your_secure_admin_username
export ADMIN_PASSWORD_HASH=your_bcrypt_password_hash

# Sicherheit
export SECRET_KEY=your_very_secure_random_secret_key
export FLASK_ENV=production

# CORS-Konfiguration
export CORS_ORIGINS=https://your-frontend-domain.com,https://another-domain.com

# Datei-Upload-Limits
export MAX_CONTENT_LENGTH=16777216  # 16MB in Bytes

# Logging
export LOG_LEVEL=INFO
```

### **2. Bcrypt-Passwort generieren**
```python
import bcrypt

password = "your_secure_password"
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(f"Password hash: {password_hash}")
```

### **3. Secret Key generieren**
```python
import secrets
secret_key = secrets.token_hex(32)
print(f"Secret key: {secret_key}")
```

## 📁 **DATEISYSTEM-BERECHTIGUNGEN**

### **1. Upload-Verzeichnis**
```bash
# Verzeichnis erstellen
mkdir -p uploads
chmod 755 uploads
chown www-data:www-data uploads  # Für Apache/Nginx
```

### **2. Content-Verzeichnis**
```bash
# Verzeichnis erstellen
mkdir -p content
chmod 755 content
chown www-data:www-data content
```

### **3. Participants-Datei**
```bash
# Datei erstellen falls nicht vorhanden
touch participants.json
chmod 644 participants.json
chown www-data:www-data participants.json
```

## 🌐 **CORS-KONFIGURATION**

### **1. Erlaubte Domains**
```python
# In config.py oder über Umgebungsvariablen
CORS_ORIGINS = [
    "https://kosge.netlify.app",
    "https://kosge.onrender.com",
    "https://your-production-domain.com"
]
```

### **2. Lokale Entwicklung**
```python
# Für lokale Entwicklung
CORS_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8000"
]
```

## 📊 **MONITORING & LOGGING**

### **1. Logging-Konfiguration**
```python
# In app.py
import logging
from logging.handlers import RotatingFileHandler

# Datei-Logging für Produktion
if not app.debug:
    file_handler = RotatingFileHandler('logs/kosge.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('KOSGE startup')
```

### **2. Health Check Monitoring**
```bash
# Cron-Job für Health Check
*/5 * * * * curl -f https://your-api-domain.com/api/health || echo "API down" | mail -s "KOSGE API Alert" admin@example.com
```

## 🔧 **PERFORMANCE-OPTIMIERUNG**

### **1. Gunicorn-Konfiguration**
```python
# gunicorn.conf.py
bind = "0.0.0.0:10000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
preload_app = True
```

### **2. Nginx-Konfiguration (falls verwendet)**
```nginx
server {
    listen 80;
    server_name your-api-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:10000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Statische Dateien
    location /api/uploads/ {
        alias /path/to/your/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

## 🧪 **TESTING**

### **1. Vor Deployment**
```bash
# Tests ausführen
python3 test_backend.py

# Health Check
curl https://your-api-domain.com/api/health

# API-Endpunkte testen
curl -X POST https://your-api-domain.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'
```

### **2. Post-Deployment Tests**
```bash
# Alle Endpunkte testen
./test_all_endpoints.sh

# Load Testing (optional)
ab -n 1000 -c 10 https://your-api-domain.com/api/health
```

## 📋 **DEPLOYMENT-CHECKLISTE**

### **Vor Deployment:**
- [ ] Alle Umgebungsvariablen gesetzt
- [ ] Passwort-Hash generiert und gesetzt
- [ ] Secret Key generiert und gesetzt
- [ ] CORS-Origins konfiguriert
- [ ] Dateisystem-Berechtigungen korrekt
- [ ] Tests erfolgreich durchgeführt
- [ ] Logging-Verzeichnis erstellt

### **Nach Deployment:**
- [ ] Health Check erfolgreich
- [ ] Login-Endpunkt funktioniert
- [ ] File-Upload funktioniert
- [ ] CMS-Endpunkte funktionieren
- [ ] CORS funktioniert vom Frontend
- [ ] Logs werden geschrieben
- [ ] Monitoring-Alerts konfiguriert

### **Sicherheits-Check:**
- [ ] Standard-Credentials geändert
- [ ] HTTPS aktiviert
- [ ] Firewall konfiguriert
- [ ] Rate Limiting aktiviert (empfohlen)
- [ ] Backup-Strategie implementiert
- [ ] SSL-Zertifikat gültig

## 🚨 **NOTFALL-PROZEDUREN**

### **1. API-Down**
```bash
# Logs überprüfen
tail -f logs/kosge.log

# Service neu starten
sudo systemctl restart kosge-backend

# Health Check
curl https://your-api-domain.com/api/health
```

### **2. Datenverlust**
```bash
# Backup wiederherstellen
cp backup/participants.json participants.json
cp -r backup/uploads/ uploads/

# Berechtigungen setzen
chown www-data:www-data participants.json uploads/
```

### **3. Sicherheitsvorfall**
```bash
# Logs sichern
cp logs/kosge.log logs/kosge.log.$(date +%Y%m%d_%H%M%S)

# Service stoppen
sudo systemctl stop kosge-backend

# Passwort ändern
# Neue Umgebungsvariablen setzen
# Service neu starten
```

## 📞 **KONTAKTE**

- **Entwickler:** [Ihr Name]
- **System-Admin:** [Admin Name]
- **Notfall:** [Notfall-Nummer]

## 📝 **NOTIZEN**

- Backup-Strategie: Tägliche Backups der `participants.json` und `uploads/`
- Monitoring: Health Check alle 5 Minuten
- Updates: Monatliche Sicherheits-Updates
- Logs: 30 Tage Aufbewahrung