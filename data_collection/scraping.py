from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import time
import csv
import logging
from config import setup_logging


logger = logging.getLogger('scraping')
setup_logging()
logger.info("Начало работы")




URL = "https://www.capology.com/de/1-bundesliga/salaries/"

def scrape_current_league(driver, writer, csvfile):
    logger.info("Сбор данных для текущей лиги")
    while True:
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#table tbody tr'))
            )
            logger.info("Таблица загружена")
        except Exception:
            logger.error("Слишком долго ждем загрузки таблицы")
            return

        try:
            rows = driver.find_elements(By.CSS_SELECTOR, '#table tbody tr')
            logger.info(f"Найдено {len(rows)} строк")
        except StaleElementReferenceException:
            logger.error("Ошибка с StaleElementReferenceException при получении строк")
            continue

        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, 'td')
            except StaleElementReferenceException:
                logger.error("Ошибка с StaleElementReferenceException при получении ячеек, пропускаем строку")
                continue

            if len(cells) < 8:
                logger.error(f"Строка пропущена — недостаточно ячеек: {len(cells)}")
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
                logger.error("Ошибка с StaleElementReferenceException при получении данных ячеек, пропускаем строку")
                continue

            if not signed and not expiration and not years_remaining:
                logger.error(f"Нет данных о контракте для игрока: {name}, пропускаем строку")
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
            logger.info(f"Текущая страница: {current_page}, последняя страница: {last_page}")
            if current_page == last_page:
                logger.info("Последняя страница достигнута")
                break
        except StaleElementReferenceException:
            logger.error("Ошибка с StaleElementReferenceException при получении страниц, ретраю")
            continue
        except Exception:
            logger.error("Ошибка при получении страниц, пропускаем")
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
            logger.error("Не удалось перейти на следующую страницу, возможно, она недоступна")
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
                logger.info(f"Найдено {len(league_paths)} лиг")
            except Exception:
                logger.error("Ошибка при получении лиг")
                league_paths = []

            for path in league_paths:
                if path == "/de/1-bundesliga/salaries/":
                    continue

                full_url = base_url + path
                print(f"Parsing league: {full_url}")

                try:
                    driver.get(full_url)
                except Exception:
                    logger.error(f"Не удалось открыть лигу: {full_url}")
                    continue

                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '#table'))
                    )
                except Exception:
                    logger.error("Таблица лиги не найдена или не загружается")
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
                    logger.info(f"Сбор данных для лиги {full_url} завершен")
                except Exception:
                    logger.error(f"Ошибка при сборке данных для лиги {full_url}")
                    continue

        finally:
            driver.quit()

if __name__ == "__main__":
    main()
