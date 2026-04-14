import os
import google.generativeai as genai
from dotenv import load_dotenv

# API Key load karo
load_dotenv()
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("🔍 Google API se puch rahe hain...\n")
print("✅ Tumhare liye available models ki list:")

# Google se saare models ki list maango
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"👉 {m.name}")
except Exception as e:
    print(f"❌ Error aaya: {e}")