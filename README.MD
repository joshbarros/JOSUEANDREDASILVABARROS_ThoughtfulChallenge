# Yahoo News Scraper Application

This Yahoo News Scraper is an RPA (Robotic Process Automation) application built using Python and Selenium. The app scrapes news articles from Yahoo News, filters them by category, searches for a specific phrase, and extracts relevant information, including titles, descriptions, images, and more. The extracted data is saved into an Excel file along with the downloaded images. The application is configurable, allowing you to specify the search phrase, news category, and whether to run the browser in headless mode.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Output](#output)
- [Logs](#logs)
- [Contributing](#contributing)
- [License](#license)

## Features
- Scrape news articles from Yahoo News.
- Filter articles by category.
- Search for a specific phrase within the articles.
- Extract titles, descriptions, and images.
- Save extracted data into an Excel file.
- Download images into a structured folder system.
- Configurable headless mode for browser automation.
- Detailed logging of the entire scraping process.

## Prerequisites
- Python 3.10 or higher
- Pip (Python package installer)
- Virtual environment (optional but recommended)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/news-scraper.git
   cd news-scraper
   ```

2. **Set up a virtual environment (optional but recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The application is configured using a JSON file named `work-item.json`. This file contains the necessary parameters for the scraper to run.

### Example `work-item.json`:
```json
{
    "site_url": "https://news.yahoo.com",
    "search_phrase": "Biden",
    "category": "Politics",
    "months": 1,
    "headless": true  # Set to `false` if you want to see the browser in action
}
```

### Configuration Parameters:
- `site_url`: The URL of the site to scrape (default is Yahoo News).
- `search_phrase`: The phrase to search within the news articles.
- `category`: The news category to filter (e.g., Politics, World).
- `months`: Not used in the current implementation but could be extended for time-based filtering.
- `headless`: Boolean flag to determine if the browser should run in headless mode (`true` for headless, `false` to see the browser).

## Running the Application

1. Ensure your `work-item.json` is correctly configured.
2. Run the application with the following command:
   ```bash
   python ./src/main.py
   ```

## Output

The application will create an output directory under `output/{timestamp}/` where `{timestamp}` is the UTC time when the scraper was run. The directory structure will look like this:

```
output/
└── 20240823180355/
    ├── images/
    │   ├── image_1.jpg
    │   ├── image_2.jpg
    │   └── ...
    ├── news_data_20240823180355.xlsx
    └── scraper_log_20240823180355.txt
```

- **images/**: Contains all downloaded images from the news articles.
- **news_data_YYYYMMDDHHMMSS.xlsx**: Excel file with the extracted data.
- **scraper_log_YYYYMMDDHHMMSS.txt**: Log file detailing the scraping process.

## Logs

All significant actions, errors, and warnings are logged in a log file stored in the output directory. This log file provides a detailed trace of the application’s execution, which is valuable for debugging or verifying the scraping process.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
