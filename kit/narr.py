import json, soundfile as sf, numpy as np
from kokoro_onnx import Kokoro
# each segment: list of (caption text, spoken text)
SEG = {
 "open": [("I'm the founder of Limina, a daily word puzzle.", "I'm the founder of Limina, a daily word puzzle."),
          ("Here's how I solved Monday's, number 29.", "Here's how I solved Monday's, number twenty nine.")],
 "g1":   [("I start with REACT.", "I start with react."),
          ("Two green clues and one orange.", "Two green clues, and one orange."),
          ("E comes before T and A, and orange says T comes before A.", "E comes before T, and A. And orange says T comes before A."),
          ("So the order so far is E, T, A. R and C are out.", "So the order so far is E, T, A. R and C are out.")],
 "g2":   [("Next, THING, to try some new letters.", "Next, thing, to try some new letters."),
          ("No pairs at all.", "No pairs at all."),
          ("T is in the word, so H, I, N and G must be out.", "T is in the word, so H, I, N, and G, must be out.")],
 "g3":   [("Third guess, DAMPS.", "Third guess, damps."),
          ("One orange clue: A and M.", "One orange clue. A, and M."),
          ("So M comes before A. D, P and S are out.", "So M comes before A. D, P, and S, are out.")],
 "think":[("Four letters now: E, T, A and M. I need one more.", "Four letters now. E, T, A, and M. I need one more."),
          ("L hasn't been ruled out, and one word fits every clue.", "L hasn't been ruled out. And one word fits every clue.")],
 "solve":[("METAL! Solved in four guesses.", "Metal! Solved in four guesses.")],
 "close":[("Limina is free, with a new puzzle every day.", "Limina is free, with a new puzzle every day."),
          ("Play at liminawordgame.com, and tell me how you got on.", "Play at limina word game dot com. And tell me how you got on.")],
}
k=Kokoro('/home/claude/vid/tts/kokoro-v1.0.onnx','/home/claude/vid/tts/voices-v1.0.bin')
SR=24000; GAP=0.35; out={}
for name, lines in SEG.items():
    parts=[]; caps=[]; t=0.0
    for cap, say in lines:
        a,sr=k.create(say, voice='bm_george', speed=0.92, lang='en-gb'); assert sr==SR
        # trim leading/trailing near-silence
        nz=np.where(np.abs(a)>0.01)[0]; a=a[max(nz[0]-240,0):nz[-1]+480]
        caps.append([round(t,3), round(t+len(a)/SR,3), cap]); sf.write(f'/home/claude/vid/nar/{name}_{len(caps)-1}.wav', a, SR); parts.append(a); t+=len(a)/SR
        parts.append(np.zeros(int(GAP*SR),np.float32)); t+=GAP
    w=np.concatenate(parts[:-1]); sf.write(f'/home/claude/vid/nar/{name}.wav', w, SR)
    out[name]={'dur':round(len(w)/SR,3),'caps':caps}; print(name, out[name]['dur'])
json.dump(out, open('/home/claude/vid/nar/nar.json','w'), indent=1)
print('total', sum(v['dur'] for v in out.values()))
