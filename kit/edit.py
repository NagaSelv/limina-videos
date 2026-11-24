"""Build the Limina founder video: scenes -> concat -> narration + ducked music."""
import json, subprocess, os, sys
import numpy as np, soundfile as sf
from scipy.signal import resample_poly

V = '/home/claude/vid'
N = os.environ.get('N', 'x')   # puzzle number, e.g. N=30 python3 edit.py
SRC = f'{V}/in/today.mp4'
OUT = f'{V}/out'; os.makedirs(OUT, exist_ok=True); os.makedirs(f'{V}/scenes', exist_ok=True)
nar = json.load(open(f'{V}/nar/nar.json'))
ENC = ['-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', '30', '-an']
GAP = 0.35

def durs(seg): return [c[1] - c[0] for c in nar[seg]['caps']]

def place(seg, first_at, after_submit=None, anchors=None):
    """Return [(start, end, capfile, wavfile)] in scene time."""
    out = []; t = first_at
    for i, d in enumerate(durs(seg)):
        if anchors: t = max(t, anchors[i])
        if after_submit is not None and i == 1: t = max(t, after_submit)
        out.append((t, t + d, f'{V}/png/cap_{seg}_{i}.png', f'{V}/nar/{seg}_{i}.wav'))
        t = t + d + GAP
    return out

scenes = []   # dict(kind, dur, lines, ...)
# opening card
L = place('open', 0.5); scenes.append(dict(name='open', kind='card', png=f'{V}/png/open.png', dur=L[-1][1] + 0.8, lines=L, fadein=True))
# guesses: (seg, typing start, submit, footage available until, typing shown in seconds)
G = [('g1', 0.4, 2.6, 9.4, 2.2), ('g2', 9.4, 16.7, 43.4, 2.5), ('g3', 43.4, 57.6, 63.4, 3.0)]
for seg, a, sub, avail, tdur in G:
    L = place(seg, 0.3, after_submit=tdur + 0.4)
    dur = L[-1][1] + 0.7
    post = min(avail - sub, dur - tdur)
    scenes.append(dict(name=seg, kind='clip', pieces=[(a, sub, (sub - a) / tdur), (sub, sub + post, 1.0)], dur=dur, lines=L))
# thinking: hold the board before the last guess
L = place('think', 0.4); d = L[-1][1] + 0.6
scenes.append(dict(name='think', kind='clip', pieces=[(62.4, 63.4, 1.0)], dur=d, lines=L))
# solve: typing METAL (63.4-67.8) at 2x, then the win to the end of the recording
end_src = 72.45
L = place('solve', 2.2 + 0.35)
dur = max(2.2 + (end_src - 67.8), L[-1][1]) + 0.9
scenes.append(dict(name='solve', kind='clip', pieces=[(63.4, 67.8, 2.0), (67.8, end_src, 1.0)], dur=dur, lines=L))
L = place('close', 0.5); scenes.append(dict(name='close', kind='card', png=f'{V}/png/close.png', dur=L[-1][1] + 1.2, lines=L))

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: print(r.stderr[-3000:]); sys.exit(1)

