# -*- coding: utf-8 -*-

import asyncio
import json

import zendriver as zd


async def scrape(page: zd.Tab):

    await page.get("https://www.fknc.top")
    await page.wait_for_ready_state(until="complete")

    # Avoid the invitation modal appearing during scraping.
    await page.evaluate('localStorage["invite_modal_first_shown"] = "1"')

    email_login = await page.select(
        "div.login-tab-row > div.login-tab:nth-child(2)",
        timeout=60,
    )
    await email_login.click()

    email = await page.select("input[type=email]")
    password = await page.select("input[type=password]")
    eula = await page.select("input[type=checkbox]")
    login = await page.select("button[type=submit]")

    await email.send_keys("mokurin000@gmail.com")
    await password.send_keys("9XlM3fhaGVyguvXJun26iP9UCpa935")
    await eula.click()

    await login.click()

    fknc_data = None

    # `fknc_game_data` is written to localStorage asynchronously after login,
    # so wait until the application has populated it.
    while fknc_data is None:
        await asyncio.sleep(0.1)

        value = await page.evaluate('localStorage.getItem("fknc_game_data")')

        if value:
            fknc_data = json.loads(value)

    plants = fknc_data["crops"]
    mutations = fknc_data["mutations"]

    with open("game_data.json", "w", encoding="utf-8") as f:
        json.dump(
            fknc_data,
            f,
            ensure_ascii=False,
            indent=2,
        )

    with open("src/fknc_calc/plants.json", "w", encoding="utf-8") as f:
        json.dump(
            plants,
            f,
            ensure_ascii=False,
            indent=2,
        )

    def clean_mut(mut: dict) -> dict:
        # These fields are runtime/UI metadata and are not needed by the
        # calculator.
        mut.pop("sortOrder", None)
        mut.pop("isActive", None)
        mut.pop("shareBitIndex", None)
        return mut

    with open("src/fknc_calc/mutations.json", "w", encoding="utf-8") as f:
        json.dump(
            [clean_mut(mut) for mut in mutations],
            f,
            ensure_ascii=False,
            indent=2,
        )


async def main():
    browser = await zd.start(
        headless=True,
    )

    try:
        page = await browser.get("https://www.fknc.top")
        await scrape(page)
    finally:
        print("Scrape done, cleaning-up...")
        await browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
