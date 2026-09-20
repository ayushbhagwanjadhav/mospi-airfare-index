import asyncio
import json
import re
from datetime import datetime, timedelta

def parse_emt_payload(data_json, origin, destination, window_label, now_ts, target_date, obs_date_str):
    records = []
    date_num = target_date.strftime("%Y%m%d")
    dep_date_str = target_date.strftime("%Y-%m-%d")

    try:
        flights = []
        def extract_flights(node):
            if isinstance(node, list):
                for item in node: extract_flights(item)
            elif isinstance(node, dict):
                keys_str = str(node.keys()).lower()
                if ("flight" in keys_str or "flt" in keys_str) and ("fare" in keys_str or "price" in keys_str):
                    flights.append(node)
                for v in node.values():
                    if isinstance(v, (dict, list)): extract_flights(v)
        extract_flights(data_json)

        for flight in flights:
            c_name = flight.get("AirLineName", flight.get("AirlineName", flight.get("carrier", "XX")))
            dep_time_raw = flight.get("DepTime", flight.get("deptime", flight.get("DepartureTime", "00:00")))
            
            fare_node = flight.get("Fare", flight.get("fare", flight.get("price", {})))
            if isinstance(fare_node, dict):
                total_fare = fare_node.get("PublishedFare", fare_node.get("TotalFare", fare_node.get("grandTotal", 0)))
                base_fare = fare_node.get("BaseFare", fare_node.get("base", total_fare * 0.8))
                taxes = fare_node.get("Tax", fare_node.get("tax", total_fare * 0.2))
            else:
                total_fare = fare_node
                base_fare = total_fare * 0.8
                taxes = total_fare * 0.2

            try:
                total_fare = int(float(total_fare))
            except Exception:
                continue

            if total_fare > 500:
                carrier_code = "6E" if "indigo" in c_name.lower() else "SG" if "spice" in c_name.lower() else "AI" if "air india" in c_name.lower() else "QP" if "akasa" in c_name.lower() else "UK" if "vistara" in c_name.lower() else "IX"
                dep_time_clean = str(dep_time_raw).replace(":", "").replace(" ", "").strip()[:4]
                canonical_key = f"{origin}-{destination}_{date_num}_{carrier_code}_{dep_time_clean}"

                records.append({
                    "Observation_Date": obs_date_str,
                    "Departure_Date": dep_date_str,
                    "Extraction_Timestamp": now_ts,
                    "Source_Portal": "OTA_EaseMyTrip",
                    "Origin_Destination": f"{origin}-{destination}",
                    "Carrier_Name": str(c_name).strip(),
                    "Canonical_Flight_Key": canonical_key,
                    "Advance_Purchase_Window": window_label,
                    "Fare_Class": "Economy",
                    "Base_Fare_INR": round(float(base_fare), 2),
                    "Taxes_And_UDF_INR": round(float(taxes), 2),
                    "Total_Fare_INR": total_fare
                })
    except Exception as e:
        print(f"      -> [EMT PARSER ERROR] {e}")
    return records

