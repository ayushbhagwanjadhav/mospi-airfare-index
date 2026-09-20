import os
import pandas as pd
import pytest
from datetime import datetime

# Test 1: Deduplication Logic Verification
def test_cleaner_logic():
    clean_path = "data/cleaned_dataset.csv"
    if not os.path.exists(clean_path):
        pytest.skip("No clean data found to test.")
    
    df = pd.read_csv(clean_path)
    # Ensure no duplicate canonical keys exist for the same observation date
    duplicates = df.duplicated(subset=['Observation_Date', 'Canonical_Flight_Key']).sum()
    assert duplicates == 0, f"Found {duplicates} duplicate flights on the same observation date!"

# Test 2: Price Floor Validation
def test_price_integrity():
    clean_path = "data/cleaned_dataset.csv"
    if not os.path.exists(clean_path):
        pytest.skip("No clean data found to test.")
        
    df = pd.read_csv(clean_path)
    # Ensure no glitch/zero-rupee fares bypassed the sanitization layer
    invalid_fares = len(df[df['Total_Fare_INR'] < 500])
    assert invalid_fares == 0, f"Data corruption: Found {invalid_fares} fares under 500 INR."

# Test 3: Base Math Verification
def test_cpi_math_execution():
    report_path = "data/mospi_cpi_report.csv"
    if not os.path.exists(report_path):
        pytest.skip("No CPI report found.")
        
    df = pd.read_csv(report_path)
    # Ensure inflation percentage perfectly matches the index shift
    df['Math_Check'] = (df['Airfare_CPI_Index'] - 100).round(2)
    mismatches = len(df[df['Math_Check'] != df['Inflation_Percentage']])
    assert mismatches == 0, "CPI Index to Inflation Percentage math is disjointed!"