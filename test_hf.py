import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("HF_TOKEN")

if token:
    print("Hugging Face token loaded successfully!")
    print("Token starts with:", token[:3] + "...")
else:
    print("HF_TOKEN not found.")