async def scrape_route(page, origin, destination, window_days):
    now_dt = datetime.now()
    target_date = now_dt + timedelta(days=window_days)
    obs_date_str = now_dt.strftime("%Y-%m-%d")
    dep_date_str = target_date.strftime("%Y-%m-%d")
    window_label = f"T+{window_days}"
    date_str = target_date.strftime("%d/%m/%Y")
    date_num = target_date.strftime("%Y%m%d")
    
    print(f"\n[Adapter: EaseMyTrip] Sweeping {origin}-{destination} for {window_label} (Flight Date: {dep_date_str})...")
    captured_data = []
    payload_caught = False

    async def handle_response(response):
        nonlocal payload_caught
        try:
            if response.request.resource_type in ["fetch", "xhr"]:
                text_data = await response.text()
                text_lower = text_data.lower()
                if ("fare" in text_lower or "publishedfare" in text_lower) and ("airline" in text_lower or "flightno" in text_lower):
                    try:
                        data = json.loads(text_data)
                        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        parsed = parse_emt_payload(data, origin, destination, window_label, now_ts, target_date, obs_date_str)
                        if parsed:
                            captured_data.extend(parsed)
                            payload_caught = True
                            print(f"   -> [NETWORK] EMT API Intercepted! Parsed {len(parsed)} flights.")
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass

    page.on("response", handle_response)
    
    airport_map = {"DEL": "Delhi", "BOM": "Mumbai", "BLR": "Bangalore", "CCU": "Kolkata", "HYD": "Hyderabad", "MAA": "Chennai", "PNQ": "Pune"}
    o_name = airport_map.get(origin, origin)
    d_name = airport_map.get(destination, destination)
    
    search_url = f"https://flight.easemytrip.com/FlightList/Index?srch={origin}-{o_name}-India|{destination}-{d_name}-India|{date_str}&px=1-0-0&c=E&rd=0&isl=0&isow=true&issearch=true"
    
    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
        wait_time = 0
        while not payload_caught and wait_time < 20: 
            await asyncio.sleep(1)
            wait_time += 1
    except Exception as e:
        print(f"   -> [WARNING] EMT Navigation: {e}")

    page.remove_listener("response", handle_response)
    
    if not payload_caught:
        print("   -> [NOTICE] API masked. Activating DOM Screen-Reader...")
        try:
            await page.evaluate('''() => {
                let popups = document.querySelectorAll('.EMT_Layer, .emt_popup, #myModal, .modal, .login-popup');
                popups.forEach(p => p.remove());
            }''')
            await asyncio.sleep(3)
            
            page_text = await page.evaluate("document.body.innerText")
            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            carriers = {"IndiGo": "6E", "SpiceJet": "SG", "Air India Express": "IX", "Air India": "AI", "Akasa Air": "QP", "Vistara": "UK"}
            
            for carrier_name, carrier_code in carriers.items():
                pattern_1 = rf"{carrier_name}[\s\S]{{1,150}}?(\d{{2}}:\d{{2}})[\s\S]{{1,150}}?(?:₹|Rs\.?|INR)?\s*([\d,]{{4,}})"
                pattern_2 = rf"(\d{{2}}:\d{{2}})[\s\S]{{1,150}}?{carrier_name}[\s\S]{{1,150}}?(?:₹|Rs\.?|INR)?\s*([\d,]{{4,}})"
                
                for pattern in [pattern_1, pattern_2]:
                    matches = re.finditer(pattern, page_text, re.IGNORECASE)
                    for match in matches:
                        try:
                            time_str = match.group(1) if ":" in match.group(1) else match.group(2)
                            price_str = match.group(2).replace(",", "").strip() if ":" in match.group(1) else match.group(1).replace(",", "").strip()
                            price = int(price_str)
                            dep_time_clean = time_str.replace(":", "").strip()
                            
                            if price > 500:
                                canonical_key = f"{origin}-{destination}_{date_num}_{carrier_code}_{dep_time_clean}"
                                captured_data.append({
                                    "Observation_Date": obs_date_str,
                                    "Departure_Date": dep_date_str,
                                    "Extraction_Timestamp": now_ts,
                                    "Source_Portal": "OTA_EaseMyTrip",
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
                print(f"   -> [SUCCESS] Screen-Read {len(captured_data)} quotes from EMT pixels!")
        except Exception as e:
            print(f"   -> [OCR ERROR] {e}")

    if captured_data:
        seen = set()
        uniq = []
        for r in sorted(captured_data, key=lambda x: x["Total_Fare_INR"]):
            if r["Canonical_Flight_Key"] not in seen:
                seen.add(r["Canonical_Flight_Key"])
                uniq.append(r)
        captured_data = uniq
        print(f"[Adapter: EaseMyTrip] Extracted {len(captured_data)} clean quotes.")
    else:
        print("   -> [NOTICE] EMT completely failed to yield data.")
        
    return captured_data