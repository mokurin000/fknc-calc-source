# -*- coding: utf-8 -*-

import asyncio
import json

from playwright.async_api import async_playwright, Page

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"


async def scrape(page: Page):
    email_login = page.locator("div.login-tab-row > div.login-tab:nth-child(2)")
    email = page.locator("input[type=email]")
    password = page.locator("input[type=password]")
    eula = page.locator("input[type=checkbox]")
    login = page.locator("button[type=submit]")

    await page.goto("https://www.fknc.top")
    await page.evaluate('localStorage["invite_modal_first_shown"] = "1"')

    await email_login.click(timeout=0)
    await email.fill("mokurin000@gmail.com")
    await password.fill("9XlM3fhaGVyguvXJun26iP9UCpa935")
    await eula.check()

    await login.click()

    fknc_data = None

    while fknc_data is None:
        await asyncio.sleep(0.1)

        state = await page.context.storage_state()
        fknc_localStorage = state["origins"][0]["localStorage"]
        for entry in fknc_localStorage:
            if entry["name"] == "fknc_game_data":
                fknc_data = json.loads(entry["value"])
                break

    plants = fknc_data["crops"]
    mutations = fknc_data["mutations"]

    with open("src/fknc_calc/plants.json", "w", encoding="utf-8") as f:
        json.dump(
            plants,
            f,
            ensure_ascii=False,
            indent=2,
        )
    with open("src/fknc_calc/mutations.json", "w", encoding="utf-8") as f:

        def clean_mut(mut: dict) -> dict:
            mut.pop("sortOrder")
            mut.pop("isActive")
            mut.pop("shareBitIndex")
            return mut

        json.dump(
            [clean_mut(mut) for mut in mutations],
            f,
            ensure_ascii=False,
            indent=2,
        )


async def main():
    async with async_playwright() as pw:
        async with await pw.chromium.launch(
            channel="chrome",
            headless=False,
        ) as browser:
            async with await browser.new_context(
                user_agent=USER_AGENT,
            ) as ctx:
                async with await ctx.new_page() as page:
                    await scrape(page)


if __name__ == "__main__":
    asyncio.run(main())
