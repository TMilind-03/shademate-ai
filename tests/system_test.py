# tests/system_test.py
# END-TO-END SYSTEM TEST
# Purpose: Verify the entire pipeline with a real face and a real product catalog.

import json
import os
import math
import requests
import time
import subprocess
from pathlib import Path

def delta_e(lab1, lab2):
    """CIE76 Delta-E calculation."""
    return math.sqrt(
        (lab1["L"] - lab2["L"])**2 +
        (lab1["A"] - lab2["A"])**2 +
        (lab1["B"] - lab2["B"])**2
    )

def run_test():
    print("=== SHADEMATE END-TO-END SYSTEM TEST ===")
    
    # 1. Paths
    root = Path(__file__).parent.parent
    sample_face = root / ".venv" / "Lib" / "site-packages" / "matplotlib" / "mpl-data" / "sample_data" / "grace_hopper.jpg"
    catalog_path = root / "assets" / "catalog_processed.json"
    
    if not sample_face.exists():
        print(f"Error: Sample face {sample_face} not found.")
        return

    # 2. Start Server
    print("Starting FastAPI server...")
    env = os.environ.copy()
    env["VALID_API_KEYS"] = "test-key-999"
    env["API_KEY_DOMAINS"] = "test-key-999:*"
    
    server = subprocess.Popen(
        ["uv", "run", "uvicorn", "main:app", "--port", "8001", "--host", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=str(root)
    )
    
    time.sleep(10) # Give it time to load MediaPipe
    
    try:
        # 3. Call /analyze with Grace Hopper
        print(f"Sending real selfie ({sample_face.name}) to AI Layer...")
        url = "http://127.0.0.1:8001/analyze"
        headers = {"Authorization": "Bearer test-key-999"}
        
        with open(sample_face, 'rb') as img_file:
            files = {'image': (sample_face.name, img_file, 'image/jpeg')}
            data = {'client_id': 'system-test-001'}
            response = requests.post(url, headers=headers, files=files, data=data)

        if response.status_code != 200:
            print(f"Failed! Status: {response.status_code}")
            print(response.text)
            return

        result = response.json()
        detected_lab = result["detected_skin"]["lab"]
        undertone = result["detected_skin"]["undertone"]
        
        print(f"\n[AI RESULTS]")
        print(f"Detected Skin: {result['detected_skin']['hex']}")
        print(f"LAB: {detected_lab}")
        print(f"Undertone: {undertone}")

        # 4. Perform Matching against the Onboarded Catalog
        print(f"\nMatching against product catalog...")
        with open(catalog_path, 'r', encoding='utf-8') as f:
            catalog = json.load(f)

        matches = []
        for product in catalog:
            score = delta_e(detected_lab, product["lab"])
            match_percent = max(0, 100 - score)
            matches.append({
                "name": f"{product['brand']} - {product['shade']}",
                "score": round(match_percent, 2),
                "delta_e": round(score, 2)
            })

        # Sort by best match
        matches.sort(key=lambda x: x["delta_e"])

        print("\n[TOP RECOMMENDATIONS]")
        for i, m in enumerate(matches[:3]):
            print(f"{i+1}. {m['name']} | Match Score: {m['score']}% (Delta-E: {m['delta_e']})")

    finally:
        print("\nShutting down server...")
        server.terminate()

if __name__ == "__main__":
    run_test()
