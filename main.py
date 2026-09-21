import asyncio
import os
import random
import pandas as pd
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

import config
from adapters import ota_easemytrip
from adapters import ota_google
from core import cleaner

def get_proxy_settings():
    if config.USE_PROXY and config.PROXY_SERVER:
        return {"server": config.PROXY_SERVER}
    return None

async def run_pipeline():
    print("=" * 70, flush=True)
    print("      APIx ENGINE: MASTER CLOUD ORCHESTRATOR (PS 26056)       ", flush=True)
    print("=" * 70, flush=True)

    os.makedirs(config.DATA_DIR, exist_ok=True)
    proxy_config = get_proxy_settings()

    async with async_playwright() as p:
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--ignore-certificate-errors",
            "--no-sandbox"
        ]

        browser = await p.chromium.launch(
            headless=True,
            proxy=proxy_config,
            args=launch_args
        )

        print(f"[*] Proxy Tunnel: {'Active' if proxy_config else 'Direct Interface'}", flush=True)

        for route in config.ROUTES:
            for window_days in config.T_WINDOWS:
                current_sweep_records = []

                v_width = random.randint(1366, 1920)
                v_height = random.randint(768, 1080)

                context = await browser.new_context(
                    viewport={'width': v_width, 'height': v_height},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )

                # --- BANDWIDTH HACK FOR 30-DAY CLOUD RUN ---
                await context.route("**/*", lambda route: route.abort() 
                    if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
                    else route.continue_()
                )

                # EaseMyTrip Pass
                page_emt = await context.new_page()
                await stealth_async(page_emt)
                try:
                    records_emt = await ota_easemytrip.scrape_route(page_emt, route["origin"], route["destination"], window_days)
                    if records_emt:
                        current_sweep_records.extend(records_emt)
                except Exception as e:
                    print(f"   -> [ERROR EMT] {e}", flush=True)
                finally:
                    await page_emt.close()

                # Google Flights Pass
                page_goog = await context.new_page()
                await stealth_async(page_goog)
                try:
                    records_goog = await ota_google.scrape_route(page_goog, route["origin"], route["destination"], window_days)
                    if records_goog:
                        current_sweep_records.extend(records_goog)
                except Exception as e:
                    print(f"   -> [ERROR Google] {e}", flush=True)
                finally:
                    await page_goog.close()

                await context.close()

                # Deduplication & Persistence
                if current_sweep_records:
                    df_new = pd.DataFrame(current_sweep_records)
                    
                    if os.path.exists(config.MASTER_DATASET_PATH):
                        df_existing = pd.read_csv(config.MASTER_DATASET_PATH)
                        df_combined = pd.concat([df_existing, df_new]).drop_duplicates(
                            subset=["Source_Portal", "Canonical_Flight_Key", "Advance_Purchase_Window", "Extraction_Timestamp"],
                            keep="last"
                        )
                        df_combined.to_csv(config.MASTER_DATASET_PATH, index=False)
                    else:
                        df_new.to_csv(config.MASTER_DATASET_PATH, index=False)

                    cleaner.process_and_deduplicate(config.MASTER_DATASET_PATH, config.CLEANED_DATASET_PATH)

                jitter = random.uniform(4.5, 8.5)
                await asyncio.sleep(jitter)

        await browser.close()
        print("\n[COMPLETE] Multi-OTA sweep finished successfully.", flush=True)

if __name__ == "__main__":
    asyncio.run(run_pipeline())
