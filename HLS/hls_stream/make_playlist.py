import glob

segments = sorted(glob.glob('segment_*.ts'))
if not segments:
    print('Сегменты не найдены!')
    input('Нажмите Enter для выхода...')
    exit()

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

print(f'Создан index.m3u8 с {len(segments)} сегментами.')
input('Нажмите Enter для выхода...')