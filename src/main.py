from news_scraper import NewsScraper
from utils import get_config

def main():
    config = get_config()
    scraper = NewsScraper(
        site_url=config["site_url"],
        search_phrase=config["search_phrase"],
        category=config["category"],
        months=config["months"],
        headless=config.get("headless", True)
    )
    
    scraper.open_site()
    scraper.filter_news_by_category()
    # Yahoo open searchs on new tabs, unused for now.
    # scraper.search_news()
    news_data = scraper.extract_news_data()
    scraper.save_to_excel(news_data)
    scraper.close()
    
if __name__ == "__main__":
    main()
