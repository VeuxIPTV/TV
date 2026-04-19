import os
import subprocess
import glob
import sys
import signal

# ---------- НАСТРОЙКИ ----------
ffmpeg_path = r'C:\repo\ffmpeg.exe'
VIDEO_FILE  = r'C:\repo\Info.mp4'
OUTPUT_DIR  = r'C:\Репозиторий github\TV\HLS\hls_stream'
RESOLUTION  = (1024, 576)
FPS         = 30
SEGMENT_TIME = 2
# ------------------------------

def generate_playlist():
    """Создаёт index.m3u8 из существующих segment_*.ts."""
    os.chdir(OUTPUT_DIR)
    segments = sorted(glob.glob('segment_*.ts'))
    if not segments:
        print("⚠️ Нет сегментов для создания плейлиста.")
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
    print(f"✅ Плейлист создан: {len(segments)} сегментов.")
    return True

def convert_video():
    if not os.path.exists(VIDEO_FILE):
        print(f"❌ Видеофайл {VIDEO_FILE} не найден!")
        return False

    # Очищаем папку и создаём заново
    import shutil
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    os.chdir(OUTPUT_DIR)
    cmd = [
        ffmpeg_path,
        '-i', VIDEO_FILE,
        '-vf', f'scale={RESOLUTION[0]}:{RESOLUTION[1]}:force_original_aspect_ratio=decrease,pad={RESOLUTION[0]}:{RESOLUTION[1]}:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p',
        '-c:v', 'libx264', '-preset', 'fast', '-profile:v', 'baseline', '-level', '3.0',
        '-pix_fmt', 'yuv420p', '-g', str(FPS*SEGMENT_TIME), '-keyint_min', str(FPS*SEGMENT_TIME),
        '-sc_threshold', '0', '-c:a', 'aac', '-b:a', '128k', '-ar', '44100', '-ac', '2',
        '-f', 'hls', '-hls_time', str(SEGMENT_TIME), '-hls_list_size', '0',
        '-hls_playlist_type', 'vod', '-hls_segment_type', 'mpegts',
        '-hls_segment_filename', 'segment_%03d.ts', 'index.m3u8'
    ]

    print("🎬 Запуск конвертации. Это займёт время. Можно безопасно прервать Ctrl+C — плейлист восстановится.")
    process = None
    try:
        process = subprocess.Popen(cmd)
        process.wait()
        if process.returncode == 0:
            print("✅ Конвертация завершена успешно.")
        else:
            print(f"⚠️ FFmpeg завершился с кодом {process.returncode}. Проверьте ошибки выше.")
    except KeyboardInterrupt:
        print("\n⏹️ Конвертация прервана пользователем.")
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    finally:
        # В любом случае генерируем плейлист из существующих сегментов
        generate_playlist()

if __name__ == '__main__':
    convert_video()
    print(f"\n📁 Готовые файлы лежат в:\n{OUTPUT_DIR}")
    print("Теперь можно скопировать папку с сегментами и index.m3u8 в репозиторий для GitHub Pages.")