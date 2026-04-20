import os
import subprocess
import time
import glob
import threading
from flask import Flask, send_from_directory, render_template_string, abort

# ---------- НАСТРОЙКИ СТАБИЛЬНОГО SD КАНАЛА ----------
VIDEO_FILE = r'C:\repo\Info.mp4'
FFMPEG_PATH = r'C:\repo\ffmpeg.exe'
HLS_DIR = r'C:\Репозиторий github\TV\HLS\hls_stream'
RESOLUTION = (1216, 678)
FPS = 25                       # Стандарт PAL – 25 кадров/с
SEGMENT_TIME = 2
PLAYLIST_SIZE = 10
PORT = 8080
# ------------------------------------------------------

app = Flask(__name__)
stream_process = None

def start_ffmpeg_stream():
    global stream_process
    os.makedirs(HLS_DIR, exist_ok=True)

    if stream_process and stream_process.poll() is None:
        stream_process.terminate()
        stream_process.wait()

    cmd = [
        FFMPEG_PATH,
        '-re',
        '-stream_loop', '-1',
        '-i', VIDEO_FILE,
        '-vf', f'scale={RESOLUTION[0]}:{RESOLUTION[1]}:force_original_aspect_ratio=decrease,pad={RESOLUTION[0]}:{RESOLUTION[1]}:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-profile:v', 'baseline',
        '-level', '3.0',
        '-pix_fmt', 'yuv420p',
        '-g', str(FPS * SEGMENT_TIME),
        '-keyint_min', str(FPS * SEGMENT_TIME),
        '-sc_threshold', '0',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-ar', '44100',
        '-ac', '2',
        '-f', 'hls',
        '-hls_time', str(SEGMENT_TIME),
        '-hls_list_size', str(PLAYLIST_SIZE),
        '-hls_flags', 'delete_segments+append_list+omit_endlist',
        '-hls_segment_type', 'mpegts',
        '-hls_segment_filename', os.path.join(HLS_DIR, 'segment_%03d.ts'),
        os.path.join(HLS_DIR, 'index.m3u8')
    ]

    stream_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[STREAM] FFmpeg запущен, сегменты в {HLS_DIR}")

@app.route('/')
def index():
    stream_url = "/index.m3u8"
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Stable HLS 576p25</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { background: #111; color: #eee; font-family: Arial; padding: 20px; }
            .box { background: #222; padding: 20px; border-radius: 10px; max-width: 800px; margin: auto; }
            video { width: 100%; max-width: 640px; background: black; margin: 15px 0; }
            .status { padding: 5px 15px; border-radius: 20px; display: inline-block; }
            .ok { background: #4caf50; color: black; }
            .err { background: #f44336; }
            pre { background: #333; padding: 10px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>🎬 Стабильный HLS 576p @25fps</h2>
            <p>Статус: <span id="status" class="status">Проверка...</span></p>
            <video id="player" controls autoplay muted></video>
            <button onclick="reloadPlayer()">🔄 Перезапустить плеер</button>
            <hr>
            <h3>📋 Диагностика</h3>
            <pre id="info">Загрузка...</pre>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
        <script>
            const streamUrl = '/index.m3u8';
            const video = document.getElementById('player');
            const statusDiv = document.getElementById('status');
            const infoPre = document.getElementById('info');

            function updateInfo() {
                fetch('/status')
                    .then(r => r.json())
                    .then(data => {
                        infoPre.textContent = JSON.stringify(data, null, 2);
                        if (data.segments > 0) {
                            statusDiv.className = 'status ok';
                            statusDiv.textContent = '🟢 Поток активен (' + data.segments + ' сегментов)';
                        } else {
                            statusDiv.className = 'status err';
                            statusDiv.textContent = '🔴 Сегменты не найдены';
                        }
                    })
                    .catch(e => {
                        statusDiv.className = 'status err';
                        statusDiv.textContent = '❌ Ошибка получения статуса';
                    });
            }

            if (Hls.isSupported()) {
                const hls = new Hls({ liveSyncDurationCount: 3, liveMaxLatencyDurationCount: 10 });
                hls.loadSource(streamUrl);
                hls.attachMedia(video);
                hls.on(Hls.Events.MANIFEST_PARSED, () => video.play().catch(() => {}));
                hls.on(Hls.Events.ERROR, (event, data) => {
                    if (data.fatal) {
                        statusDiv.className = 'status err';
                        statusDiv.textContent = '❌ Ошибка HLS: ' + data.type;
                    }
                });
            } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
                video.src = streamUrl;
                video.addEventListener('loadedmetadata', () => video.play());
            } else {
                statusDiv.className = 'status err';
                statusDiv.textContent = '❌ Браузер не поддерживает HLS';
            }

            function reloadPlayer() {
                video.load();
                video.play();
                updateInfo();
            }

            setInterval(updateInfo, 3000);
            updateInfo();
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/index.m3u8')
def serve_playlist():
    if not os.path.exists(os.path.join(HLS_DIR, 'index.m3u8')):
        abort(503, description="Плейлист ещё не создан. Подождите несколько секунд.")
    return send_from_directory(HLS_DIR, 'index.m3u8', mimetype='application/vnd.apple.mpegurl')

@app.route('/segment_<int:num>.ts')
def serve_segment(num):
    filename = f'segment_{num:03d}.ts'
    return send_from_directory(HLS_DIR, filename, mimetype='video/MP2T')

@app.route('/status')
def status():
    segments = glob.glob(os.path.join(HLS_DIR, 'segment_*.ts'))
    return {
        "segments": len(segments),
        "playlist_exists": os.path.exists(os.path.join(HLS_DIR, 'index.m3u8')),
        "ffmpeg_running": stream_process is not None and stream_process.poll() is None
    }

def monitor_ffmpeg():
    while True:
        time.sleep(5)
        if stream_process and stream_process.poll() is not None:
            print("[MONITOR] FFmpeg упал, перезапуск...")
            start_ffmpeg_stream()

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ЗАПУСК СТАБИЛЬНОГО HLS 576p25")
    print(f"📁 Папка сегментов: {HLS_DIR}")
    print(f"🌐 Порт: {PORT}")
    print("=" * 60)

    if not os.path.exists(VIDEO_FILE):
        print(f"❌ Видеофайл не найден: {VIDEO_FILE}")
        exit(1)

    start_ffmpeg_stream()
    threading.Thread(target=monitor_ffmpeg, daemon=True).start()

    print("[WAIT] Ожидание первого сегмента...")
    for _ in range(30):
        if glob.glob(os.path.join(HLS_DIR, 'segment_*.ts')):
            print("[WAIT] Сегменты появились, сервер готов!")
            break
        time.sleep(1)

    print(f"\n🌐 Откройте в браузере: http://localhost:{PORT}")
    print(f"📺 Прямая ссылка для плеера: http://localhost:{PORT}/index.m3u8")
    print("Нажмите Ctrl+C для остановки.\n")

    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)