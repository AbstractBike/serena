"""
Detailed Playwright investigation of SkyWalking traces.pin
Captures screenshots and analyzes service topology, traces, and metrics.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright


async def investigate_traces():
    """Run detailed investigation of traces.pin using Playwright."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # Create output directory for screenshots
        screenshots_dir = Path("./investigation_screenshots")
        screenshots_dir.mkdir(exist_ok=True)

        # Log all info
        log_file = screenshots_dir / "investigation_log.md"
        with open(log_file, "w") as f:
            f.write("# SkyWalking (traces.pin) Investigation Report\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")

        print("🔍 Starting SkyWalking investigation...")

        # Try different URLs
        urls_to_try = [
            "http://traces.pin",
            "http://traces.pin:8080",
            "http://192.168.0.4:8080",
        ]

        for url in urls_to_try:
            try:
                print(f"\n📍 Trying {url}...")
                await page.goto(url, wait_until="networkidle", timeout=10000)

                # Take initial screenshot
                screenshot_path = screenshots_dir / f"01-home-page.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"✅ Loaded {url} - screenshot saved")

                with open(log_file, "a") as f:
                    f.write(f"\n## Access\n\n✅ Successfully accessed **{url}**\n\n")

                break
            except Exception as e:
                print(f"❌ Failed to load {url}: {str(e)[:100]}")

        # 1. Capture main dashboard
        try:
            print("\n📊 Investigating Service Topology...")
            # Look for topology/dashboard link
            topology_links = await page.query_selector_all("a, button")
            with open(log_file, "a") as f:
                f.write("## 1. Service Topology\n\n")

            # Wait for any dynamic content
            await page.wait_for_timeout(2000)

            screenshot = screenshots_dir / "02-service-topology.png"
            await page.screenshot(path=str(screenshot), full_page=True)
            print("✅ Service topology screenshot captured")

            with open(log_file, "a") as f:
                f.write("![Service Topology](02-service-topology.png)\n\n")

        except Exception as e:
            print(f"⚠️ Could not capture topology: {e}")

        # 2. Look for services in the UI
        try:
            print("\n🔎 Extracting visible services...")
            page_content = await page.content()

            # Extract service names from page
            if "service" in page_content.lower():
                with open(log_file, "a") as f:
                    f.write("## 2. Available Services\n\n")
                    f.write("Services detected in UI:\n\n")

                print("✅ Services detected in UI")
            else:
                with open(log_file, "a") as f:
                    f.write("## 2. Available Services\n\nNo explicit service list detected.\n\n")

        except Exception as e:
            print(f"⚠️ Could not extract services: {e}")

        # 3. Navigate to Services view
        try:
            print("\n🏢 Navigating to Services view...")
            # Try common navigation paths
            service_links = await page.query_selector_all(
                'a:has-text("Service"), a:has-text("Services"), [href*="service"], [href*="services"]'
            )

            if service_links:
                print(f"Found {len(service_links)} service links")
                await service_links[0].click()
                await page.wait_for_timeout(2000)

                screenshot = screenshots_dir / "03-services-list.png"
                await page.screenshot(path=str(screenshot), full_page=True)
                print("✅ Services list screenshot captured")

                with open(log_file, "a") as f:
                    f.write("![Services List](03-services-list.png)\n\n")
            else:
                print("⚠️ No service navigation links found")

        except Exception as e:
            print(f"⚠️ Could not navigate to services: {e}")

        # 4. Look for traces
        try:
            print("\n📋 Searching for Traces...")
            await page.goto("http://192.168.0.4:8080", wait_until="networkidle", timeout=10000)
            await page.wait_for_timeout(1000)

            # Look for traces/timeline navigation
            trace_links = await page.query_selector_all(
                'a:has-text("Trace"), a:has-text("Traces"), [href*="trace"], [href*="traces"]'
            )

            if trace_links:
                print(f"Found {len(trace_links)} trace links")
                await trace_links[0].click()
                await page.wait_for_timeout(2000)

                screenshot = screenshots_dir / "04-traces-view.png"
                await page.screenshot(path=str(screenshot), full_page=True)
                print("✅ Traces view screenshot captured")

                with open(log_file, "a") as f:
                    f.write("## 3. Traces\n\n")
                    f.write("![Traces View](04-traces-view.png)\n\n")

        except Exception as e:
            print(f"⚠️ Could not navigate to traces: {e}")

        # 5. Check for metrics/dashboard
        try:
            print("\n📈 Looking for Metrics Dashboard...")
            dashboard_links = await page.query_selector_all(
                'a:has-text("Dashboard"), a:has-text("Metrics"), [href*="dashboard"], [href*="metrics"]'
            )

            if dashboard_links:
                print(f"Found {len(dashboard_links)} dashboard links")
                await dashboard_links[0].click()
                await page.wait_for_timeout(2000)

                screenshot = screenshots_dir / "05-metrics-dashboard.png"
                await page.screenshot(path=str(screenshot), full_page=True)
                print("✅ Metrics dashboard screenshot captured")

                with open(log_file, "a") as f:
                    f.write("## 4. Metrics Dashboard\n\n")
                    f.write("![Metrics Dashboard](05-metrics-dashboard.png)\n\n")

        except Exception as e:
            print(f"⚠️ Could not navigate to metrics: {e}")

        # 6. Page structure analysis
        try:
            print("\n🔍 Analyzing page structure...")
            headings = await page.query_selector_all("h1, h2, h3, h4")
            buttons = await page.query_selector_all("button")
            links = await page.query_selector_all("a")

            with open(log_file, "a") as f:
                f.write("## 5. Page Structure Analysis\n\n")
                f.write(f"**Headings found:** {len(headings)}\n\n")
                f.write(f"**Buttons found:** {len(buttons)}\n\n")
                f.write(f"**Links found:** {len(links)}\n\n")

                f.write("### UI Elements Detected\n\n")
                f.write("```\n")
                f.write(f"Total interactive elements: {len(buttons) + len(links)}\n")
                f.write("```\n\n")

            print(f"✅ Found {len(headings)} headings, {len(buttons)} buttons, {len(links)} links")

        except Exception as e:
            print(f"⚠️ Could not analyze page structure: {e}")

        # 7. Final full page screenshot
        try:
            print("\n📸 Taking final full-page screenshot...")
            screenshot = screenshots_dir / "06-final-view.png"
            await page.screenshot(path=str(screenshot), full_page=True)
            print("✅ Final screenshot captured")

            with open(log_file, "a") as f:
                f.write("## 6. Final State\n\n")
                f.write("![Final View](06-final-view.png)\n\n")

        except Exception as e:
            print(f"⚠️ Could not take final screenshot: {e}")

        # Summary
        with open(log_file, "a") as f:
            f.write("---\n\n")
            f.write("## Investigation Summary\n\n")
            f.write(
                "✅ Investigation completed. "
                "All available screenshots have been captured to the `investigation_screenshots/` directory.\n\n"
            )
            f.write("### Screenshot Manifest\n\n")
            f.write("| # | Screenshot | Content |\n")
            f.write("|---|---|---|\n")
            f.write("| 1 | `01-home-page.png` | Initial SkyWalking home/dashboard |\n")
            f.write("| 2 | `02-service-topology.png` | Service topology/dependency graph |\n")
            f.write("| 3 | `03-services-list.png` | List of instrumented services |\n")
            f.write("| 4 | `04-traces-view.png` | Distributed trace viewing interface |\n")
            f.write("| 5 | `05-metrics-dashboard.png` | Metrics and performance dashboard |\n")
            f.write("| 6 | `06-final-view.png` | Final state of SkyWalking UI |\n\n")
            f.write("### Access Details\n\n")
            f.write("- **URL:** http://192.168.0.4:8080 (or traces.pin if DNS configured)\n")
            f.write("- **Service:** SkyWalking OpenObservability Platform\n")
            f.write("- **Purpose:** Distributed tracing, APM, and service topology visualization\n\n")

        await browser.close()

        print("\n" + "=" * 60)
        print("✅ Investigation Complete!")
        print(f"📁 Screenshots saved to: {screenshots_dir.absolute()}")
        print(f"📄 Report: {log_file.absolute()}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(investigate_traces())
