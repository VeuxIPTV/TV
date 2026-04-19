import os
import subprocess

VIDEO_FILE = 'Info.mp4'   
OUTPUT_DIR = 'hls_stream'     
RESOLUTION = (1024, 576)
FPS = 30
SEGMENT_TIME = 2              # секунд на сегмент

def create_loopable_hls():
    if not os.path.exists(VIDEO_FILE):
        print(f"Ошибка: {VIDEO_FILE} не найден!")
        return

    if os.path.exists(OUTPUT_DIR):
        import shutil
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

   
    cmd = [
        'ffmpeg.exe',
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
        '-hls_list_size', '0',                # все сегменты в плейлисте
        '-hls_playlist_type', 'vod',          # обычный VOD, но мы добавим loop в плеере
        '-hls_segment_type', 'mpegts',
        '-hls_segment_filename', os.path.join(OUTPUT_DIR, 'segment_%03d.ts'),
        os.path.join(OUTPUT_DIR, 'index.m3u8')
    ]
    subprocess.run(cmd, check=True)
    print(f"Готово! HLS-файлы сохранены в папке '{OUTPUT_DIR}'.")

if __name__ == '__main__':
    create_loopable_hls()
