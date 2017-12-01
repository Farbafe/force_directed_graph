import subprocess
import os
import sys

maxIterations = 2
process = subprocess.call(["python", os.path.join(sys.path[0], "Source.py")] + (sys.argv[1:]))

for i in range(maxIterations):
    print(i)
    parameter = "continue" if i != maxIterations - 1 else "end"
    process = subprocess.call(["python", os.path.join(sys.path[0], "Source.py")] + (sys.argv[1:] + [parameter]))
    if process != 0:
        sys.exit(1)
