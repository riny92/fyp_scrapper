import sys
import time
import json
import re
from openai import OpenAI
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
            {"role": "user", "content": f"Identify the section titles in this academic article excerpt: {content}. Your output should be ONLY the titles, one per line, nothing else."}
        ]
    )
    return response.choices[0].message.content.strip()

#split the paper into sections using the section titles found with the 1st prompt
def split_content(content, sections):
    print("\nSubchapter Titles Identified")

    section_titles = [title.strip() for title in sections.split("\n") if title.strip()]

    #handle cases where no valid sections come from the ai prompt
    if not section_titles:
        print("No valid section titles found -treating the whole text as a single section")
        return [("Full Document", content)]

    pattern = '|'.join([re.escape(title) for title in section_titles])
    split_sections = re.split(pattern, content)

    return list(zip(section_titles, split_sections[1:]))  # Pair section titles with their content

#split the blocks further into paragraphs - easier on the LLM
def split_into_paragraphs(text, max_paragraph_length=500):
    paragraphs = [p.strip() for p in re.split(r'\n+', text.strip()) if p.strip()]
    combined_paragraphs = []
    buffer = ""

    for para in paragraphs:
        if len(buffer) + len(para) < max_paragraph_length:
            buffer += " " + para
        else:
            combined_paragraphs.append(buffer.strip())
            buffer = para

    if buffer:  
        combined_paragraphs.append(buffer.strip())

    return combined_paragraphs

#create 'ai versions' of each content block after the splitting happens
#prompt the LLM to try mimic the human writing and keep the structure as best as possible
def generate_ai_versions(split_sections, current_paper, total_papers):
    ai_versions = []
    
    for section_title, section_text in split_sections:

        paragraphs = split_into_paragraphs(section_text)
        ai_paragraphs = []
        
        for para in paragraphs:
            if para.strip():
                response = client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=16300,  #max possible value
                    messages=[
                        {"role": "system", "content": "You are a skilled assistant trained to rewrite academic text to make it indistinguishable from human-written text."},
                        {"role": "user", "content": f"""
                        Rewrite the following text in a way that best mimics human writing.

                        - **DO NOT summarize or shorten.**  
                        - **Maintain the same word count or slightly expand the text.**  
                        - **Ensure the output has AT LEAST as many words as the input.**  
                        - **Do not remove key details or simplify concepts.**  
                        - **Maintain paragraph structures and overall format.**  

                        Here is the text to rewrite:
                        {para.strip()}
                        """}
                    ]
                )
                ai_paragraphs.append(response.choices[0].message.content.strip())

        #combine AI paragraphs for the section
        ai_versions.append(f"\n### {section_title}\n" + "\n".join(ai_paragraphs))

        #update progress with the loading bar
        update_progress(len(ai_versions) / len(split_sections), current_paper, total_papers)

    return ai_versions

#pogress bar for tracking the status of each paper i out of n total papers
def update_progress(progress, current_paper, total_papers):
    bar_length = 40
    status = "Done...\r\n" if progress >= 1 else ""
    block = int(round(bar_length * progress))
    text = f"\rProcessing Paper {current_paper}/{total_papers}: [{'#' * block + '-' * (bar_length - block)}] {int(progress * 100)}% {status}"
    sys.stdout.write(text)
    sys.stdout.flush()

#write 'ai versions' after each end of process to prevent data loss if the script crashes
def save_article_progress(filepath, ai_articles):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(ai_articles, f, indent=4)

#load article from data folder
#needs to be changed from hardcoding
articles = load_article_data('../data/arxive_data.json')
ai_articles = []
total_papers = len(articles)

#loop through each article and process it
for index, article_data in enumerate(articles, start=1):  
    article_content = article_data['contents']
    
    #identify sections and split content
    sections = identify_sections(article_content)
    split_sections = split_content(article_content, sections)
    
    #get 'ai version' of each
    ai_versions = generate_ai_versions(split_sections, index, total_papers)  
    ai_full_text = "\n\n".join(ai_versions).replace("\n", " ")  #handle whitespace in json file

    #strcture the json with ai content
    ai_article = {
        "category": article_data["category"],
        "article_id": article_data["article_id"],
        "name of paper": article_data["name of paper"],
        "author": "gpt-4o",
        "summary": article_data["summary"],
        "label": "AI",
        "contents": ai_full_text
    }
    
    ai_articles.append(ai_article)
    
    #save most recent progress after each paper is processed
    save_article_progress('../data/arxive_data_ai.json', ai_articles)

print("\nAI versions saved to data/arxive_data_ai.json.")
