import glob, io, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jscheck
files = sorted(glob.glob("*_FULL_REVIEW.html"))
ok = bad = 0
broken = []
t0 = time.time()
for i, f in enumerate(files, 1):
    probs = jscheck.check(f)
    if probs:
        bad += 1
        broken.append((f, probs[0]))
        print(f"  [JS-BROKEN] {f}: block#{probs[0][0]} {probs[0][1][:120]}", flush=True)
    else:
        ok += 1
    if i % 100 == 0:
        print(f"  ...{i}/{len(files)} ({time.time()-t0:.0f}s)  ok={ok} bad={bad}", flush=True)
print(f"\n=== jscheck: {ok} JS-OK, {bad} JS-BROKEN (of {len(files)}) in {time.time()-t0:.0f}s ===")
if broken:
    io.open("outputs/_jscheck_broken.log", "w", encoding="utf-8").write(
        "\n".join(f"{f}\t{p}" for f, p in broken))
    print("broken logged -> outputs/_jscheck_broken.log")
sys.exit(1 if bad else 0)
