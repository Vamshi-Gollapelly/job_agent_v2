import os
import sys

# Make the project root importable and keep tests away from the real database / API
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")
