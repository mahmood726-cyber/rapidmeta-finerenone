import io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
print("PROGRESS 1 of 3")
time.sleep(4)
print("PROGRESS 2 of 3")
