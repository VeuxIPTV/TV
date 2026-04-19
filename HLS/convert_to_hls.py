import os
import subprocess
import socket
import glob
import sys

# ---------- НАСТРОЙКИ ----------
ffmpeg_path = r'C:\repo\ffmpeg.exe'
VIDEO_FILE  = r'C:\repo\Info.mp4'
OUTPUT_DIR  = r'C:\repo\hls_stream'
RESOLUTION  = (1024, 576)
FPS         = 30
SEGMENT_TIME = 2
PORT        = 8080
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
    os.chdir(OUTPUT_DIR)
    segments = sorted(glob.glob('segment_*.ts'))
    if not segments:
        print("Сегменты не найдены!")
        return False
    with open('index.m3u8', 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        f.write('#EXT-X-VERSION:3\n')
        f.write('#EXT-X-TARGETDURATION:2\n')
        f.write('#EXT-X-MEDIA-SEQUENCE:0\n')
        f.write('#EXT-X-PLAYLIST-TYPE:VOD\n')
        for seg in segments:
            f.write('#EXTINF:2.0,\n')
            f.write(f'{seg}\n')
        f.write('#EXT-X-ENDLIST\n')
    print(f'Плейлист создан: {len(segments)} сегментов.')
    return True

def convert_video():
    if not os.path.exists(VIDEO_FILE):
        print(f"Видео {VIDEO_FILE} не найдено!")
        return False
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.chdir(OUTPUT_DIR)
    if glob.glob('segment_*.ts'):
        print("Сегменты уже есть, конвертация пропущена.")
        return True
    print("Конвертация видео в HLS... (не нажимайте Ctrl+C)")
    cmd = [
        ffmpeg_path, '-i', VIDEO_FILE,
        '-vf', f'scale={RESOLUTION[0]}:{RESOLUTION[1]}:force_original_aspect_ratio=decrease,pad={RESOLUTION[0]}:{RESOLUTION[1]}:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p',
        '-c:v', 'libx264', '-preset', 'fast', '-profile:v', 'baseline', '-level', '3.0',
        '-pix_fmt', 'yuv420p', '-g', str(FPS*SEGMENT_TIME), '-keyint_min', str(FPS*SEGMENT_TIME),
        '-sc_threshold', '0', '-c:a', 'aac', '-b:a', '128k', '-ar', '44100', '-ac', '2',
        '-f', 'hls', '-hls_time', str(SEGMENT_TIME), '-hls_list_size', '0',
        '-hls_playlist_type', 'vod', '-hls_segment_type', 'mpegts',
        '-hls_segment_filename', 'segment_%03d.ts', 'index.m3u8'
    ]
    try:
        subprocess.run(cmd, check=True)
        print("Конвертация завершена.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка конвертации: {e}")
        return False
    except KeyboardInterrupt:
        print("\nКонвертация прервана. Используем существующие сегменты...")
        return True  # продолжаем, т.к. сегменты могли успеть создаться

def start_server():
    os.chdir(OUTPUT_DIR)
    import http.server, socketserver
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        ip = get_local_ip()
        print("\n" + "="*60)
        print("✅ ПОТОК ГОТОВ!")
        print(f"Локально: http://localhost:{PORT}/index.m3u8")
        print(f"В сети:   http://{ip}:{PORT}/index.m3u8")
        print("="*60)
        print("Вставьте ссылку в VLC. Включите Loop для повтора.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nСервер остановлен.")

if __name__ == '__main__':
    if not convert_video():
        if not glob.glob(os.path.join(OUTPUT_DIR, 'segment_*.ts')):
            sys.exit(1)
    if not os.path.exists(os.path.join(OUTPUT_DIR, 'index.m3u8')):
        generate_playlist()
    start_server()