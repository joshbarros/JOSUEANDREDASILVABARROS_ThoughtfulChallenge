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
        
        # Use a single timestamp for the entire session to avoid multiple directories
        self.timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        self.output_dir = self.create_output_directory()
        self.images_dir = os.path.join(self.output_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
        logging.info("Initialized NewsScraper with URL: %s, Search Phrase: %s, Category: %s, Months: %d", 
                     site_url, search_phrase, category, months)
        
    def create_output_directory(self):
        category_prefix = self.category.upper().replace(" ", "_")
        output_dir = os.path.join("output", f"{category_prefix}_{self.timestamp}")
        
        if not os.path.exists(output_dir):
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
            try:
                # Find all the list items in the navbar
                categories = self.browser.get_webelements("css:ul._yb_c8hmf2 li")
                
                # Iterate over each category and check the text
                for category in categories:
                    span_element = category.find_element(By.CSS_SELECTOR, "span._yb_5tqys3")
                    if span_element.text.strip().lower() == self.category.lower():
                        logging.info(f"Found category '{self.category}', clicking it now.")
                        span_element.click()
                        
                        # Wait for the page to reload with the filtered category
                        WebDriverWait(self.browser.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "h3"))
                        )
                        return
                raise ValueError(f"Category '{self.category}' not found.")
            except Exception as e:
                logging.error(f"Error during category selection: {e}")
                screenshot_path = os.path.join(self.output_dir, 'error_screenshot.png')
                self.browser.capture_page_screenshot(screenshot_path)
                raise
    
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
            title_sanitized = re.sub(r'\W+', '', title[:15])
            category_prefix = self.category.upper().replace(" ", "_")
            image_filename = f"{category_prefix}_{title_sanitized}_{self.timestamp}.jpg"
            image_path = os.path.join(self.images_dir, image_filename)

            urllib.request.urlretrieve(image_url, image_path)
            logging.info("Downloaded image to: %s", image_path)

            return image_filename
        except Exception as e:
            logging.error("Failed to download image: %s", e)
            return "placeholder.png"
    
    def save_to_excel(self, news_data):
        category_prefix = self.category.upper().replace(" ", "_")
        file_name = os.path.join(self.output_dir, f"{category_prefix}_news_data_{self.timestamp}.xlsx")
        df = pd.DataFrame(news_data)
        df.to_excel(file_name, index=False)
        logging.info("Data saved to %s", file_name)
        self.save_scrape_log(news_data, file_name)
    
    def save_scrape_log(self, news_data, file_name):
        log_filename = os.path.join(self.output_dir, f"{self.category.upper().replace(' ', '_')}_scrape_log_{self.timestamp}.txt")
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
