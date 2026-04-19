import os
import subprocess
import glob
import sys

# ---------- НАСТРОЙКИ ----------
ffmpeg_path = r'C:\repo\ffmpeg.exe'
VIDEO_FILE  = r'C:\repo\Info.mp4'
OUTPUT_DIR  = r'C:\Репозиторий github\TV\HLS\hls_stream'
RESOLUTION  = (1024, 576)
FPS         = 30
SEGMENT_TIME = 2
# ------------------------------

def create_hls():
    if not os.path.exists(VIDEO_FILE):
        print(f"Ошибка: {VIDEO_FILE} не найден!")
        return False

    # Очищаем папку (ВНИМАНИЕ: удаляет все предыдущие файлы)
    if os.path.exists(OUTPUT_DIR):
        import shutil
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    os.chdir(OUTPUT_DIR)

    cmd = [
        ffmpeg_path,
        '-i', VIDEO_FILE,
        '-vf', f'scale={RESOLUTION[0]}:{RESOLUTION[1]}:force_original_aspect_ratio=decrease,pad={RESOLUTION[0]}:{RESOLUTION[1]}:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p',
        '-c:v', 'libx264',
        '-preset', 'fast',
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
        '-hls_list_size', '0',
        '-hls_playlist_type', 'vod',
        '-hls_segment_type', 'mpegts',
        '-hls_segment_filename', 'segment_%03d.ts',
        'index.m3u8'
    ]

    print("Начинается конвертация. Это займёт время. Пожалуйста, не прерывайте.")
    try:
        subprocess.run(cmd, check=True)
        print("✅ Конвертация успешно завершена!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка FFmpeg: {e}")
        return False

def fix_playlist():
    """На всякий случай проверим и пересоздадим плейлист."""
    os.chdir(OUTPUT_DIR)
    segments = sorted(glob.glob('segment_*.ts'))
    if not segments:
        print("❌ Сегменты не найдены.")
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
    print(f"✅ Плейлист обновлён ({len(segments)} сегментов).")
    return True

if __name__ == '__main__':
    if create_hls():
        fix_playlist()
        print(f"\n✅ ГОТОВО! Файлы сохранены в:\n{OUTPUT_DIR}")
        print("Теперь можно загрузить эту папку на GitHub.")
    else:
        print("\n⚠️ Конвертация не удалась. Проверьте пути и наличие ffmpeg.")