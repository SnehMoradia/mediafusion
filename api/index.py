import os
import sys

# Ensure current root directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Handler entry point for Vercel Serverless Functions
app = app
