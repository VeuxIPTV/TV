import os
import subprocess
import time
import glob
import threading
from flask import Flask, send_from_directory, render_template_string, abort

# ---------- НАСТРОЙКИ КАНАЛОВ ----------
CHANNELS = [
    {
        'name': 'SD',
        'video_file': r'C:\repo\Info.mp4',
        'ffmpeg_path': r'C:\repo\ffmpeg.exe',
        'hls_dir': r'C:\Репозиторий github\TV\HLS\hls_stream',
        'resolution': (1216, 678),
        'fps': 25,
        'port': 8080,
        'interlaced': False,
        'preset': 'ultrafast',
        'profile': 'baseline',
        'level': '3.0',
        'audio_bitrate': '128k',
        'ar': '44100'
    },
    {
        'name': '1080i50',
        'video_file': r'C:\repo\Info.mp4',
        'ffmpeg_path': r'C:\repo\ffmpeg.exe',
        'hls_dir': r'C:\Репозиторий github\TV\HLS\hls_stream_1080i',
        'resolution': (1920, 1080),
        'fps': 50,
        'port': 8081,
        'interlaced': True,
        'preset': 'ultrafast',
        'profile': 'high',
        'level': '4.0',
        'audio_bitrate': '192k',
        'ar': '48000'
    }
]

SEGMENT_TIME = 2
PLAYLIST_SIZE = 10
# ---------------------------------------

