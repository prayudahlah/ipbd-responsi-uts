import marimo

__generated_with = "0.23.2"
app = marimo.App(width="columns")


@app.cell(column=0, hide_code=True)
def _(mo):
    mo.md(r"""
    # Libraries
    """)
    return


@app.cell
def _():
    import marimo as mo
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import NoSuchElementException
    from datetime import datetime
    import logging
    import time
    import random
    import json
    import os

    return (
        By,
        NoSuchElementException,
        datetime,
        json,
        logging,
        mo,
        random,
        time,
        uc,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Constants dan Logging
    """)
    return


@app.cell
def _(logging):
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    ]

    TARGET_URL = "https://www.wired.com"

    OUTPUT_FILE = "wired_articles.json"

    MAX_ARTICLES = 100

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger(__name__)
    return MAX_ARTICLES, OUTPUT_FILE, TARGET_URL, USER_AGENTS, logger


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Utility Functions
    """)
    return


@app.cell
def _(
    By,
    NoSuchElementException,
    USER_AGENTS,
    datetime,
    logger,
    random,
    time,
    uc,
):
    def setup_driver():
        options = uc.ChromeOptions()

        options.binary_location = "/usr/bin/chromium"

        # User-Agent random
        options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")

        # Anti-detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")

        options.add_argument("--start-maximized")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")

        driver = uc.Chrome(
            options=options,
            browser_executable_path="/usr/bin/chromium",
            version_main=None,
        )

        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        return driver


    def random_delay(min_seconds: float = 0.5, max_seconds: float = 2):
        time.sleep(random.uniform(min_seconds, max_seconds))


    def get_text(driver, selector, default):
        try:
            elem = driver.find_element(By.CSS_SELECTOR, selector)
            return elem.text.strip() if elem.text else default
        except NoSuchElementException:
            return default


    def clean_link(link):
        if link and "/story/" in link:
            return link.split("/")[4]
        return None


    def parse_wired_date(date_string):
        month_map = {
            "JAN": 1,
            "FEB": 2,
            "MAR": 3,
            "APR": 4,
            "MAY": 5,
            "JUN": 6,
            "JUL": 7,
            "AUG": 8,
            "SEP": 9,
            "OCT": 10,
            "NOV": 11,
            "DEC": 12,
        }

        parts = date_string.replace(",", "").split()
        # contoh parts = ['APR', '21', '2026', '6:00', 'AM']

        month = month_map[parts[0].upper()]
        day = int(parts[1])
        year = int(parts[2])

        time_str = parts[3]
        hour, minute = map(int, time_str.split(":"))

        # Konversi ke 24-hour format
        if parts[4].upper() == "PM" and hour != 12:
            hour += 12
        elif parts[4].upper() == "AM" and hour == 12:
            hour = 0

        # Buat datetime object
        dt = datetime(year, month, day, hour, minute)

        # Format untuk PostgreSQL (ISO format)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


    def log_visit(index, total, link, success=True, title=None, error_msg=None):
        if success:
            logger.info(f"[{index}/{total}] SUCCESS | {title[:60]}... | {link}")
        else:
            logger.error(f"[{index}/{total}] FAILED | {error_msg} | {link}")

    return clean_link, get_text, parse_wired_date, random_delay, setup_driver


@app.cell
def _():
    return


@app.cell(column=1, hide_code=True)
def _(mo):
    mo.md(r"""
    # Scrape
    """)
    return


@app.cell
def _(
    By,
    MAX_ARTICLES,
    OUTPUT_FILE,
    TARGET_URL,
    clean_link,
    get_text,
    json,
    logger,
    parse_wired_date,
    random_delay,
    setup_driver,
):
    driver = setup_driver()
    driver.get(TARGET_URL)
    result = []
    article_links = {}


    # Ambil initial links
    hrefs = driver.find_elements(By.CSS_SELECTOR, "a[href*='/story/']")
    for href in hrefs:
        link = href.get_attribute("href")
        link = clean_link(link)
        if link:
            article_links[f"{TARGET_URL}/story/{link}"] = False

    logger.info(
        f"Starting scraping | Target: {MAX_ARTICLES} articles | Initial links: {len(article_links)}"
    )


    while len(result) < MAX_ARTICLES:
        random_delay(0.5, 2)

        unvisitted_links = [
            link for link, visited in article_links.items() if not visited
        ]

        for link in unvisitted_links:
            if len(result) >= MAX_ARTICLES:
                break

            try:
                driver.get(link)
                random_delay(0.5, 2)

                title = get_text(driver, "h1", None)
                authors = get_text(driver, "span[class^='BylineWrapper']", None)
                authors = (
                    [a.strip() for a in authors.split("\n") if a.strip()]
                    if authors
                    else None
                )
                date = get_text(driver, "time", None)
                date = parse_wired_date(date) if date else None

                result.append(
                    {
                        "title": title,
                        "authors": authors,
                        "date": date,
                        "link": link,
                    }
                )

                article_links[link] = True

                current_count = len(result)
                logger.info(f"[{current_count}/{MAX_ARTICLES}] {title[:70]}")

                hrefs = driver.find_elements(By.CSS_SELECTOR, "a[href*='/story/']")
                new_count = 0
                for href in hrefs:
                    link = href.get_attribute("href")
                    link = clean_link(link)
                    if link and f"{TARGET_URL}/story/{link}" not in article_links:
                        article_links[f"{TARGET_URL}/story/{link}"] = False
                        new_count += 1

                if new_count > 0:
                    logger.info(
                        f"Discovered {new_count} new links | Total pending: {sum(1 for v in article_links.values() if not v)}"
                    )
            except Exception as e:
                logger.error(f"Failed: {str(e)[:100]} | {link}")
                article_links[link] = True
                continue

    driver.quit()
    logger.info(f"Total links discovered: {len(article_links)}")
    logger.info(f"Articles scraped: {len(result)}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return


if __name__ == "__main__":
    app.run()
