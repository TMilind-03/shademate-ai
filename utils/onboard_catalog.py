# utils/onboard_catalog.py
# INTERNAL USE ONLY — For ShadeMate Team (Milind/Sujal)
# Purpose: Take a simple CSV of HEX codes and generate the high-precision LAB catalog.

import csv
import json
import os
import sys

# Add project root to path so we can import our utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.color_utils import rgb_to_lab, detect_undertone

def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Convert #RRGGBB to (R, G, B)."""
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def process_catalog(input_csv: str, output_json: str):
    print(f"--- Onboarding Catalog: {input_csv} ---")
    processed_data = []
    
    if not os.path.exists(input_csv):
        print(f"Error: {input_csv} not found.")
        return

    with open(input_csv, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # 1. Extract RGB from HEX
                r, g, b = hex_to_rgb(row['hex'])
                
                # 2. Convert to LAB using our core utility
                lab = rgb_to_lab(r, g, b)
                
                # 3. Detect Undertone
                undertone = detect_undertone(lab)
                
                # 4. Build enriched record
                item = {
                    "product_id": row['product_id'],
                    "brand": row['brand'],
                    "name": row['name'],
                    "shade": row['shade'],
                    "hex": row['hex'],
                    "lab": lab,
                    "undertone": undertone
                }
                processed_data.append(item)
                print(f"[OK] Processed: {row['shade']} ({undertone})")
                
            except Exception as e:
                print(f"[ERROR] Failed to process {row.get('shade', 'unknown')}: {e}")

    # Save to JSON for the JS Widget / Frontend to consume
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=2)
    
    print(f"\nSUCCESS: Processed {len(processed_data)} products.")
    print(f"Output saved to: {output_json}")

if __name__ == "__main__":
    # Default paths
    RAW = "assets/catalog_raw.csv"
    PROCESSED = "assets/catalog_processed.json"
    process_catalog(RAW, PROCESSED)
