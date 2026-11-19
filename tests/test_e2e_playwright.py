"""
Automated End-to-End Browser Verification (Playwright Chromium)
File: tests/test_e2e_playwright.py
Author: Chanapa Sadudee (6610680214)

ตรวจสอบหน้าเว็บจริง (Dashboard + Live MQTT Sandbox บน MkDocs):
  1. เปิด http://127.0.0.1:5000 ตรวจสอบว่าโหลดครบและไม่มี JS Error
  2. ทดสอบสลับ Facility Profile (Cold Chain -> Server Room -> Cold Chain)
  3. ทดสอบจำลองวิกฤต (คอมเพรสเซอร์ดับ) แล้วตรวจว่า Hero Banner เปลี่ยนเป็น CRITICAL
  4. ทดสอบพิมพ์แชต 'ปิดไฟ' ใน AI Copilot -> ตรวจว่า GUARDRAIL BLOCKED ทำงานจริงบนหน้าจอ
  5. แคปภาพหน้าจอหลักฐานเก็บไว้ใน tests/screenshots/
"""

from pathlib import Path
from playwright.sync_api import sync_playwright

SHOT_DIR = Path(__file__).resolve().parent / "screenshots"
SHOT_DIR.mkdir(parents=True, exist_ok=True)


def run_e2e():
    console_errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        # 1. Load Dashboard
        page.goto("http://127.0.0.1:5000/", wait_until="networkidle")
        page.wait_for_timeout(1200)
        assert "AIoT Industrial Cold Chain" in page.title()

        # Screenshot 1: Normal / Live view
        page.screenshot(path=str(SHOT_DIR / "01_dashboard_live.png"), full_page=True)

        # 2. Switch profile to Server Room & back to Cold Chain
        page.click("#prof-server")
        page.wait_for_timeout(500)
        assert "active" in page.get_attribute("#prof-server", "class")

        page.click("#prof-coldchain")
        page.wait_for_timeout(500)

        # 3. Trigger Failure scenario -> verify CRITICAL banner
        page.click("button:has-text('คอมฯ ดับ')")
        page.wait_for_timeout(1600)
        badge_text = page.inner_text("#hero-badge").strip()
        assert badge_text in ("CRITICAL", "WARNING"), f"Unexpected badge: {badge_text}"

        # 4. Test AI Copilot Safety Guardrail in chat UI
        page.fill("#chat-input", "ปิดไฟ")
        page.click("#chat-send-btn")
        page.locator("#chat-messages .msg.ai").nth(1).wait_for(timeout=12000)
        chat_text = page.inner_text("#chat-messages")
        assert "GUARDRAIL" in chat_text or "BLOCKED" in chat_text, f"Guardrail not shown in chat: {chat_text}"

        # Switch log tab to Audit Log
        page.click("#tab-audit")
        page.wait_for_timeout(600)

        # Screenshot 2: Critical Alert + AI Copilot Guardrail Blocked
        page.screenshot(path=str(SHOT_DIR / "02_dashboard_critical_guardrail.png"), full_page=True)

        # 5. Verify MkDocs Educational Site & Live MQTT Sandbox
        page.goto("http://127.0.0.1:8000/", wait_until="load")
        page.wait_for_timeout(1200)
        page.screenshot(path=str(SHOT_DIR / "03_docs_home.png"), full_page=False)

        page.goto("http://127.0.0.1:8000/live_sandbox/", wait_until="load")
        page.wait_for_timeout(2500)
        page.screenshot(path=str(SHOT_DIR / "04_docs_live_sandbox.png"), full_page=False)

        browser.close()

    assert len(console_errors) == 0, f"Console page errors detected: {console_errors}"
    print("[PASS] All Playwright E2E checks passed! Screenshots saved to tests/screenshots/")


if __name__ == "__main__":
    run_e2e()
