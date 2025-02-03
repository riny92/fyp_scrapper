##-----
# pymupdf PDF processing
import requests
from bs4 import BeautifulSoup
import json
import fitz  # PyMuPDF
from io import BytesIO
import time
import random
import re  

print('--- ARXIV PDF Scraping Starting ---')

#arxive urls for getting the articles
ARXIV_BASE_URL = 'https://arxiv.org/list/'
ARXIV_ABS_BASE_URL = 'https://arxiv.org/abs/'
ARXIV_PDF_BASE_URL = 'https://arxiv.org/pdf/'

#generate a list of urls to get articles from a specific category over the past week
#show 25 results/page, then move to next page
def generate_urls(category, max_results):
    urls = []
    for start in range(0, max_results, 25):  
        url = f"{ARXIV_BASE_URL}{category}/pastweek?skip={start}&show=25"
        urls.append(url)
    return urls

#extract ids from the HTML of a given page
def extract_article_ids(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    ids = [a['href'].split('/')[-1] for a in soup.find_all('a', title='Abstract')]
    return ids

#fetch the HTML content of a page by url / if connection unsuccesful (!=200) - none
def fetch_page_content(url, category):
    print(f">> Fetching content from: {url} (New Page for {category}) <<")
    response = requests.get(url)
    return response.text if response.status_code == 200 else None

#clean extracted pdf text - handle \n's and whitespaces
def clean_text(text):
    text = text.replace("\n", " ")  
    text = re.sub(r'\s+', ' ', text)  
    return text.strip()  

#fetch / process the pdf content using pymupdf 
def fetch_pdf_content(url, counter):
    print(f"Fetching PDF content from: {url} (Article {counter})")
    response = requests.get(url)
    if response.status_code == 200:
        try:
            pdf_document = fitz.open(stream=BytesIO(response.content), filetype="pdf")
            text = "\n".join(page.get_text("text") for page in pdf_document if page.get_text("text"))
            return clean_text(text)  # Clean and format extracted text
        except Exception as e:
            print(f"Error processing (Article {counter}): {e}")
            return "Error in processing pdf"
    else:
        print(f"Failed to fetch pdf due to HTTP status: {response.status_code}")
        return "Failed to fetch pdf"

#scrap metadata from the article abstract url - title, authors, and summary
def fetch_metadata(article_id):
    url = ARXIV_ABS_BASE_URL + article_id
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('h1', class_='title').text.replace('Title:', '').strip()
        author_section = soup.find('div', class_='authors')
        authors = [a.text for a in author_section.find_all('a')] if author_section else []
        summary = soup.find('blockquote', class_='abstract').text.replace('Abstract:', '').strip()
        return title, authors, summary
    else:
        print(f"Failed to fetch metadata due to HTTP status: {response.status_code}")
        return None, None, None

#main function to put everything together and scrape the final data
def scrape_data(categories, max_results_per_category):
    all_data = []
    for category, max_results in max_results_per_category.items():
        urls = generate_urls(category, max_results)
        article_counter = 1

        for url in urls:
            page_content = fetch_page_content(url, category)
            if page_content:
                article_ids = extract_article_ids(page_content)
                for article_id in article_ids:
                    if article_counter > max_results:
                        break

                    pdf_url = f"{ARXIV_PDF_BASE_URL}{article_id}.pdf"
                    title, authors, summary = fetch_metadata(article_id)
                    pdf_content = fetch_pdf_content(pdf_url, article_counter)

                    all_data.append({
                        'category': category,
                        'article_id': article_id,
                        'name of paper': title,
                        'author(s)': authors,
                        'summary': summary,
                        'label': 'human',
                        'URL': ARXIV_ABS_BASE_URL + article_id,
                        'PDF URL': pdf_url,
                        'contents': pdf_content
                    })

                    time.sleep(random.randint(2, 6))  #have a random delay between queries to not get ip banned by arxive
                    article_counter += 1
            else:
                print(f"No content retrieved from URL: {url}")
    return all_data

#arxive categories and the number of results to be scrapped (hardcoded for now - to be changable by user via terminal prompt later)
categories = {'stat': 6, 'cs': 5, 'math': 4}

data = scrape_data(categories, categories)
print('--- ARXIV Scraping Done ---')

#once all data is scrapped, save it to a json file

print('>> Saving data to arxive_data_test.json <<')
with open('../data/arxive_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
print('>> Data Saved Successfully <<')
# ----

