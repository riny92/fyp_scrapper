#-------

import sys
import time
from openai import OpenAI
import json
import re
from dotenv import load_dotenv

load_dotenv()

#load article from json file
def load_article_data(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data  

#start client
client = OpenAI()

#function to identify section titles in the article using the API - preferably 4o-mini 
#prompt the LLM to find subsections within the paper
def identify_sections(content):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a skilled assistant trained to identify and list section titles in academic articles."},
            {"role": "user", "content": f"Identify the section titles in this academic article excerpt: {content}. Your output should be ONLY the titles, nothing else"}
        ]
    )
    return response.choices[0].message.content.strip()

#split the paper into sections using the section titles found with the 1st prompt
def split_content(content, sections):
    pattern = '|'.join([re.escape(section) for section in sections.split('\n') if section.strip()]) #regex pattern to match the section titles found
    return re.split(pattern, content)   #split based on section titles

#create 'ai versions' of each content block after the splitting happens
#prompt the LLM to try mimic the human writing and keep the structure as best as possible
# (maybe adjust the prompt later for better results - tbd)
def generate_ai_versions(blocks):
    ai_versions = []
    total = len(blocks)
    for i, block in enumerate(blocks):
        if block.strip():
            response = client.chat.completions.create(
                model="gpt-4o-mini",    #using 4o-mini for testing purposes, the real thing will use 4o probably
                messages=[
                    {"role": "system", "content": "You are a skilled assistant trained to rewrite academic text to make it indistinguishable from human-written text."},
                    {"role": "user", "content": f"Rewrite this text to best mimic human writing, while keeping the same structure and word count of the text as best as possible: {block.strip()}"}
                ]
            )
            ai_versions.append(response.choices[0].message.content.strip() + "\n")
        update_progress((i + 1) / total)
    return ai_versions

#an attempt to create a loading bar that shows the processing status for each paper as it goes through the API
#works, but it refreshes at weird times
#(needs improvement - maybe add a index for each bar to know paper number)
def update_progress(progress):
    bar_length = 40
    status = ""
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(bar_length * progress))
    text = "\rProcessing: [{0}] {1}% {2}".format("#" * block + "-" * (bar_length - block), int(progress * 100), status)
    sys.stdout.write(text)
    sys.stdout.flush()

#load article from data folder
#needs to be changed from hardcoding
articles = load_article_data('../data/arxive_data.json')
ai_articles = []

#loop through each article and process it
for article_data in articles:
    article_content = article_data['contents']
    sections = identify_sections(article_content)
    blocks = split_content(article_content, sections)
    ai_versions = generate_ai_versions(blocks)
    ai_full_text = "".join(ai_versions)

    ai_article = {
        "category": article_data["category"],
        "article_id": article_data["article_id"],
        "name of paper": article_data["name of paper"],
        "author": "gpt-4o",
        "summary": article_data["summary"],
        "label": "AI",
        "contents": ai_full_text
    }
    #join all ai rewritten sections into one full text
    ai_articles.append(ai_article)

#save 'ai versions' into a json - path is hard coded - needs to be changed
with open('../test_data/ai_paper.json', 'w') as f:
    json.dump(ai_articles, f, indent=4)

print("\nAI versions saved to test_data/ai_paper.json.")
