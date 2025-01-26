import requests
from bs4 import BeautifulSoup
import json
import pdfplumber
from io import BytesIO
import time
import random

print('--- ARXIVE scraping starting ---')

#arxive urls for getting the articles
ARXIV_BASE_URL = 'https://arxiv.org/list/'
ARXIV_ABS_BASE_URL = 'https://arxiv.org/abs/'

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

#fetch the HTML content of a page by url / if connection unsuccesful (!=200) - print the status code
def fetch_page_content(url,category):
    print(f">> Fetching content from: {url} (New Page for {category}) <<")
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch page content. Status code: {response.status_code}")
        return None

#fetch the pdf content from arxiv pdf url and extract its text using pdfplumber lib
#also have a counter just better readability of the process in terminal
def fetch_pdf_content(url, counter):
    print(f"Fetching PDF content from: {url} (Article {counter})")
    response = requests.get(url)
    if response.status_code == 200:
        try:
            with pdfplumber.open(BytesIO(response.content)) as pdf:
                pages = [page.extract_text() for page in pdf.pages if page.extract_text()]
                text = ' '.join(pages)
                text = text.replace('\n', ' ')  #attempt to handle whitespace
            return text
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
        article_counter = 1  #article counter for each category

        for url in urls:
            page_content = fetch_page_content(url,category)
            if page_content:
                article_ids = extract_article_ids(page_content)
                for article_id in article_ids:
                    if article_counter > max_results:
                        break  #stop once the max results for the category is hit

                    pdf_url = f"https://arxiv.org/pdf/{article_id}.pdf"
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
categories = {'stat': 50, 'cs': 50, 'math': 50} # CHANGE ACCORDINGLY

data = scrape_data(categories, categories)
print('--- ARXIVE scraping done ---')

#once all data is scrapped, save it to a json file

print('>> Saving data to arxive_data.json <<')
with open('arxive_data.json', 'w') as f:
    json.dump(data, f, indent=4)
print('>> Data saved successfully <<')

