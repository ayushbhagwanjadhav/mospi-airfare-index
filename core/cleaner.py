import os
import pandas as pd

def process_and_deduplicate(master_csv_path, output_csv_path):
    print("\n" + "="*70)
    print("      APIx ENGINE: DATA SANITIZATION & DEDUPLICATION       ")
    print("="*70)

    if not os.path.exists(master_csv_path):
        print(f"[ERROR] Master dataset not found at {master_csv_path}")
        return None

    df = pd.read_csv(master_csv_path)
    initial_count = len(df)
    print(f"[*] Loaded raw master dataset: {initial_count} rows.")

    df['Total_Fare_INR'] = pd.to_numeric(df['Total_Fare_INR'], errors='coerce')
    df = df.dropna(subset=['Total_Fare_INR', 'Canonical_Flight_Key', 'Observation_Date'])
    df = df[df['Total_Fare_INR'] > 500] 

    # Sort so cheapest quotes surface first
    df = df.sort_values(by=['Observation_Date', 'Canonical_Flight_Key', 'Advance_Purchase_Window', 'Total_Fare_INR'], ascending=[True, True, True, True])
    
    # Drop duplicates per flight key on that observation date
    df_clean = df.drop_duplicates(subset=['Observation_Date', 'Canonical_Flight_Key', 'Advance_Purchase_Window'], keep='first')
    
    final_count = len(df_clean)
    duplicates_removed = initial_count - final_count

    df_clean.to_csv(output_csv_path, index=False)
    
    print(f"[*] Multi-Source Deduplication: Removed {duplicates_removed} overlapping listings.")
    print(f"[SUCCESS] Final sanitized dataset saved to {output_csv_path} with {final_count} lowest-fare quotes.\n")
    
    return df_clean

if __name__ == "__main__":
    process_and_deduplicate("data/master_dataset.csv", "data/cleaned_dataset.csv")