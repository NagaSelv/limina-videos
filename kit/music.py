import numpy as np, soundfile as sf
SR=44100; BPM=72; beat=60/BPM; bar=4*beat; DUR=140.0
n=int(DUR*SR); L=np.zeros(n); R=np.zeros(n); rng=np.random.default_rng(7)
def hz(m): return 440*2**((m-69)/12)
# chords as midi notes (voicing around C4)
prog=[[53,57,60,64],[52,55,59,62],[50,53,57,60],[48,52,55,59]]   # Fmaj7 Em7 Dm7 Cmaj7
roots=[41,40,38,36]
def add(sig, start, pan=0.0, gain=1.0):
    i=int(start*SR)
    if i>=n: return
    j=min(n,i+len(sig)); s=sig[:j-i]*gain
    L[i:j]+=s*(1-pan)/1.0*0.5*2**0.5; R[i:j]+=s*(1+pan)/1.0*0.5*2**0.5
t_chord=2*bar
for c in range(int(DUR/t_chord)+1):
    t0=c*t_chord; ch=prog[c%4]; rt=roots[c%4]
    # pad
    d=t_chord+2.0; t=np.arange(int(d*SR))/SR
    env=np.minimum(1,t/1.8)*np.minimum(1,np.maximum(0,(d-t)/2.0))
    for k,m in enumerate(ch):
        f=hz(m)
        s=sum(np.sin(2*np.pi*f*(1+dt)*t+rng.random()*6) for dt in (-0.003,0,0.0035))/3
        add(s*env*0.06, t0, pan=(k-1.5)*0.3)
    # rhodes hits: beat 1 and beat 3-and of each bar
    for b in range(2):
        for off in (0, 2.5*beat):
            ts=t0+b*bar+off+0.02*rng.random()
            d=2.4; t=np.arange(int(d*SR))/SR
            env=np.exp(-t*2.2)*(1-np.exp(-t*200))
            trem=1+0.15*np.sin(2*np.pi*4.5*t)
            for k,m in enumerate(ch):
                f=hz(m+12 if k>1 else m)
                s=(np.sin(2*np.pi*f*t)+0.25*np.sin(4*np.pi*f*t)*np.exp(-t*5))
                add(s*env*trem*0.045*(0.8 if off else 1), ts+k*0.012, pan=(k-1.5)*0.25)
    # bass
    for b in range(2):
        for off,g in ((0,1),(2*beat,0.7)):
            d=1.6; t=np.arange(int(d*SR))/SR
            env=np.exp(-t*1.8)*(1-np.exp(-t*80))
            add(np.sin(2*np.pi*hz(rt)*t)*env*0.16*g, t0+b*bar+off)
# soft drums
nb=int(DUR/beat)
for i in range(nb):
    ts=i*beat
    if i%4 in (0,) or (i%8==6):
        d=0.4; t=np.arange(int(d*SR))/SR
        f=50+70*np.exp(-t*30); ph=2*np.pi*np.cumsum(f)/SR
        add(np.sin(ph)*np.exp(-t*9)*0.22, ts)
    if i%4==2:  # brushy snare
        d=0.3; t=np.arange(int(d*SR))/SR
        nz=rng.standard_normal(len(t)); nz=np.convolve(nz,np.ones(6)/6,'same')
        add(nz*np.exp(-t*14)*0.035, ts)
    for sub in (0.5,):  # off-beat hat (swung)
        d=0.08; t=np.arange(int(d*SR))/SR
        nz=rng.standard_normal(len(t)); nz=nz-np.convolve(nz,np.ones(4)/4,'same')
        add(nz*np.exp(-t*60)*0.02, ts+beat*0.58, pan=0.3)
# vinyl crackle + hiss
hiss=rng.standard_normal(n)*0.0025; hiss=np.convolve(hiss,np.ones(8)/8,'same')
L+=hiss; R+=hiss
for _ in range(int(DUR*6)):
    i=rng.integers(0,n-50); a=rng.random()*0.03
    L[i:i+20]+=a*np.exp(-np.arange(20)/4); R[i:i+20]+=a*np.exp(-np.arange(20)/4)*0.8
# gentle lowpass (one-pole) for warmth
def lp(x,fc=5000):
    a=np.exp(-2*np.pi*fc/SR); y=np.empty_like(x); s=0.0
    from scipy.signal import lfilter
    return lfilter([1-a],[1,-a],x)
L=lp(L); R=lp(R)
m=np.stack([L,R],1); m/=np.abs(m).max()/0.7
sf.write('/home/claude/vid/music/calm.wav', m.astype(np.float32), SR)
print('ok', m.shape[0]/SR)
