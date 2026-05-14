# tests/analyze_selfie.py
# Purpose: Run the AI Layer analysis on the real user-provided selfie.

import os
import requests
import time
import subprocess
from pathlib import Path

def run_analysis():
    print("=== SHADEMATE AI LAYER ANALYSIS: REAL SELFIE ===")
    
    # 1. Path to real selfie
    root = Path(__file__).parent.parent
    selfie_path = root / "assets" / "selfies" / "Papa.jpeg"
    
    if not selfie_path.exists():
        print(f"Error: Selfie not found at {selfie_path}")
        return

    # 2. Start Server
    print("Starting ShadeMate AI Layer...")
    env = os.environ.copy()
    env["VALID_API_KEYS"] = "test-key-001"
    env["API_KEY_DOMAINS"] = "test-key-001:*"
    
    server = subprocess.Popen(
        ["uv", "run", "uvicorn", "main:app", "--port", "8000", "--host", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=str(root)
    )
    
    # Give MediaPipe time to initialize
    time.sleep(8)
    
    try:
        # 3. Call /analyze
        print(f"Analyzing: {selfie_path.name}...")
        url = "http://127.0.0.1:8000/analyze"
        headers = {"Authorization": "Bearer test-key-001"}
        
        with open(selfie_path, 'rb') as img_file:
            files = {'image': (selfie_path.name, img_file, 'image/jpeg')}
            data = {'client_id': 'milind-internal-test'}
            response = requests.post(url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            result = response.json()
            print("\n[AI LAYER JSON RESPONSE]")
            print("-" * 50)
            # Print the key data we send to the client
            print(f"DETECTED SKIN: {result['detected_skin']['hex']} ({result['detected_skin']['undertone']})")
            print(f"LAB: {result['detected_skin']['lab']}")
            print("\nCOMPLEMENTARY VARIANTS (Sent to JS Widget):")
            for i, v in enumerate(result['complementary_range']['range']):
                print(f"  Variant {i+1}: {v['hex']} | Undertone: {v['undertone']} | Delta-E: {v['delta_e_from_primary']}")
            print("-" * 50)
            print("\nThis JSON is what Uvaish's JS Widget receives. The widget then")
            print("matches these variants against the client's local catalog.")
        else:
            print(f"Error! {response.status_code}: {response.text}")

    finally:
        server.terminate()
        print("\nServer shut down.")

if __name__ == "__main__":
    run_analysis()
