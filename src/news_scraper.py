import os
import time
import re
import urllib.request
import pandas as pd
import logging

from datetime import datetime
from RPA.Browser.Selenium import Selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NewsScraper:
    def __init__(self, site_url, search_phrase, category, months, headless=True):
        self.browser = Selenium()
        self.site_url = site_url
        self.search_phrase = search_phrase
        self.category = category
        self.months = months
        self.headless = headless
        self.output_dir = self.create_output_directory()
        self.images_dir = os.path.join(self.output_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
        logging.info("Initialized NewsScraper with URL: %s, Search Phrase: %s, Category: %s, Months: %d", 
                     site_url, search_phrase, category, months)
        
    def create_output_directory(self):
        # Create a unique folder based on the category and current UTC timestamp
        category_prefix = self.category.upper().replace(" ", "_")
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        output_dir = os.path.join("output", f"{category_prefix}_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)
        logging.info("Created output directory: %s", output_dir)
        return output_dir
        
    def open_site(self):
        options = {
            "arguments": [
                "--headless", 
                "--disable-gpu", 
                "--window-size=1920,1080", 
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ] if self.headless else []
        }
        logging.info("Opening site: %s with headless mode: %s", self.site_url, self.headless)
        self.browser.open_available_browser(self.site_url, options=options)
        
    def filter_news_by_category(self):
        if self.category:
            logging.info("Filtering news by category: %s", self.category)
            category_locator = f"//span[text()='{self.category}']"  # Removed "xpath:" prefix
            
            retry_attempts = 3
            for attempt in range(retry_attempts):
                try:
                    logging.info(f"Attempt {attempt + 1} to locate category element.")
                    WebDriverWait(self.browser.driver, 30).until(
                        EC.visibility_of_element_located((By.XPATH, category_locator))
                    )

                    if self.browser.is_element_visible(category_locator):
                        self.browser.click_element(category_locator)

                        # Wait for the page to reload with the filtered category
                        WebDriverWait(self.browser.driver, 30).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "h3"))
                        )
                        logging.info("Category filtered successfully.")
                        return  # Exit the method after successful category selection
                    else:
                        logging.warning(f"Category '{self.category}' not visible, retrying...")
                except Exception as e:
                    logging.error(f"Error on attempt {attempt + 1}: {e}")
                    if attempt == retry_attempts - 1:
                        logging.error("Max retry attempts reached. Taking a screenshot for debugging.")
                        screenshot_path = os.path.join(self.output_dir, f'error_screenshot_attempt_{attempt + 1}.png')
                        self.browser.capture_page_screenshot(screenshot_path)
                        raise ValueError(f"Category '{self.category}' not found on the site after {retry_attempts} attempts.")
            raise ValueError(f"Failed to locate category '{self.category}' after {retry_attempts} attempts.")
    
    # Yahoo open searchs on new tabs, unused for now.
    # def search_news(self):
    #    logging.info("Searching for news with phrase: %s", self.search_phrase)
    #    search_box = self.browser.get_webelement(locator="id:ybar-sbq")
    #    self.browser.input_text(search_box, self.search_phrase)
    #    self.browser.press_keys(search_box, "ENTER")
    
    def scroll_and_load(self):
        logging.info("Scrolling and loading news articles...")
        articles = []
        previous_count = 0
        
        while len(articles) < 20:
            self.browser.execute_javascript("window.scrollBy(0, document.body.scrollHeight/3);")
            time.sleep(4)  # Wait for content to load
            
            articles = self.browser.get_webelements(locator="css:li.stream-item")
            logging.info("Loaded %d articles...", len(articles))

            if len(articles) == previous_count:
                logging.info("No more articles loaded, exiting scroll loop.")
                break
            
            previous_count = len(articles)

        return articles[:20]  # Return only the first 20 items
    
    def extract_image_url(self, article):
        try:
            image_element = article.find_element(By.CSS_SELECTOR, "img")
            image_url = image_element.get_attribute("src")
            logging.info("Extracted image URL: %s", image_url)
            return image_url
        except Exception as e:
            logging.error("Failed to extract image URL: %s", e)
            return None

    def extract_news_data(self):
        logging.info("Extracting news data...")
        articles = self.scroll_and_load()
        
        news_data = []
        for article in articles:
            try:
                title_element = article.find_element(By.CSS_SELECTOR, "h3.stream-item-title")
                
                # Use WebDriverWait to wait for the description to be present
                description_element = WebDriverWait(article, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "p[data-test-locator='stream-item-summary']"))
                )
                
                image_url = self.extract_image_url(article)
                
                news_item = {
                    "title": title_element.text,
                    "description": description_element.text if description_element else "No description available",
                    "date": time.strftime("%Y-%m-%d"),
                    "picture_filename": self.download_image(image_url, title_element.text),
                    "money_mentioned": self.check_for_money(title_element.text, description_element.text if description_element else ""),
                    "search_phrase_count": self.search_phrase_count(title_element.text, description_element.text if description_element else "")
                }
                news_data.append(news_item)
                logging.info("Extracted news item: %s", news_item)
            except Exception as e:
                logging.error("Error extracting article: %s", e)

        return news_data
    
    def check_for_money(self, title, description):
        money_patterns = [r"\$\d[\d,.]*", r"\d+\s*(dollars|USD)"]
        for pattern in money_patterns:
            if re.search(pattern, title) or re.search(pattern, description):
                logging.info("Money mentioned in article with title: %s", title)
                return True
        return False
    
    def search_phrase_count(self, title, description):
        count = title.lower().count(self.search_phrase.lower()) + description.lower().count(self.search_phrase.lower())
        logging.info("Search phrase count in title '%s' and description '%s': %d", title, description, count)
        return count
    
    def download_image(self, image_url, title):
        if not image_url:
            return "placeholder.png"

        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            title_sanitized = re.sub(r'\W+', '', title[:15])
            category_prefix = self.category.upper().replace(" ", "_")
            image_filename = f"{category_prefix}_{title_sanitized}_{timestamp}.jpg"
            image_path = os.path.join(self.images_dir, image_filename)

            urllib.request.urlretrieve(image_url, image_path)
            logging.info("Downloaded image to: %s", image_path)

            return image_filename
        except Exception as e:
            logging.error("Failed to download image: %s", e)
            return "placeholder.png"
    
    def save_to_excel(self, news_data):
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        category_prefix = self.category.upper().replace(" ", "_")
        file_name = os.path.join(self.output_dir, f"{category_prefix}_news_data_{timestamp}.xlsx")
        df = pd.DataFrame(news_data)
        df.to_excel(file_name, index=False)
        logging.info("Data saved to %s", file_name)
        self.save_scrape_log(news_data, file_name)
    
    def save_scrape_log(self, news_data, file_name):
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        category_prefix = self.category.upper().replace(" ", "_")
        log_filename = os.path.join(self.output_dir, f"{category_prefix}_scrape_log_{timestamp}.txt")
        try:
            with open(log_filename, 'w') as log_file:
                log_file.write(f"Scraping Report - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
                log_file.write(f"URL: {self.site_url}\n")
                log_file.write(f"Category: {self.category}\n")
                log_file.write(f"Search Phrase: {self.search_phrase}\n")
                log_file.write(f"Excel File: {file_name}\n\n")
                log_file.write("Extracted News Articles:\n")
                for news_item in news_data:
                    log_file.write(f"- Title: {news_item['title']}\n")
                    log_file.write(f"  Description: {news_item['description']}\n")
                    log_file.write(f"  Date: {news_item['date']}\n")
                    log_file.write(f"  Picture Filename: {news_item['picture_filename']}\n")
                    log_file.write(f"  Money Mentioned: {news_item['money_mentioned']}\n")
                    log_file.write(f"  Search Phrase Count: {news_item['search_phrase_count']}\n\n")
            logging.info("Scraping log saved to: %s", log_filename)
        except Exception as e:
            logging.error("Failed to save scraping log: %s", e)
    
    def close(self):
        logging.info("Closing all browsers...")
        self.browser.close_all_browsers()
