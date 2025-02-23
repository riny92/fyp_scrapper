import sys
import time
import json
import re
import unicodedata
from openai import OpenAI
from dotenv import load_dotenv
from pylatexenc.latex2text import LatexNodes2Text
import ftfy

load_dotenv()

#load article from json file
def load_article_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data  

#start client
client = OpenAI()


# data cleaning
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


def clean_ai_text(text):

    text = ftfy.fix_text(text)  
    text = decode_unicode(text)
    text = fix_word_splits(text)
    text = convert_latex_math(text)
    # text = remove_control_characters(text)  

    # Ensure proper quotes are used
    text = text.replace('\"', '“').replace('\'', '’')  

    text = re.sub(r'\s+', ' ', text).strip()  
    return text




#function to identify section titles in the article using the API - preferably 4o-mini 
#prompt the LLM to find subsections within the paper
def identify_sections(content):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
            "role": "system",
            "content": "You are an expert in extracting section titles from academic papers. "
                        "Your task is to accurately identify and list section titles without hallucinating or "
                        "misplacing sections. Maintain the correct order and avoid creating section breaks in the middle of a paragraph."
            },
            {"role": "user", 
            "content": f"""Extract section titles from the following academic paper excerpt:{content}
            
            **Guidelines:**
            - **Return ONLY section titles that actually appear in the text.** Do NOT create new section titles.
            - **Maintain the order of sections as they appear.**
            - **Do NOT split paragraphs incorrectly.** If a section title is ambiguous or unclear, ignore it.
            - **Ensure that 'References' or similar sections are separate and not merged with other content.**
            - If no clear sections exist, return `"Full Document"`."""}
        ]
    )
    return response.choices[0].message.content.strip()


#split the paper into sections using the section titles found with the 1st prompt
def split_content(content, sections):
    section_titles = [title.strip() for title in sections.split("\n") if title.strip()]
    if section_titles:
        print("\nSubchapter Titles Identified")
    elif not section_titles:
        print("No valid section titles found - treating the whole text as a single section.")
        return [("Full Document", content)]

    pattern = '|'.join([re.escape(title) for title in section_titles])
    split_sections = re.split(pattern, content)

    return list(zip(section_titles, split_sections[1:]))



#split the blocks further into paragraphs - easier on the LLM
def split_into_paragraphs(text):
    """ Splits a section into paragraphs while keeping structure """
    paragraphs = [p.strip() for p in re.split(r'\n+', text.strip()) if p.strip()]
    return paragraphs

#create 'ai versions' of each content block after the splitting happens
#prompt the LLM to try mimic the human writing and keep the structure as best as possible
def generate_ai_versions(human_text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=16300,
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
            {human_text.strip()}
            """}
        ]
    )
    return clean_ai_text(response.choices[0].message.content.strip())


#pogress bar for tracking the status of each paper i out of n total papers
def update_progress(progress, current_paper, total_papers):
    bar_length = 40
    status = "Done!" if progress >= 1 else ""
    block = int(round(bar_length * progress))
    sys.stdout.write(
        f"\rProcessing Paper {current_paper}/{total_papers}: [{'#' * block + '-' * (bar_length - block)}] {int(progress * 100)}% {status}   "
    )
    sys.stdout.flush()


#write 'ai versions' after each end of process to prevent data loss if the script crashes
def save_article_progress(filepath, ai_articles):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(ai_articles, f, indent=4, ensure_ascii=False)


#load article from data folder
articles = load_article_data('../data/demo.json')
ai_articles = []
total_papers = len(articles)

#loop through each article and process it
for paper_index, article_data in enumerate(articles, start=1):  
    article_content = article_data['contents']
    sections = identify_sections(article_content)


    if not sections.strip():
        sections = "Full Document"

    split_sections = split_content(article_content, sections)
    
    structured_contents = []
    total_paragraphs = sum(len(split_into_paragraphs(text)) for _, text in split_sections)
    processed_paragraphs = 0  


    cleaned_summary = clean_ai_text(article_data["summary"])

    for section_title, section_text in split_sections:
        paragraphs = split_into_paragraphs(section_text)

        for paragraph_number, human_text in enumerate(paragraphs, start=1):
            cleaned_human_text = (human_text)  
            ai_text = generate_ai_versions(cleaned_human_text)
            cleaned_ai_text = ai_text.replace("\n", " ")  

            structured_contents.append({
                "section_title": section_title,
                "paragraph_number": paragraph_number,
                "human": cleaned_human_text,
                "AI": cleaned_ai_text
            })

            processed_paragraphs += 1
            update_progress(0.8 * (processed_paragraphs / total_paragraphs) + 0.2 * (paper_index / total_papers), paper_index, total_papers)
            

    ai_article = {
        "category": article_data["category"],
        "article_id": article_data["article_id"],
        "name of paper": article_data["name of paper"],
        "author": {
            "human": article_data["author(s)"],
            "AI": "GPT-4o"
        },
        "summary": cleaned_summary,
        "contents": structured_contents
    }
    
    ai_articles.append(ai_article)
    save_article_progress('../data/demo_ai_section.json', ai_articles)

    update_progress(1, paper_index, total_papers)

print("\nAI versions saved to /data/broken_ai.json.")
#-----------------####