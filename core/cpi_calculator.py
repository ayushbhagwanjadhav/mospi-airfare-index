import pandas as pd
import os

def generate_mospi_index(clean_data_path="data/cleaned_dataset.csv", 
                        report_path="data/mospi_cpi_report.csv", 
                        timeseries_path="data/mospi_cpi_timeseries.csv", 
                        base_fares_path="data/base_fares.csv"):
    print("\n" + "="*70)
    print("      APIx ENGINE: MoSPI CPI CALCULATOR (PS 26056)       ")
    print("="*70)

    if not os.path.exists(clean_data_path):
        print(f"[ERROR] Clean dataset not found at {clean_data_path}")
        return

    df = pd.read_csv(clean_data_path)
    print(f"[*] Loaded {len(df)} sanitized flight quotes across all observation dates.")

    # 1. Group by Observation Date, Route, and Window
    metrics = df.groupby(['Observation_Date', 'Origin_Destination', 'Advance_Purchase_Window']).agg(
        Total_Flights_Tracked=('Canonical_Flight_Key', 'count'),
        Minimum_Fare_INR=('Total_Fare_INR', 'min'),
        Average_Fare_INR=('Total_Fare_INR', 'mean'),
        Median_Fare_INR=('Total_Fare_INR', 'median')
    ).reset_index()
    metrics['Average_Fare_INR'] = metrics['Average_Fare_INR'].round(2)

    # 2. Dynamic Baseline Initialization
    if not os.path.exists(base_fares_path):
        first_obs_date = metrics['Observation_Date'].min()
        print(f"[NOTICE] No historical base found. Initializing Base Period from Day 1 ({first_obs_date}).")
        
        base_df = metrics[metrics['Observation_Date'] == first_obs_date][
            ['Origin_Destination', 'Advance_Purchase_Window', 'Average_Fare_INR']
        ].copy()
        base_df.rename(columns={'Average_Fare_INR': 'Base_Fare_INR'}, inplace=True)
        base_df.to_csv(base_fares_path, index=False)
        base_fares_dict = base_df.set_index(['Origin_Destination', 'Advance_Purchase_Window'])['Base_Fare_INR'].to_dict()
    else:
        print("[*] Historical base dataset found. Calculating inflation relative to baseline...")
        base_df = pd.read_csv(base_fares_path)
        base_fares_dict = base_df.set_index(['Origin_Destination', 'Advance_Purchase_Window'])['Base_Fare_INR'].to_dict()

    # 3. Calculate CPI for each observation date
    def calculate_cpi(row):
        key = (row['Origin_Destination'], row['Advance_Purchase_Window'])
        current_price = row['Average_Fare_INR']
        base_price = base_fares_dict.get(key, current_price)
        return round((current_price / base_price) * 100, 2)

    metrics['MoSPI_Base_Fare'] = metrics.apply(
        lambda r: base_fares_dict.get((r['Origin_Destination'], r['Advance_Purchase_Window']), r['Average_Fare_INR']), 
        axis=1
    )
    metrics['Airfare_CPI_Index'] = metrics.apply(calculate_cpi, axis=1)
    metrics['Inflation_Percentage'] = (metrics['Airfare_CPI_Index'] - 100).round(2)

    window_order = {'T+1': 1, 'T+7': 2, 'T+15': 3, 'T+30': 4}
    metrics['order'] = metrics['Advance_Purchase_Window'].map(window_order)
    metrics = metrics.sort_values(by=['Observation_Date', 'Origin_Destination', 'order']).drop(columns=['order'])

    # 4. Save Cumulative 30-Day Time Series
    metrics.to_csv(timeseries_path, index=False)
    
    # 5. Save Latest Snapshot Report
    latest_date = metrics['Observation_Date'].max()
    latest_snapshot = metrics[metrics['Observation_Date'] == latest_date]
    latest_snapshot.to_csv(report_path, index=False)

    print(f"\n[SUCCESS] MoSPI Index for Latest Date ({latest_date}):")
    print(latest_snapshot[['Origin_Destination', 'Advance_Purchase_Window', 'Average_Fare_INR', 'Airfare_CPI_Index', 'Inflation_Percentage']].to_string(index=False))
    print(f"\n[*] Cumulative time series saved to: {timeseries_path}")
    print(f"[*] Latest snapshot saved to: {report_path}")

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    generate_mospi_index()