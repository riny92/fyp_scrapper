import requests
import json
import time
import random

#query the API and handle pagination with scroll_id
def query_api(search_url, query, api_key, scroll_id=None):
    headers = {"Authorization": "Bearer " + api_key}
    params = {'q': query, 'limit': 100, 'scroll': 'true'}
    if scroll_id:
        params['scrollId'] = scroll_id

    response = requests.get(search_url, headers=headers, params=params)
    return response.json(), response.elapsed.total_seconds()


#handle scrolling to get papers stopping at (x) articles processed (can be changed)
def scroll(search_url, query, api_key, extract_info_callback):
    all_results = []
    count = 0
    scroll_id = None
    total_hits = 0

    while True:
        result, elapsed = query_api(search_url, query, api_key, scroll_id)
        scroll_id = result.get("scrollId")
        total_hits = result.get("totalHits", 0)
        result_size = len(result.get("results", []))

        if result_size == 0 or count >= 500:
            print(f"Reached limit of articles or no more results.")
            break

        for hit in result["results"]:
            all_results.append(extract_info_callback(hit))
            count += 1
            if count >= 500:
                break

        print(f"{count}/{total_hits} retrieved in {elapsed} seconds")
        # time.sleep(random.randint(2, 6))

    return all_results

#extract paper info and get structured data
def extract_info(hit):
    #text cleaning for whitespace/ new lines
    full_text = hit.get("fullText", "No full text available")
    clean_text = ' '.join(full_text.split())  

    return {
        'category': 'General',
        'article_id': hit.get("id"),
        'name of paper': hit.get("title"),
        'author(s)': [author.get("name") for author in hit.get("authors", [])],
        'summary': hit.get("abstract", "No abstract available"),
        'label': 'human',
        'URL': hit.get("urls", {}).get("canonicalUrl"),
        'PDF URL': hit.get("downloadUrl", "No PDF available"),
        'contents': clean_text
    }

api_key = ''  # api key
search_url = "https://api.core.ac.uk/v3/search/works" #api url
query = "_exists_:fullText"

#runner for scroller
papers_data = scroll(search_url, query, api_key, extract_info)

#save the data in json
with open('data/core_data.json', 'w') as f:
    json.dump(papers_data, f, indent=4)

print("Data saved successfully")


