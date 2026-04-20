import subprocess
import os

VIDEO_FILE = r'C:\Репозиторий github\TV\HLS\Info.mp4'
OUTPUT_DIR = r'C:\Репозиторий github\TV\HLS\hls_vod'
FFMPEG_PATH = r'C:\Репозиторий github\TV\HLS\ffmpeg.exe'
RESOLUTION = (1024, 576)
FPS = 25
SEGMENT_TIME = 2

os.makedirs(OUTPUT_DIR, exist_ok=True)

cmd = [
    FFMPEG_PATH,
    '-i', VIDEO_FILE,
    '-vf', f'scale={RESOLUTION[0]}:{RESOLUTION[1]}:force_original_aspect_ratio=decrease,pad={RESOLUTION[0]}:{RESOLUTION[1]}:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p',
    '-c:v', 'libx264',
    '-preset', 'fast',          # качественнее, но один раз
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
    '-hls_list_size', '0',      # все сегменты в плейлисте
    '-hls_playlist_type', 'vod',
    '-hls_segment_type', 'mpegts',
    '-hls_segment_filename', os.path.join(OUTPUT_DIR, 'segment_%03d.ts'),
    os.path.join(OUTPUT_DIR, 'index.m3u8')
]

print("Начинается однократная конвертация. Это займёт время, но потом будет идеально.")
subprocess.run(cmd, check=True)
print(f"Готово! HLS-файлы сохранены в {OUTPUT_DIR}")