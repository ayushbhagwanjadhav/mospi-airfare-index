import asyncio
import re
from datetime import datetime, timedelta

async def scrape_route(page, origin, destination, window_days):
    now_dt = datetime.now()
    target_date = now_dt + timedelta(days=window_days)
    obs_date_str = now_dt.strftime("%Y-%m-%d")
    dep_date_str = target_date.strftime("%Y-%m-%d")
    window_label = f"T+{window_days}"
    date_num = target_date.strftime("%Y%m%d")
    
    print(f"\n[Adapter: Google Flights] Sweeping {origin}-{destination} for {window_label} (Flight Date: {dep_date_str})...")
    captured_data = []

    search_url = f"https://www.google.com/travel/flights?q=Flights%20from%20{origin}%20to%20{destination}%20on%20{dep_date_str}%20oneway"

    try:
        await page.goto(search_url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(6)
        
        page_text = await page.evaluate("document.body.innerText")
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        carriers = {
            "IndiGo": "6E", "SpiceJet": "SG", "Air India Express": "IX",
            "Air India": "AI", "Akasa Air": "QP", "Vistara": "UK"
        }
        
        for carrier_name, carrier_code in carriers.items():
            pattern = rf"(\d{{1,2}}:\d{{2}}\s*(?:AM|PM))[\s\S]{{1,120}}?({carrier_name})[\s\S]{{1,120}}?(?:₹|Rs\.?|INR)\s*([\d,]+)"
            matches = re.finditer(pattern, page_text, re.IGNORECASE)
            
            for match in matches:
                raw_time = match.group(1).strip()
                price_str = match.group(3).replace(",", "").strip()
                
                try:
                    price = int(price_str)
                    clean_time_str = raw_time.replace(" ", "").replace("\u202f", "")
                    time_dt = datetime.strptime(clean_time_str, "%I:%M%p")
                    dep_time_24 = time_dt.strftime("%H%M")
                    
                    if price > 500:
                        canonical_key = f"{origin}-{destination}_{date_num}_{carrier_code}_{dep_time_24}"
                        captured_data.append({
                            "Observation_Date": obs_date_str,
                            "Departure_Date": dep_date_str,
                            "Extraction_Timestamp": now_ts,
                            "Source_Portal": "OTA_GoogleFlights",
                            "Origin_Destination": f"{origin}-{destination}",
                            "Carrier_Name": carrier_name,
                            "Canonical_Flight_Key": canonical_key,
                            "Advance_Purchase_Window": window_label,
                            "Fare_Class": "Economy",
                            "Base_Fare_INR": round(price * 0.8, 2),
                            "Taxes_And_UDF_INR": round(price * 0.2, 2),
                            "Total_Fare_INR": price
                        })
                except Exception:
                    pass
        
        if captured_data:
            seen = set()
            uniq = []
            for r in sorted(captured_data, key=lambda x: x["Total_Fare_INR"]):
                if r["Canonical_Flight_Key"] not in seen:
                    seen.add(r["Canonical_Flight_Key"])
                    uniq.append(r)
            captured_data = uniq
            print(f"   -> [SUCCESS] Extracted {len(captured_data)} normalized quotes from Google Flights.")
        else:
            print("   -> [NOTICE] Screen-Reader found no matching price patterns.")
            
    except Exception as e:
        print(f"   -> [WARNING] Google Flights Execution: {e}")

    return captured_data