class HLSChannel:
    def __init__(self, config):
        self.config = config
        self.app = Flask(__name__)
        self.stream_process = None
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route('/')
        def index():
            stream_url = "/index.m3u8"
            html = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Live HLS {self.config['name']}</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ background: #111; color: #eee; font-family: Arial; padding: 20px; }}
                    .box {{ background: #222; padding: 20px; border-radius: 10px; max-width: 800px; margin: auto; }}
                    video {{ width: 100%; max-width: 640px; background: black; margin: 15px 0; }}
                    .status {{ padding: 5px 15px; border-radius: 20px; display: inline-block; }}
                    .ok {{ background: #4caf50; color: black; }}
                    .err {{ background: #f44336; }}
                    pre {{ background: #333; padding: 10px; overflow-x: auto; }}
                </style>
            </head>
            <body>
                <div class="box">
                    <h2>🎬 Live HLS {self.config['name']} ({self.config['resolution'][0]}x{self.config['resolution'][1]}@{self.config['fps']}fps)</h2>
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

                    function updateInfo() {{
                        fetch('/status')
                            .then(r => r.json())
                            .then(data => {{
                                infoPre.textContent = JSON.stringify(data, null, 2);
                                if (data.segments > 0) {{
                                    statusDiv.className = 'status ok';
                                    statusDiv.textContent = '🟢 Поток активен (' + data.segments + ' сегментов)';
                                }} else {{
                                    statusDiv.className = 'status err';
                                    statusDiv.textContent = '🔴 Сегменты не найдены';
                                }}
                            }})
                            .catch(e => {{
                                statusDiv.className = 'status err';
                                statusDiv.textContent = '❌ Ошибка получения статуса';
                            }});
                    }}

                    if (Hls.isSupported()) {{
                        const hls = new Hls({{ liveSyncDurationCount: 3, liveMaxLatencyDurationCount: 10 }});
                        hls.loadSource(streamUrl);
                        hls.attachMedia(video);
                        hls.on(Hls.Events.MANIFEST_PARSED, () => video.play().catch(() => {{}}));
                        hls.on(Hls.Events.ERROR, (event, data) => {{
                            if (data.fatal) {{
                                statusDiv.className = 'status err';
                                statusDiv.textContent = '❌ Ошибка HLS: ' + data.type;
                            }}
                        }});
                    }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                        video.src = streamUrl;
                        video.addEventListener('loadedmetadata', () => video.play());
                    }} else {{
                        statusDiv.className = 'status err';
                        statusDiv.textContent = '❌ Браузер не поддерживает HLS';
                    }}

                    function reloadPlayer() {{
                        video.load();
                        video.play();
                        updateInfo();
                    }}

                    setInterval(updateInfo, 3000);
                    updateInfo();
                </script>
            </body>
            </html>
            '''
            return render_template_string(html)

        @self.app.route('/index.m3u8')
        def serve_playlist():
            playlist = os.path.join(self.config['hls_dir'], 'index.m3u8')
            if not os.path.exists(playlist):
                abort(503, description="Плейлист ещё не создан. Подождите несколько секунд.")
            return send_from_directory(self.config['hls_dir'], 'index.m3u8', mimetype='application/vnd.apple.mpegurl')

        @self.app.route('/segment_<int:num>.ts')
        def serve_segment(num):
            filename = f'segment_{num:03d}.ts'
            return send_from_directory(self.config['hls_dir'], filename, mimetype='video/MP2T')

        @self.app.route('/status')
        def status():
            segments = glob.glob(os.path.join(self.config['hls_dir'], 'segment_*.ts'))
            return {
                "segments": len(segments),
                "playlist_exists": os.path.exists(os.path.join(self.config['hls_dir'], 'index.m3u8')),
                "ffmpeg_running": self.stream_process is not None and self.stream_process.poll() is None
            }

    def start_ffmpeg(self):
        cfg = self.config
        os.makedirs(cfg['hls_dir'], exist_ok=True)

        if self.stream_process and self.stream_process.poll() is None:
            self.stream_process.terminate()
            self.stream_process.wait()

        vf = f"scale={cfg['resolution'][0]}:{cfg['resolution'][1]}:force_original_aspect_ratio=decrease,pad={cfg['resolution'][0]}:{cfg['resolution'][1]}:(ow-iw)/2:(oh-ih)/2,fps={cfg['fps']},format=yuv420p"
        if cfg['interlaced']:
            vf += ',interlace=tff'

        cmd = [
            cfg['ffmpeg_path'],
            '-re', '-stream_loop', '-1',
            '-i', cfg['video_file'],
            '-vf', vf,
            '-c:v', 'libx264',
            '-preset', cfg['preset'],
            '-tune', 'zerolatency',
            '-profile:v', cfg['profile'],
            '-level', cfg['level'],
            '-pix_fmt', 'yuv420p',
            '-g', str(cfg['fps'] * SEGMENT_TIME),
            '-keyint_min', str(cfg['fps'] * SEGMENT_TIME),
            '-sc_threshold', '0',
            '-c:a', 'aac',
            '-b:a', cfg['audio_bitrate'],
            '-ar', cfg['ar'],
            '-ac', '2',
            '-f', 'hls',
            '-hls_time', str(SEGMENT_TIME),
            '-hls_list_size', str(PLAYLIST_SIZE),
            '-hls_flags', 'delete_segments+append_list+omit_endlist',
            '-hls_segment_type', 'mpegts',
            '-hls_segment_filename', os.path.join(cfg['hls_dir'], 'segment_%03d.ts'),
            os.path.join(cfg['hls_dir'], 'index.m3u8')
        ]

        if cfg['interlaced']:
            cmd.insert(cmd.index('-pix_fmt') + 2, '-flags')
            cmd.insert(cmd.index('-flags') + 1, '+ilme+ildct')
            cmd.insert(cmd.index('-flags') + 2, '-x264-params')
            cmd.insert(cmd.index('-x264-params') + 1, 'interlaced=1')

        self.stream_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[{cfg['name']}] FFmpeg запущен, порт {cfg['port']}")

    def monitor(self):
        while True:
            time.sleep(5)
            if self.stream_process and self.stream_process.poll() is not None:
                print(f"[{self.config['name']}] FFmpeg упал, перезапуск...")
                self.start_ffmpeg()

    def wait_for_segments(self):
        print(f"[{self.config['name']}] Ожидание сегментов...")
        for _ in range(30):
            if glob.glob(os.path.join(self.config['hls_dir'], 'segment_*.ts')):
                print(f"[{self.config['name']}] Готов!")
                return True
            time.sleep(1)
        print(f"[{self.config['name']}] Предупреждение: сегменты не появились.")
        return False

    def run(self):
        if not os.path.exists(self.config['video_file']):
            print(f"[{self.config['name']}] ❌ Видеофайл не найден: {self.config['video_file']}")
            return
        self.start_ffmpeg()
        threading.Thread(target=self.monitor, daemon=True).start()
        self.wait_for_segments()
        print(f"[{self.config['name']}] Сервер запущен на http://localhost:{self.config['port']}")
        self.app.run(host='0.0.0.0', port=self.config['port'], debug=False, threaded=True)

def main():
    print("=" * 70)
    print("🚀 ЗАПУСК МНОГОКАНАЛЬНОГО HLS СЕРВЕРА")
    print("=" * 70)

    threads = []
    for cfg in CHANNELS:
        channel = HLSChannel(cfg)
        t = threading.Thread(target=channel.run, daemon=False)
        t.start()
        threads.append(t)
        time.sleep(2)  # небольшая задержка между запусками

    print("\n✅ Все каналы запущены!")
    print("📺 SD канал:    http://localhost:8080/index.m3u8")
    print("📺 1080i канал: http://localhost:8081/index.m3u8")
    print("\nДля остановки нажмите Ctrl+C\n")

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n🛑 Остановка сервера...")

if __name__ == '__main__':
    main()