import asyncio
import json
from playwright.async_api import async_playwright

async def discover_apis():
    async with async_playwright() as p:
        # 이미 실행 중인 브라우저(9222 포트)에 연결
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await context.new_page()

        print("\n" + "="*50)
        print("🚀 API Discovery Started (Target: CDP localhost:9222)")
        print("="*50 + "\n")

        # 요청 모니터링 핸들러
        async def handle_request(request):
            url = request.url
            # 영화관 관련 이벤트 목록 API로 의심되는 키워드들
            keywords = ["event", "list", "select", "ajax", "json", "GetEvent", "ohg"]
            if any(kw in url.lower() for kw in keywords) and request.resource_type in ["xhr", "fetch"]:
                print(f"[{request.method}] {url}")
                if request.post_data:
                    print(f"   -> Payload: {request.post_data}")
                print("-" * 30)

        page.on("request", handle_request)

        # 1. CGV
        print("\n--- Visiting CGV ---")
        await page.goto("https://m.cgv.co.kr/WebApp/EventNotiV8/EventList.aspx", wait_until="networkidle")
        await asyncio.sleep(3)

        # 2. Megabox
        print("\n--- Visiting Megabox ---")
        await page.goto("https://www.megabox.co.kr/event", wait_until="networkidle")
        await asyncio.sleep(3)

        # 3. CineQ
        print("\n--- Visiting CineQ ---")
        await page.goto("https://www.cineq.co.kr/Event/List", wait_until="networkidle")
        await asyncio.sleep(3)

        print("\n" + "="*50)
        print("✅ API Discovery Finished")
        print("="*50 + "\n")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(discover_apis())
