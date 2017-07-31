import sys
import os

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(base, "src")
sys.path.insert(0, src)
