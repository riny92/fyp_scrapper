
import requests
from bs4 import BeautifulSoup

def fetch_arxiv_categories():
    url = "https://arxiv.org/category_taxonomy"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    categories = []

    for div in soup.find_all("div", class_="column is-one-fifth"):
        h4 = div.find("h4")
        if h4:
            category_code = h4.contents[0].strip()  
            if category_code:
                categories.append(category_code)

    return categories

if __name__ == "__main__":
    categories = fetch_arxiv_categories()
    if categories:
        print(f"Found {len(categories)} categories:")
        for cat in categories:
            print(cat)
    else:
        print("No categories found.")
