import json
import re
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def load_article_data(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data  

client = OpenAI()

def identify_sections(content):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a skilled assistant trained to identify and list section titles in academic articles."},
            {"role": "user", "content": f"Identify the section titles in this academic article excerpt: {content}. Your output should be ONLY the titles, one per line, nothing else."}
        ]
    )
    return response.choices[0].message.content.strip()

def split_content(content, sections):
    print("\n--- Subchapter Titles---")
    print(sections)  

    section_titles = [title.strip() for title in sections.split("\n") if title.strip()]

    if not section_titles:
        print("No valid section titles found -treating the whole text as a single section")
        return [content]

    pattern = '|'.join([re.escape(title) for title in section_titles])
    split_sections = re.split(pattern, content)

    return list(zip(section_titles, split_sections[1:]))  

def split_into_paragraphs(text, max_paragraph_length=500):
    paragraphs = re.split(r'\n+', text.strip()) 
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

def write_debug_output(filename, articles):
    with open(filename, 'w', encoding='utf-8') as f:
        for index, article_data in enumerate(articles, start=1):
            article_content = article_data['contents']
            sections = identify_sections(article_content)
            split_sections = split_content(article_content, sections)

            f.write(f"\n--- Paper {index}: {article_data['name of paper']} ---\n")
            f.write("=" * 80 + "\n")

            for section_title, section_text in split_sections:
                f.write(f"\n### Section: {section_title}\n")
                f.write("\n[Full Section Below]\n")

                paragraphs = split_into_paragraphs(section_text)
                for i, para in enumerate(paragraphs, start=1):
                    f.write(f"\n    [Paragraph {i}]: {para}\n")

            f.write("\n" + "=" * 80 + "\n")

articles = load_article_data('../data/temp.json')
write_debug_output('../data/debug_output.txt', articles)

print("\ndebugging over")
