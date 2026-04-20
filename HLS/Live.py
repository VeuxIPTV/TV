import os
import glob
import time
import threading
import http.server
import socketserver
import socket

# ---------- НАСТРОЙКИ ----------
HLS_DIR = r'C:\Репозиторий github\TV\HLS\hls_stream'   # папка с сегментами
PORT = 8080
UPDATE_INTERVAL = 5   # проверять новые сегменты каждые 5 секунд
# ------------------------------

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def generate_playlist():
    """Пересоздаёт index.m3u8 на основе всех имеющихся segment_*.ts."""
    os.chdir(HLS_DIR)
    segments = sorted(glob.glob('segment_*.ts'))
    if not segments:
        return
    with open('index.m3u8', 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        f.write('#EXT-X-VERSION:3\n')
        f.write('#EXT-X-TARGETDURATION:2\n')
        f.write('#EXT-X-MEDIA-SEQUENCE:0\n')
        f.write('#EXT-X-PLAYLIST-TYPE:EVENT\n')  
        for seg in segments:
            f.write('#EXTINF:2.0,\n')
            f.write(f'{seg}\n')
    print(f"[Плейлист] Обновлён ({len(segments)} сегментов)")

def playlist_updater():
    """Фоновый поток: периодически обновляет плейлист при появлении новых сегментов."""
    last_count = 0
    while True:
        time.sleep(UPDATE_INTERVAL)
        current_segments = glob.glob(os.path.join(HLS_DIR, 'segment_*.ts'))
        if len(current_segments) != last_count:
            generate_playlist()
            last_count = len(current_segments)

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HLS_DIR, **kwargs)

    def log_message(self, format, *args):
        
        pass

def start_server():
    updater = threading.Thread(target=playlist_updater, daemon=True)
    updater.start()

    generate_playlist()

    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        ip = get_local_ip()
        print("\n" + "="*60)
        print("🚀 LIVE HLS СЕРВЕР ЗАПУЩЕН")
        print(f"📺 Поток: http://{ip}:{PORT}/index.m3u8")
        print(f"🖥️  Тестовая страница: http://{ip}:{PORT}/index.html")
        print("="*60)
        print("Плейлист обновляется автоматически при появлении новых сегментов.")
        print("Нажмите Ctrl+C для остановки.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nСервер остановлен.")

if __name__ == '__main__':
    start_server()