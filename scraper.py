# scraper.py
import yaml
import requests
from bs4 import BeautifulSoup


def scrape_hackatrack():
    url = "https://www.hackatrack.net/"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        hackathons = []
        # Inspecting the site reveals each event is in a 'div' with these classes
        for card in soup.find_all('div', class_='col-lg-6 col-md-6'):
            title_element = card.find('h3', class_='card-title')
            link_element = card.find('a', class_='btn-primary')  # The "details" button

            if title_element and link_element and link_element.has_attr('href'):
                hackathons.append({
                    'title': title_element.get_text(strip=True),
                    'link': "https://www.hackatrack.net" + link_element['href'],  # Link is relative
                    'source': 'HackaTrack'
                })
        return hackathons
    except requests.RequestException as e:
        print(f"Error scraping HackaTrack: {e}")
        return []


def scrape_hackathon_directory():
    """
    Fetches hackathon data directly from the hackathon-directory's
    public YAML file on GitHub.
    """
    url = "https://raw.githubusercontent.com/imbjdd/hackathon-directory/main/data/hackathons.yml"
    hackathons = []

    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()

        # Use yaml.safe_load() to parse the YAML content
        data = yaml.safe_load(response.text)

        # The YAML file is a list of hackathon objects
        for item in data:
            # We add extra details to our returned dictionary
            hackathons.append({
                'title': item.get('name'),
                'link': item.get('url'),
                'startDate': item.get('startDate'),
                'endDate': item.get('endDate'),
                'location': item.get('location'),
                'mode': item.get('mode'),  # e.g., Online, Hybrid, In-Person
                'source': 'Hackathon Directory'
            })

        return hackathons
    except requests.RequestException as e:
        print(f"Error fetching Hackathon Directory YAML: {e}")
        return []
    except yaml.YAMLError as e:
        print(f"Error parsing YAML from Hackathon Directory: {e}")
        return []


def scrape_kontest():
    # This site provides a direct, public API!
    api_url = "https://kontests.net/api/v1/all"  # Note: URL from docs is slightly different
    try:
        response = requests.get(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        data = response.json()

        hackathons = []
        # Filtering for European-relevant platforms or keywords
        relevant_sites = {'CodeForces', 'TopCoder', 'AtCoder', 'CodeChef', 'HackerRank', 'HackerEarth', 'LeetCode'}
        for contest in data:
            if contest.get('site') in relevant_sites and 'hackathon' in contest.get('name').lower():
                hackathons.append({
                    'title': contest['name'],
                    'link': contest['url'],
                    'source': contest['site']
                })
        return hackathons
    except requests.RequestException as e:
        print(f"Error scraping Kontests API: {e}")
        return []


# In scraper.py

def scrape_euro_hackathons():
    """
    Fetches hackathon data by parsing the Markdown table in the
    Euro-Hackathons README.md file on GitHub.
    """
    url = "https://raw.githubusercontent.com/lorenzopalaia/Euro-Hackathons/main/README.md"
    hackathons = []

    # Regex to find Markdown links like [text](url)
    link_regex = re.compile(r"\[(.*?)\]\((.*?)\)")

    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()

        lines = response.text.splitlines()

        # Find the start of the table data
        # It begins 2 lines after the header row "Upcoming Hackathons"
        # and 1 line after the table separator "|---|---..."
        data_started = False
        for line in lines:
            # The separator line indicates that the next lines are data
            if "|---" in line:
                data_started = True
                continue

            if not data_started or not line.strip().startswith('|'):
                continue

            # Split the table row into columns
            columns = [col.strip() for col in line.split('|')[1:-1]]

            if len(columns) < 5:  # Ensure the row has enough columns
                continue

            name_cell, location, start_date, end_date, mode = columns

            # Extract title and link from the name cell
            match = link_regex.search(name_cell)
            if not match:
                continue  # Skip if there's no link

            title, link = match.groups()

            hackathons.append({
                'title': title,
                'link': link,
                'location': location if location != '🌍' else 'Online',
                'startDate': start_date,
                'endDate': end_date,
                'mode': mode,
                'source': 'Euro-Hackathons'
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
    all_hackathons.extend(scrape_euro_hackathons())
    all_hackathons.extend(scrape_hackathon_directory())  # <-- ADD THIS LINE

    print(f"Scraping complete. Found {len(all_hackathons)} total entries.")
    return all_hackathons