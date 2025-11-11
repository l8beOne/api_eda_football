from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import time
import csv

URL = "https://www.capology.com/de/1-bundesliga/salaries/"

def scrape_current_league(driver, writer, csvfile):
    while True:
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#table tbody tr'))
            )
        except Exception:
            return

        try:
            rows = driver.find_elements(By.CSS_SELECTOR, '#table tbody tr')
        except StaleElementReferenceException:
            continue

        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, 'td')
            except StaleElementReferenceException:
                continue

            if len(cells) < 8:
                continue

            try:
                try:
                    name = row.find_element(
                        By.CSS_SELECTOR,
                        'td.name-column a.firstcol'
                    ).text.strip()
                except Exception:
                    name = cells[0].text.strip()

                signed = cells[5].text.strip()
                expiration = cells[6].text.strip()
                years_remaining = cells[7].text.strip()
            except StaleElementReferenceException:
                continue

            if not signed and not expiration and not years_remaining:
                continue

            writer.writerow([name, signed, expiration, years_remaining])

        csvfile.flush()

        try:
            current_page_el = driver.find_element(
                By.XPATH,
                '//ul[contains(@class,"pagination")]/li[contains(@class,"active")]/a'
            )
            last_page_el = driver.find_element(
                By.XPATH,
                '(//ul[contains(@class,"pagination")]/li[a[@aria-label and contains(@aria-label, "to page")]]/a)[last()]'
            )
            current_page = current_page_el.text.strip()
            last_page = last_page_el.text.strip()
            if current_page == last_page:
                break
        except StaleElementReferenceException:
            continue
        except Exception:
            pass

        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//li[contains(@class,"page-next") and not(contains(@class,"disabled"))]'
                        '/a[@class="page-link" and @aria-label="next page"]'
                    )
                )
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", next_button
            )
            next_button.click()
        except Exception:
            break


def main():
    opts = Options()
    driver = webdriver.Chrome(options=opts)

    with open('contracts.csv', 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['player', 'signed', 'expiration', 'years_remaining'])

        try:
            driver.get(URL)


            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="qc-cmp2-ui"]/div[2]/div/button[2]')
                )
            ).click()
  

            try:
                WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//*[@id="salaries_table"]/div[1]/div[3]/div[1]/div/div/div/a[3]')
                    )
                ).click()
            except Exception:
                pass

            scrape_current_league(driver, writer, csvfile)

            base_url = "https://www.capology.com"
            league_paths = []

            try:
                select_el = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "nav-menu"))
                )
                options = select_el.find_elements(By.TAG_NAME, "option")
                for opt in options:
                    val = opt.get_attribute("value") or ""
                    val = val.strip()
                    if not val:
                        continue
                    league_paths.append(val)
            except Exception:
                league_paths = []

            for path in league_paths:
                if path == "/de/1-bundesliga/salaries/":
                    continue

                full_url = base_url + path
                print(f"Parsing league: {full_url}")

                try:
                    driver.get(full_url)
                except Exception:
                    continue

                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '#table'))
                    )
                except Exception:
                    continue

                try:
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, '//*[@id="salaries_table"]/div[1]/div[3]/div[1]/div/div/div/a[3]')
                        )
                    ).click()
                except Exception:
                    pass

                try:
                    scrape_current_league(driver, writer, csvfile)
                except Exception:
                    continue

        finally:
            driver.quit()

if __name__ == "__main__":
    main()
