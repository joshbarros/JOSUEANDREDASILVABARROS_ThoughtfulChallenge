import unittest
from news_scraper import NewsScraper
from unittest.mock import patch

class TestNewsScraper(unittest.TestCase):
    @patch('news_scraper.NewsScraper.open_site')
    @patch('news_scraper.NewsScraper.filter_news_by_category')
    @patch('news_scraper.NewsScraper.extract_news_data')
    @patch('news_scraper.NewsScraper.save_to_excel')
    @patch('news_scraper.NewsScraper.close')
    def test_categories(self, mock_close, mock_save_to_excel, mock_extract_news_data, mock_filter_news_by_category, mock_open_site):
        # List of categories to test
        categories = [
            "Today's news", "US", "Politics", "2024 Election", "DNC 2024",
            "World", "Health", "Science", "Originals", "The 360", "Weather Guide"
        ]

        # Iterate over each category and run the bot
        for category in categories:
            with self.subTest(category=category):
                scraper = NewsScraper(
                    site_url="https://news.yahoo.com",
                    search_phrase="test",
                    category=category,
                    months=1
                )

                # Mock methods to avoid actual web scraping during tests
                mock_extract_news_data.return_value = []
                scraper.open_site()
                scraper.filter_news_by_category()
                news_data = scraper.extract_news_data()
                scraper.save_to_excel(news_data)
                scraper.close()

                # Verify that the methods were called
                mock_open_site.assert_called_once()
                mock_filter_news_by_category.assert_called_once()
                mock_extract_news_data.assert_called_once()
                mock_save_to_excel.assert_called_once()
                mock_close.assert_called_once()

                # Reset mocks for the next iteration
                mock_open_site.reset_mock()
                mock_filter_news_by_category.reset_mock()
                mock_extract_news_data.reset_mock()
                mock_save_to_excel.reset_mock()
                mock_close.reset_mock()

if __name__ == "__main__":
    unittest.main()
