import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def fetch_html(url):
    """Fetches the HTML content of a given URL."""
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.text

def parse_harvest_data(html, base_url):
    """Parses the HTML and extracts big game harvest data."""
    soup = BeautifulSoup(html, 'html.parser')
    data_by_species = {}
    visited_links = set()

    # Find all species sections
    species_sections = soup.find_all('h3')
    # Ensure the elements in species_sections are distinct
    species_sections = list(set(species_sections))
    for section in species_sections:
        species_name = section.text.strip()
        print(f"Processing species: {species_name}")
        links = section.find_next('ul').find_all('a')
        # Ensure the links are distinct
        links = list(set(links))

        for link in links:
            print(f"Processing: {species_name} - {link.text.strip()}")
            visited_links.add(link['href'])
            report_url = link['href']
            if not report_url.startswith('http'):
                report_url = base_url + report_url
            report_html = fetch_html(report_url)
            report_data = parse_report_page(report_html)
            data_by_species[species_name] = report_data

    return data_by_species

def parse_report_page(html):
    """Parses the individual report page and extracts table data."""
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')

    if not table:
        return {"headers": [], "rows": []}

    rows = table.find_all('tr')
    headers = [th.text.strip() for th in rows[0].find_all('th')]

    table_data = []
    for row in rows[1:]:
        cells = [cell.text.strip() for cell in row.find_all(['td', 'th'])]
        table_data.append(cells)

    return {
        "headers": headers,
        "rows": table_data
    }

def save_to_csv(data_by_species, output_dir):
    """Saves the extracted data to CSV files categorized by species."""
    os.makedirs(output_dir, exist_ok=True)

    for species, data in data_by_species.items():
        filename = os.path.join(output_dir, f"{species.replace(' ', '_')}.csv")
        df = pd.DataFrame(data["rows"], columns=data["headers"])
        df.to_csv(filename, index=False)
        print(f"Saved: {filename}")

def main():
    base_url = "https://wdfw.wa.gov"
    url = base_url + "/hunting/management/game-harvest#2023-harvest"
    output_dir = "wdfw_harvest_reports"

    print("Fetching HTML content...")
    html = fetch_html(url)

    print("Parsing harvest data...")
    data_by_species = parse_harvest_data(html, base_url)

    print("Saving data to CSV files...")
    save_to_csv(data_by_species, output_dir)

    print("All data saved successfully!")

if __name__ == "__main__":
    main()