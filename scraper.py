import re
import time
import yaml
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


# --- Corrected Scraper for Devpost (using Selenium) ---
def scrape_devpost():
    """
    Fetches hackathon data from Devpost using Selenium to handle
    dynamically loaded content.
    """
    url = "https://devpost.com/hackathons?challenge_type=online&status[]=upcoming&status[]=open"
    hackathons = []

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Path to your chromedriver executable
    # If chromedriver is in your project folder, you can use './chromedriver'
    service = Service(executable_path='./chromedriver')

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        time.sleep(5)  # Wait for the page's JavaScript to load content

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        for tile in soup.find_all('div', class_='hackathon-tile'):
            link_element = tile.find('a', href=True)
            title_element = tile.find('h3')

            if link_element and title_element:
                hackathons.append({
                    'title': title_element.get_text(strip=True),
                    'link': link_element['href'],
                    'location': 'Online',
                    'startDate': None,
                    'endDate': None,
                    'mode': 'Online',
                    'source': 'https://devpost.com'
                })
        return hackathons
    except Exception as e:
        print(f"Error scraping Devpost: {e}")
        return []
    finally:
        if driver:
            driver.quit()


# --- Corrected Scraper for HackaTrack (using Selenium) ---
def scrape_hackatrack():
    """
    Fetches hackathon data from HackaTrack using Selenium.
    """
    url = "https://www.hackatrack.net/"
    hackathons = []

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(executable_path='./chromedriver')

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        for card_link in soup.find_all('a', class_='MuiLink-root'):
            title_element = card_link.find('h3')
            location_icon = card_link.find('svg', {'data-testid': 'PlaceIcon'})
            date_icon = card_link.find('svg', {'data-testid': 'EventIcon'})

            if not all([title_element, location_icon, date_icon]):
                continue

            location = location_icon.find_next_sibling('p').get_text(strip=True)
            dates = date_icon.find_next_sibling('p').get_text(strip=True)
            link = card_link.get('href', '')

            hackathons.append({
                'title': title_element.get_text(strip=True),
                'link': link,
                'location': location,
                'startDate': dates,
                'endDate': None,
                'mode': 'In-Person',
                'source': 'https://www.hackatrack.net'
            })
        return hackathons
    except Exception as e:
        print(f"Error scraping HackaTrack: {e}")
        return []
    finally:
        if driver:
            driver.quit()

# yaml or markdown scrapers
def scrape_hackathon_directory():
    """
    Fetches and parses hackathon data from the hackathon-directory's
    public YAML file on GitHub using the correct keys.
    """
    url = "https://raw.githubusercontent.com/imbjdd/hackathon-directory/main/data/hackathons.yml"
    hackathons = []

    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()

        # Use yaml.safe_load() to parse the YAML content
        data = yaml.safe_load(response.text)

        for item in data:
            hackathons.append({
                'title': item.get('name'),
                'link': item.get('website'),  # Correct key is 'website'
                'startDate': item.get('date'),  # Correct key is 'date'
                'endDate': None,  # This source provides a single date string
                'location': item.get('location'),
                'mode': item.get('category'),  # Using 'category' for mode is a good approximation
                'source': 'https://hackathon-directory.vercel.app/'
            })

        return hackathons
    except requests.RequestException as e:
        print(f"Error fetching Hackathon Directory YAML: {e}")
        return []
    except yaml.YAMLError as e:
        print(f"Error parsing YAML from Hackathon Directory: {e}")
        return []

def scrape_euro_hackathons():
    """
    Fetches hackathon data by parsing the Markdown table in the
    Euro-Hackathons README.md file from GitHub.
    """
    url = "https://raw.githubusercontent.com/lorenzopalaia/Euro-Hackathons/main/README.md"
    hackathons = []

    # Regex to find and extract components from a Markdown link: [text](url)
    link_regex = re.compile(r"\[(.*?)]\((.*?)\)")

    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()

        readme_content = response.text

        # Isolate the "Upcoming Hackathons" table
        try:
            table_section = \
            readme_content.split('<!-- UPCOMING_TABLE_START -->')[1].split('<!-- UPCOMING_TABLE_END -->')[0]
        except IndexError:
            print("Could not find the upcoming hackathons table in the README.")
            return []

        # Process each line in the isolated table section
        lines = table_section.splitlines()

        for line in lines:
            # Skip header, separator, or empty lines
            if not line.strip().startswith('|') or "|---" in line or "Hackathon Name" in line:
                continue

            # Split the table row into columns
            columns = [col.strip() for col in line.split('|')[1:-1]]

            if len(columns) < 5:
                continue

            name_cell, location, date, topics, url_cell = columns

            # Extract title and link from their respective cells
            name_match = link_regex.search(name_cell)
            url_match = link_regex.search(url_cell)

            # A valid entry must have both a name and a URL link
            if not (name_match and url_match):
                # Sometimes the name is plain text, but the URL cell has the link
                if url_match:
                    title = name_cell
                    link = url_match.groups()[1]
                else:
                    continue  # Skip row if no link is found
            else:
                title = name_match.groups()[0]
                link = url_match.groups()[1]

            hackathons.append({
                'title': title,
                'link': link,
                'location': location,
                'startDate': date,
                'endDate': None,
                'mode': topics if topics else 'General',
                'source': 'https://euro-hackathons.vercel.app/'
            })

        return hackathons
    except requests.RequestException as e:
        print(f"Error fetching Euro-Hackathons README: {e}")
        return []

def get_all_hackathons():
    """Aggregates results from all scraper functions."""
    print("Starting scrape...")
    all_hackathons = []

    all_hackathons.extend(scrape_hackatrack())
    all_hackathons.extend(scrape_devpost())
    all_hackathons.extend(scrape_hackathon_directory())
    all_hackathons.extend(scrape_euro_hackathons())

    print(f"Scraping complete. Found {len(all_hackathons)} total entries.")
    return all_hackathons