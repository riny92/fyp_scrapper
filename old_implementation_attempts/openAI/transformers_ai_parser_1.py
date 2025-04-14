###TRANSFORMERS V1####
import sys
import json
import re
import unicodedata
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from pylatexenc.latex2text import LatexNodes2Text
import ftfy
from sentence_transformers import SentenceTransformer
import time,os

load_dotenv()

#disable some warnings from the transformer model
os.environ["TOKENIZERS_PARALLELISM"] = "false"

#use a pretrained transformer model for topic based splitting
# model = SentenceTransformer("all-MiniLM-L6-v2")
model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L3-v2")  

#load the articles from the json file
def load_article_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data  

#start openai client
client = OpenAI()

#as much text cleaning/ unicode translation as possible
def decode_unicode(text):
    
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("ﬂ", "fl").replace("ﬁ", "fi")  
    text = text.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")  
    text = text.replace("−", "-").replace("—", "-").replace("–", "-")  
    text = text.replace("\xad", "")  
    text = re.sub(r'[\u200B\u2060\uFEFF]', '', text)  
    return text

def fix_word_splits(text):
    #fix word splits from pdf conversion (ie. 'ge- nomics' - 'genomics')
    return re.sub(r"(\w+)-\s+(\w+)", r"\1\2", text)

# try and convert latex math expressions to unicode text
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
    return text

def clean_ai_text(text):
    
    text = ftfy.fix_text(text)
    text = decode_unicode(text)
    text = fix_word_splits(text)
    text = convert_latex_math(text)
    text = re.sub(r'\s+', ' ', text).strip()  
    return text

def split_by_topic(text, min_chunk_size=50):
    
    sentences = re.split(r'(?<=[.!?])\s+', text)  
    
    # embeddings = np.array(model.encode(sentences))
    embeddings = np.array(model.encode(sentences, batch_size=32, show_progress_bar=False))

    diffs = np.linalg.norm(np.diff(embeddings, axis=0), axis=1)

    threshold = np.percentile(diffs, 90)

    splits = []
    current_chunk = []

    for i, sentence in enumerate(sentences):
        current_chunk.append(sentence)
        if i < len(diffs) and diffs[i] > threshold:
            if sum(len(s) for s in current_chunk) > min_chunk_size: 
                splits.append(" ".join(current_chunk))
                current_chunk = []

    if current_chunk:
        splits.append(" ".join(current_chunk))  

    return splits


def generate_ai_versions(human_text):
    response = client.chat.completions.create(
        model="gpt-4o",
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

            Text to rewrite:
            {human_text.strip()}
            """}
        ]
    )
    return clean_ai_text(response.choices[0].message.content.strip())

def update_progress(current_paper, total_papers):
    bar_length = 40
    progress = current_paper / total_papers
    status = "Done!" if progress >= 1 else ""
    block = int(round(bar_length * progress))
    sys.stdout.write(
        f"\rProcessing Paper {current_paper}/{total_papers}: [{'#' * block + '-' * (bar_length - block)}] {int(progress * 100)}% {status}   "
    )
    sys.stdout.flush()

def save_article_progress(filepath, ai_articles):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(ai_articles, f, indent=4, ensure_ascii=False)

articles = load_article_data('../data/broken.json')
ai_articles = []
total_papers = len(articles)

for paper_index, article_data in enumerate(articles, start=1):  
    article_content = article_data['contents']
    
    cleaned_content = clean_ai_text(article_content)

    topic_sections = split_by_topic(cleaned_content)

    structured_contents = []
    
    cleaned_summary = clean_ai_text(article_data["summary"])

    for section_index, section_text in enumerate(topic_sections, start=1):
        cleaned_human_text = section_text  
        ai_text = generate_ai_versions(cleaned_human_text)  

        structured_contents.append({
            "topic_number": section_index,
            "human": cleaned_human_text,
            "AI": ai_text
        })

        update_progress(paper_index, total_papers)

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
    save_article_progress('../data/broken_ai.json', ai_articles)

    update_progress(paper_index, total_papers)

print("\nAI versions saved to /data/broken_ai.json.")

