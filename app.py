from flask import Flask, redirect, abort, jsonify
import requests
import urllib3
import time

# SSL uyarılarını gizle
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# Önbellek yapısı: { channel_slug: {'url': '...', 'time': 123456789} }
CACHE = {}
CACHE_DURATION = 120  # 2 dakika cache

def get_third_line_from_m3u(channel_slug):
    try:
        target_url = f"http://45.88.139.156/yt1/{channel_slug}.m3u8"
        
        # İstek atıyoruz (SSL doğrulaması kapalı, zaman aşımı 10 saniye)
        response = requests.get(target_url, verify=False, timeout=10)
        if response.status_code != 200:
            return None
            
        m3u_content = response.text
        lines = m3u_content.splitlines()
        
        # Boşlukları temizleyerek satırları liste yapalım (boş satırları hesaba katmak isteyebilirsin, 
        # ancak doğrudan 3. satır [indeks olarak 2] isteniyorsa şu şekilde alınır):
        # Python'da liste indeksleri 0'dan başlar, dolayısıyla 3. satır index 2'dir.
        if len(lines) >= 3:
            third_line = lines[2].strip()
            if third_line.startswith("http"):
                return third_line
                
        # Eğer 3. satır http ile başlamıyorsa veya dosya yeterince uzun değilse, 
        # alternatif olarak içerideki ilk http'yi aratmak istersen burayı açabilirsin:
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line.startswith("http"):
                return cleaned_line
                
    except Exception as e:
        print(f"M3U Okuma Hatası ({channel_slug}): {e}")
    
    return None

def get_third_line_from_m3u_other(channel_slug):
    try:
        target_url = f"http://45.88.139.140/yt1/{channel_slug}.m3u8"
        
        # İstek atıyoruz (SSL doğrulaması kapalı, zaman aşımı 10 saniye)
        response = requests.get(target_url, verify=False, timeout=10)
        if response.status_code != 200:
            return None
            
        m3u_content = response.text
        lines = m3u_content.splitlines()
        
        # Boşlukları temizleyerek satırları liste yapalım (boş satırları hesaba katmak isteyebilirsin, 
        # ancak doğrudan 3. satır [indeks olarak 2] isteniyorsa şu şekilde alınır):
        # Python'da liste indeksleri 0'dan başlar, dolayısıyla 3. satır index 2'dir.
        if len(lines) >= 3:
            third_line = lines[2].strip()
            if third_line.startswith("http"):
                return third_line
                
        # Eğer 3. satır http ile başlamıyorsa veya dosya yeterince uzun değilse, 
        # alternatif olarak içerideki ilk http'yi aratmak istersen burayı açabilirsin:
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line.startswith("http"):
                return cleaned_line
                
    except Exception as e:
        print(f"M3U Okuma Hatası ({channel_slug}): {e}")
    
    return None
    
@app.route('/yt1/<channel_slug>.m3u8')
def redirect_stream(channel_slug):
    current_time = time.time()
    
    # 1. Önbellek (Cache) Kontrolü
    if channel_slug in CACHE and (current_time - CACHE[channel_slug]['time'] < CACHE_DURATION):
        return redirect(CACHE[channel_slug]['url'], code=302)
        
    # 2. Kaynaktan güncel linki çek
    stream_url = get_third_line_from_m3u(channel_slug)
    
    if stream_url:
        # Başarılı olursa cache'e kaydet ve yönlendir
        CACHE[channel_slug] = {'url': stream_url, 'time': current_time}
        return redirect(stream_url, code=302)
    else:
        return abort(404, description="İçerik bulunamadı veya hedef sunucuya erişilemedi.")

@app.route('/yt2/<channel_slug>.m3u8')
def redirect_stream_other(channel_slug):
    current_time = time.time()
    
    # 1. Önbellek (Cache) Kontrolü
    if channel_slug in CACHE and (current_time - CACHE[channel_slug]['time'] < CACHE_DURATION):
        return redirect(CACHE[channel_slug]['url'], code=302)
        
    # 2. Kaynaktan güncel linki çek
    stream_url = get_third_line_from_m3u_other(channel_slug)
    
    if stream_url:
        # Başarılı olursa cache'e kaydet ve yönlendir
        CACHE[channel_slug] = {'url': stream_url, 'time': current_time}
        return redirect(stream_url, code=302)
    else:
        return abort(404, description="İçerik bulunamadı veya hedef sunucuya erişilemedi.")

@app.route('/restart')
def restart_cache():
    global CACHE
    CACHE.clear()  # Önbelleği sıfırlar
    return jsonify({
        "status": "success",
        "message": "Önbellek başarıyla temizlendi."
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
