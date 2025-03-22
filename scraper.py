import requests
import json
import os
import logging
import time
import random
from bs4 import BeautifulSoup
from HTML_processing import process_article_html
from category_finder import fetch_arxiv_categories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("scraper.log"), logging.StreamHandler()]
)

ARXIV_BASE_URL = 'https://arxiv.org/list/'
ARXIV_HTML_BASE_URL = 'https://arxiv.org/html/'


#prompt user for either specific categories or random papers.
def prompt_categories_and_papers():
    categories_dict = {}

    categories_input = input("Enter categories and paper counts (category1:<total_papers>, category2:<total_papers>, 'random:<total_papers>', or 'single:<paper_id>') --> ").strip()

    #check if the user entered a single paper ID
    if categories_input.startswith("single:"):
        paper_id = categories_input.split(":")[1].strip()
        scrape_single_paper(paper_id)
        exit()  #exit after running the test

    if categories_input.startswith("random:"):
        try:
            total_papers = int(categories_input.split(":")[1].strip())
            all_categories = fetch_arxiv_categories()
            categories_dict = distribute_random_papers(total_papers, all_categories)
        except (IndexError, ValueError):
            print("Invalid random format. Use 'random:<number>'.")
            exit()
    else:
        for entry in categories_input.split(","):
            try:
                category, count = entry.split(":")
                categories_dict[category.strip()] = int(count.strip())
            except ValueError:
                print(f"Invalid entry: {entry.strip()}")
                exit()

    return categories_dict

def scrape_single_paper(paper_id):
    html_url = f"{ARXIV_HTML_BASE_URL}{paper_id}"
    data_filename = f"single_test_{paper_id}.json"

    existing_data = {}

    logging.info(f"Scraping single paper: {paper_id}")
    
    try:
        processed_data = process_article_html(paper_id, html_url, existing_data)

        if paper_id in processed_data:
            save_to_json(data_filename, processed_data)
            print(f"Successfully scraped and saved '{paper_id}' to '{data_filename}'.")
        else:
            print(f"No content extracted from '{paper_id}'. Possible empty page or bad HTML.")

    except Exception as e:
        logging.error(f"Failed to process single paper '{paper_id}': {e}")


#random papers across fetched categories
def distribute_random_papers(total_papers, all_categories):
    categories_dict = {}
    remaining_papers = total_papers
    shuffled_categories = random.sample(all_categories, len(all_categories))

    while remaining_papers > 0:
        for category in shuffled_categories:
            if remaining_papers <= 0:
                break
            num_papers = random.randint(1, min(remaining_papers, 10))
            categories_dict[category] = categories_dict.get(category, 0) + num_papers
            remaining_papers -= num_papers

    return categories_dict

#prompt user to ask for dataset selection
def prompt_dataset_filename():
    filename = input("Enter dataset filename (ie. my_dataset.json): ").strip()
    if not filename.endswith('.json'):
        filename += '.json'
    return filename


def load_existing_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_to_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def prompt_file_mode(dataFileName):
    if os.path.exists(dataFileName):
        action = input(f"File '{dataFileName}' exists. Overwrite (O) or Append (A)? ").strip().lower()
        if action == 'o':
            return {}
        elif action == 'a':
            return load_existing_json(dataFileName)
        else:
            print("Invalid choice.")
            exit()
    else:
        return {}


def generate_category_urls(category, max_papers):
    urls = []
    for start in range(0, max_papers, 25):
        urls.append(f"{ARXIV_BASE_URL}{category}/pastweek?skip={start}&show=25")
    return urls


def fetch_article_ids(url):
    response = requests.get(url)
    if response.status_code != 200:
        logging.error(f"Failed to get category page: {url}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    return [a['href'].split('/')[-1] for a in soup.find_all('a', title='Abstract')]


def scrape_category(category, max_papers, existing_data, dataFileName):
    urls = generate_category_urls(category, max_papers)
    article_count = 0  #number of successfully added papers
    skipped_empty = 0  #track how many papers were skipped due to empty content

    for url in urls:
        article_ids = fetch_article_ids(url)

        for article_id in article_ids:
            if article_id in existing_data:
                logging.info(f"Skipping {article_id} - already present in this dataset")
                continue

            html_url = f"{ARXIV_HTML_BASE_URL}{article_id}"
            logging.info(f"Scraping {html_url}")

            try:
                temp_data = process_article_html(article_id, html_url, existing_data)

                #check if content was actually added
                if article_id in temp_data:
                    existing_data = temp_data  #update if content was added
                    article_count += 1          #count only successful scrapes
                    save_to_json(dataFileName, existing_data)
                else:
                    skipped_empty += 1  #track skipped empty papers
                    logging.warning(f"Skipping {article_id}: empty content - bad HTML.")

                #stop if max papers reached
                if article_count >= max_papers:
                    logging.info(f"Reached max_papers limit ({max_papers}) for '{category}'.")
                    if skipped_empty > 0:
                        print(f"{skipped_empty} papers were skipped due to empty content.")
                    return existing_data

                sleep_time = random.uniform(2, 6)
                time.sleep(sleep_time)

            except Exception as e:
                logging.error(f"Failed to process {html_url}: {e}")

    logging.info(f"Scraping for category '{category}' done.")
    if skipped_empty > 0:
        print(f"{skipped_empty} papers were skipped due to empty content.")
    
    return existing_data



if __name__ == "__main__":
    categories = prompt_categories_and_papers()
    dataFileName = prompt_dataset_filename()

    existing_data = prompt_file_mode(dataFileName)

    for category, max_papers in categories.items():
        logging.info(f"Starting scrape for category: {category} with {max_papers} papers.")
        existing_data = scrape_category(category, max_papers, existing_data, dataFileName)

    logging.info("Scrapping done.")


