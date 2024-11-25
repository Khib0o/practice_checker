link_string = "https://www.cm2.epss.jp/sendai/web/view/user/homeIndex.html"

from scrapy.crawler import CrawlerProcess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from scrapy.selector import Selector
import time, scrapy
import logging
import datetime
from datetime import timedelta
import re

logging.basicConfig(level=logging.ERROR)
pattern = r"(\d{4})年(\d{1,2})月"

def process_the_page(driver, file, date):
    
    # Locate all elements with a specific class (e.g., 'target-class')
    elements = driver.find_elements(By.CLASS_NAME, "tablebg2")  # Replace 'target-class' with your class

    # Iterate through the list of elements
    for element in elements:

        html_code = element.get_attribute('outerHTML')

        for testing in ["片平市民センター", "木町通市民センター"]:
            if testing in html_code:
                
                timings = element.find_elements(By.CLASS_NAME, "time-table2")  # Replace 'target-class' with your class
                count = 0
                for timing in timings:

                    timing_code = timing.get_attribute('outerHTML')
                    if "lw_rsvok" in timing_code:

                        if count == 0:
                            file.write(testing + " available morning of the "+date.strftime("%Y-%m-%d")+" ("+date.strftime("%A")+")\n")
                        if count == 1:
                            file.write(testing + " available afternoon of the "+date.strftime("%Y-%m-%d")+" ("+date.strftime("%A")+")\n")
                        if count == 2:
                            file.write(testing + " available evening of the "+date.strftime("%Y-%m-%d")+" ("+date.strftime("%A")+")\n")
                        
                    count += 1
                    

def find_date_elemn_in_calendar(calendar, tdate):

    calendar_html = calendar.get_attribute('outerHTML')
    numbers_of_clicks = 0

    year, month = 0 , 0
    matches = re.findall(pattern, calendar_html)
    for match in matches:
        year, month = match
        year = int(year)
        month = int(month)

    c = year * 12 + month
    t = tdate.year * 12 + tdate.month

    numbers_of_clicks = t - c

    if year == datetime.date.today().year and month == datetime.date.today().month and numbers_of_clicks!= 0:
        calendar.find_element(By.XPATH, "/html/body/div/form[2]/table/tbody/tr/td[1]/table[1]/tbody/tr[2]/td/div/span/table[1]/tbody/tr/td/div/a").click()
        time.sleep(0.5)
        numbers_of_clicks -= 1

    for i in range(abs(numbers_of_clicks)):

        t = calendar.find_element(By.XPATH, "/html/body/div/form[2]/table/tbody/tr/td[1]/table[1]/tbody/tr[2]/td/div/span/table[1]/tbody/tr/td/div/a[2]")
        print("MYDEBUG - not current so choosing second butt")
        t.click()
        time.sleep(0.5)

    schedule = calendar.find_element(By.LINK_TEXT, str(tdate.day)).click()
    

class SimpleSeleniumSpider(scrapy.Spider):
    name = "selenium_spider"
    start_urls = [link_string]  # Replace with your target URL

    

    def __init__(self):

        op = Options()
        op.add_argument("--headless")
        op.add_argument("--disable-gpu")
        op.add_argument("--disable-logging")

        op.add_argument("--disable-in-process-stack-traces")
        op.add_argument("--disable-crash-reporter")
        op.add_argument("--log-level=3")

        op.add_experimental_option("excludeSwitches", ["enable-logging"])
        


        ser = Service()
        ser.EnableVerboseLogging = False
        ser.SuppressInitialDiagnosticInformation = True
        ser.HideCommandPromptWindow = True


        # Initialize the WebDriver
        self.driver = webdriver.Chrome(service=ser, options=op)  # Replace with webdriver.Firefox() if using Firefox

    def parse(self, response):

        f = open("available_slots.txt", "w", encoding="utf-8")
        # Open the page with Selenium
        self.driver.get(response.url)
        time.sleep(2)  # Wait for the page to load fully

        link = self.driver.find_element(By.XPATH, "//a[@href='../user/rsvPurposeSearch.html']")
        link.click()  # Click the link
        time.sleep(1)  # Wait for the new page to load

        label = self.driver.find_element(By.XPATH, "//span[text()='バレーボール']")
        label.click()
        time.sleep(0.5)

        button = self.driver.find_element(By.XPATH, "//input[@value='上記の内容で検索する']")
        button.click()
        time.sleep(2)

        # Get the HTML source of the current page
        html_source = self.driver.page_source
        response = Selector(text=html_source)

        # Locate the specific table (Example using id='target-table')
        table = response.xpath('//table[@id="target-table"]')
        

        # Get today's date and the first day of the next month
        today = datetime.date.today()
        process_the_page(self.driver, f, today)
        first_day_next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)



        # Generate all dates from tomorrow to the end of the current month
        dates = []

        for i in range(31):
            today += timedelta(days=1)
            dates.append(today)



        for temp in dates:
            find_date_elemn_in_calendar(self.driver.find_element(By.XPATH, "/html/body/div/form[2]/table/tbody/tr/td[1]/table[1]"), temp)
            process_the_page(self.driver, f, temp)

        time.sleep(2)
        f.close

        

    def closed(self, reason):
        # Close the Selenium browser after scraping is done
        self.driver.quit()

# Run the spider
if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(SimpleSeleniumSpider)
    process.start()