def render(s):
    tmp = f'{V}/scenes/{s["name"]}.tmp.mp4'; final = f'{V}/scenes/{s["name"]}.mp4'
    D = round(s['dur'], 3)
    caps = [(l[0], l[1], l[2]) for l in s['lines']]
    inputs = []; fc = []
    if s['kind'] == 'card':
        inputs += ['-framerate', '30', '-i', s['png']]
        base = f'[0]format=yuv420p,loop=-1:1,trim=duration={D},setpts=PTS-STARTPTS'
        if s.get('fadein'): base += ',fade=in:st=0:d=0.5'
        fc.append(base + '[v0]')
        k = 1
    else:
        parts = []
        for i, (a, b, sp) in enumerate(s['pieces']):
            inputs += ['-ss', f'{a:.3f}', '-t', f'{b - a:.3f}', '-i', SRC]
            fc.append(f'[{i}:v]setpts=(PTS-STARTPTS)/{sp:.4f},fps=30,crop=1080:1920:0:270,'
                      f'setsar=1' + (',drawbox=x=0:y=734:w=1080:h=96:color=0x131820:t=fill' if a < 2.6 else '') + f',format=yuv420p[p{i}]')
            parts.append(f'[p{i}]')
        n = len(parts)
        fc.append(''.join(parts) + (f'concat=n={n}:v=1:a=0' if n > 1 else 'null') +
                  f',tpad=stop_mode=clone:stop_duration=30,trim=duration={D},setpts=PTS-STARTPTS[v0]')
        k = n
    cur = 'v0'; idx = k
    overlays = list(caps)
    if s.get('later'): overlays.append((s['later'][0], s['later'][1], f'{V}/png/later.png'))
    for j, (t0, t1, png) in enumerate(overlays):
        inputs += ['-i', png]
        nxt = f'v{j + 1}'
        fc.append(f'[{cur}][{idx}]overlay=0:0:enable=\'between(t,{t0:.3f},{t1 + 0.25:.3f})\'[{nxt}]')
        cur = nxt; idx += 1
    cmd = ['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(fc), '-map', f'[{cur}]',
           '-t', f'{D}'] + ENC + [tmp]
    run(cmd); os.replace(tmp, final)
    return final

only = sys.argv[1:]
t = 0.0; voice_events = []
for s in scenes:
    s['start'] = t
    for l in s['lines']: voice_events.append((t + l[0], l[3]))
    t += s['dur']
TOTAL = t
for s in scenes: print(f"{s['name']:6s} start {s['start']:6.2f} dur {s['dur']:5.2f}")
print('TOTAL', round(TOTAL, 2))

files = []
for s in scenes:
    f = f'{V}/scenes/{s["name"]}.mp4'
    if not only or s['name'] in only or not os.path.exists(f): render(s)
    files.append(f)
open(f'{V}/scenes/list.txt', 'w').write(''.join(f"file '{f}'\n" for f in files))
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{V}/scenes/list.txt', '-c', 'copy', f'{V}/scenes/video.mp4'])

# ---- audio: narration + music ducked under it
SR = 44100; n = int(TOTAL * SR) + SR
voice = np.zeros(n)
active = np.zeros(n)
for at, wav in voice_events:
    a, sr = sf.read(wav)
    a = resample_poly(a, 147, 80)  # 24k -> 44.1k
    i = int(at * SR); voice[i:i + len(a)] += a; active[i:i + len(a)] = 1
voice *= 0.89 / np.abs(voice).max()
m, sr = sf.read(f'{V}/music/calm.wav'); assert sr == SR
m = m[:n] if len(m) >= n else np.pad(m, ((0, n - len(m)), (0, 0)))
# ducking envelope: 1 when no voice, ~0.4 under voice; smooth 250 ms
k = int(0.25 * SR); env = np.convolve(active, np.ones(k) / k, 'same')
env = np.clip(env * 3, 0, 1)
gain = 0.48 * (1 - env) + 0.16 * env
fade = np.ones(n); fi = int(1.0 * SR); fo = int(3.0 * SR); end = int(TOTAL * SR)
fade[:fi] = np.linspace(0, 1, fi); fade[end - fo:end] = np.linspace(1, 0, fo); fade[end:] = 0
mix = m * (gain * fade)[:, None] + voice[:, None]
mix = mix[:end]
sf.write(f'{V}/scenes/mix.wav', mix.astype(np.float32), SR)
run(['ffmpeg', '-v', 'error', '-y', '-i', f'{V}/scenes/mix.wav', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '48000', f'{V}/scenes/mix_norm.wav'])
tmp = f'{OUT}/limina-founder-{N}.tmp.mp4'
run(['ffmpeg', '-v', 'error', '-y', '-i', f'{V}/scenes/video.mp4', '-i', f'{V}/scenes/mix_norm.wav', '-map', '0:v', '-map', '1:a',
     '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', tmp])
os.replace(tmp, f'{OUT}/limina-founder-{N}.mp4')
json.dump([{k: v for k, v in s.items() if k != 'lines'} | {'lines': [l[:3] for l in s['lines']]} for s in scenes],
          open(f'{V}/scenes/plan.json', 'w'), indent=1, default=str)
print('done')
