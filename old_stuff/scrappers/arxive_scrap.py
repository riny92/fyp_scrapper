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
import unicodedata
from pylatexenc.latex2text import LatexNodes2Text
import ftfy

print('--- ARXIV PDF Scraping Starting ---')

#cleaning Functions
def decode_unicode(text):
    text = unicodedata.normalize("NFKC", text) 
    text = text.replace("ﬂ", "fl").replace("ﬁ", "fi")  
    text = text.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")  
    text = text.replace("−", "-").replace("—", "-").replace("–", "-")  
    text = text.replace("\xad", "")  
    text = re.sub(r'[\u200B\u2060\uFEFF]', '', text)  
    return text

def fix_word_splits(text):
    return re.sub(r"(\w+)-\s+(\w+)", r"\1\2", text)

def convert_latex_math(text):

    def replace_inline(match):
        latex_expr = match.group(1)
        try:
            return f"${LatexNodes2Text().latex_to_text(latex_expr)}$"
        except Exception:
            return match.group(0)

    def replace_block(match):
        latex_expr = match.group(1)
        try:
            return f"$$ {LatexNodes2Text().latex_to_text(latex_expr)} $$"
        except Exception:
            return match.group(0)

    text = re.sub(r"\\\((.*?)\\\)", replace_inline, text)
    text = re.sub(r"\\\[(.*?)\\\]", replace_block, text)

    text = text.replace(r"\phi", "φ").replace(r"\theta", "θ").replace(r"\alpha", "α").replace(r"\beta", "β")
    text = text.replace(r"\gamma", "γ").replace(r"\delta", "δ").replace(r"\lambda", "λ").replace(r"\mu", "μ")
    text = text.replace(r"\pi", "π").replace(r"\sigma", "σ").replace(r"\tau", "τ").replace(r"\Omega", "Ω")
    text = text.replace(r"\in", "∈").replace(r"\cdot", "·").replace(r"\times", "×").replace(r"\pm", "±")
    text = text.replace(r"\int", "∫").replace(r"\sum", "∑").replace(r"\prod", "∏").replace(r"\frac", "/")

    return text

def remove_control_characters(text):
    return re.sub(r"[\x00-\x1F\x7F-\x9F]", "", text)  


def clean_text(text):
    text = ftfy.fix_text(text)  
    text = fix_word_splits(text)  
    text = convert_latex_math(text)  

    text = text.replace('\"', '“').replace('\'', '’')  

    text = re.sub(r'\s+', ' ', text).strip()  
    return text



ARXIV_BASE_URL = 'https://arxiv.org/list/'
ARXIV_ABS_BASE_URL = 'https://arxiv.org/abs/'
ARXIV_PDF_BASE_URL = 'https://arxiv.org/pdf/'

def generate_urls(category, max_results):
    return [f"{ARXIV_BASE_URL}{category}/pastweek?skip={start}&show=25" for start in range(0, max_results, 25)]

def extract_article_ids(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    return [a['href'].split('/')[-1] for a in soup.find_all('a', title='Abstract')]

def fetch_page_content(url, category):
    print(f">> Fetching content from: {url} (New Page for {category}) <<")
    response = requests.get(url)
    return response.text if response.status_code == 200 else None

def fetch_pdf_content(url, counter):
    print(f"Fetching PDF content from: {url} (Article {counter})")
    response = requests.get(url)
    if response.status_code == 200:
        try:
            pdf_document = fitz.open(stream=BytesIO(response.content), filetype="pdf")
            text = "\n".join(page.get_text("text") for page in pdf_document if page.get_text("text"))
            return clean_text(text)  
        except Exception as e:
            print(f"Error processing (Article {counter}): {e}")
            return "Error in processing pdf"
    else:
        print(f"Failed to fetch pdf due to HTTP status: {response.status_code}")
        return "Failed to fetch pdf"




def fetch_metadata(article_id):
    url = ARXIV_ABS_BASE_URL + article_id
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('h1', class_='title').text.replace('Title:', '').strip()
        author_section = soup.find('div', class_='authors')
        authors = [a.text for a in author_section.find_all('a')] if author_section else []
        summary = soup.find('blockquote', class_='abstract').text.replace('Abstract:', '').strip()
        return clean_text(title), authors, clean_text(summary)  
    else:
        print(f"Failed to fetch metadata due to HTTP status: {response.status_code}")
        return None, None, None

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

                    time.sleep(random.randint(2, 6)) 
                    article_counter += 1
            else:
                print(f"No content retrieved from URL: {url}")
    return all_data

# categories = {'cs':1, 'econ':1,'q-bio':1, 'cs.AI':1, 'cs.CL':1}
categories = {'cs':1,'econ':1}
data = scrape_data(categories, categories)
print('--- ARXIV Scraping Done ---')

print('>> Saving data <<')
with open('../data/evaluation.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
print('>> Data Saved Successfully <<')
##-----
