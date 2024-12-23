import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import re

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
            report_url = link['href']
            if report_url in visited_links:
                continue
            visited_links.add(report_url)
            print(f"Processing: {species_name} - {link.text.strip()} - {report_url}")
            if not report_url.startswith('http'):
                report_url = base_url + report_url
            try:
                report_html = fetch_html(report_url)
                report_data = parse_report_page(report_html)
                if species_name not in data_by_species:
                    data_by_species[species_name] = []
                data_by_species[species_name].append({
                    "link_text": link.text.strip(),
                    "report_url": report_url,
                    "data": report_data
                })
            except Exception as e:
                print(f"Failed to process {report_url}: {e}")

    return data_by_species

def parse_report_page(html):
    """Parses the individual report page and extracts table data."""
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')

    report_data = []
    for table in tables:
        caption = table.find('caption').text.strip() if table.find('caption') else 'No Caption'
        rows = table.find_all('tr')
        headers = [th.text.strip() for th in rows[0].find_all('th')]

        table_data = []
        for row in rows[1:]:
            cells = [cell.text.strip() for cell in row.find_all(['td', 'th'])]
            table_data.append(cells)

        report_data.append({
            "caption": caption,
            "headers": headers,
            "rows": table_data
        })

    return report_data

def sanitize_filename(filename):
    """Sanitizes the filename by removing or replacing invalid characters."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def save_to_csv(data_by_species, output_dir):
    """Saves the extracted data to CSV files categorized by species."""
    os.makedirs(output_dir, exist_ok=True)

    for species, reports in data_by_species.items():
        species_dir = os.path.join(output_dir, sanitize_filename(species.replace(' ', '_')))
        os.makedirs(species_dir, exist_ok=True)
        aggregated_data = {}
        for report in reports:
            for table in report["data"]:
                category = sanitize_filename(report['link_text'].replace(' ', '_'))
                if category not in aggregated_data:
                    aggregated_data[category] = {"headers": table["headers"], "rows": []}
                aggregated_data[category]["rows"].extend(table["rows"])

        for category, data in aggregated_data.items():
            filename = os.path.join(species_dir, f"{category}.csv")
            headers = data["headers"]
            rows = [row[:len(headers)] + [''] * (len(headers) - len(row)) for row in data["rows"]]
            df = pd.DataFrame(rows, columns=headers)
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