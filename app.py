from flask import Flask, redirect, abort, jsonify, Response
import requests
import urllib3
import time

# SSL uyarılarını gizle
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# Önbellek yapısı
CACHE = {}
CACHE_DURATION = 120  # 2 dakika cache

def get_third_line_from_m3u(channel_slug):
    try:
        target_url = f"http://45.88.139.156/yt1/{channel_slug}.m3u8"
        response = requests.get(target_url, verify=False, timeout=10)
        if response.status_code != 200:
            return None
            
        m3u_content = response.text
        lines = m3u_content.splitlines()
        
        if len(lines) >= 3:
            third_line = lines[2].strip()
            if third_line.startswith("http"):
                return third_line
                
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line.startswith("http"):
                return cleaned_line
                
    except Exception as e:
        print(f"M3U Okuma Hatası ({channel_slug}): {e}")
    
    return None

def get_sunarproje_stream(channel_slug):
    try:
        target_url = f"https://raw.githubusercontent.com/sunarproje/yt/refs/heads/main/streams/{channel_slug}.m3u8"
        response = requests.get(target_url, verify=False, timeout=10)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"Sunarproje Okuma Hatası ({channel_slug}): {e}")
    
    return None
            
@app.route('/yt1/<channel_slug>.m3u8')
def redirect_stream_yt1(channel_slug):
    current_time = time.time()
    
    # 1. Önbellek (Cache) Kontrolü
    if channel_slug in CACHE and (current_time - CACHE[channel_slug].get('time', 0) < CACHE_DURATION):
        if 'url' in CACHE[channel_slug]:
            return redirect(CACHE[channel_slug]['url'], code=302)
        
    # 2. Kaynaktan güncel linki çek
    stream_url = get_third_line_from_m3u(channel_slug)
    
    if stream_url:
        CACHE[channel_slug] = {'url': stream_url, 'time': current_time}
        return redirect(stream_url, code=302)
    else:
        return abort(404, description="İçerik bulunamadı veya hedef sunucuya erişilemedi.")

@app.route('/sunarproje/<channel_slug>.m3u8')
def redirect_stream_sunarproje(channel_slug):
    current_time = time.time()
    
    # 1. Önbellek (Cache) Kontrolü
    if channel_slug in CACHE and (current_time - CACHE[channel_slug].get('time', 0) < CACHE_DURATION):
        if 'content' in CACHE[channel_slug]:
            return Response(CACHE[channel_slug]['content'], mimetype="application/vnd.apple.mpegurl")
        
    # 2. Kaynaktan güncel içeriği çek
    stream_content = get_sunarproje_stream(channel_slug)
    
    if stream_content:
        CACHE[channel_slug] = {'content': stream_content, 'time': current_time}
        return Response(stream_content, mimetype="application/vnd.apple.mpegurl")
    else:
        return abort(404, description="İçerik bulunamadı veya hedef sunucuya erişilemedi.")

@app.route('/restart')
def restart_cache():
    global CACHE
    CACHE.clear()
    return jsonify({
        "status": "success",
        "message": "Önbellek başarıyla temizlendi."
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
