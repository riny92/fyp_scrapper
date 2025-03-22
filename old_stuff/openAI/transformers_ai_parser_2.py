
####TRANSFORMERS V2####
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
import os, time

load_dotenv()

#disable some warnings from the transformer model
os.environ["TOKENIZERS_PARALLELISM"] = "false"

#use a pretrained transformer model for topic based splitting
model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L3-v2")  #this model isnt super accurate, but i think its enough for our purpose, also supposedly slightly faster than other similar ones

#load the articles from the json file
def load_article_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data  

#start openai client
client = OpenAI()

#as much text cleaning/ unicode translation as possible
def decode_unicode(text):
    """ Normalize Unicode text and fix problematic characters. """
    text = unicodedata.normalize("NFKC", text) 
    text = text.replace("ﬂ", "fl").replace("ﬁ", "fi")  
    text = text.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'") 
    text = text.replace("−", "-").replace("—", "-").replace("–", "-")  
    text = text.replace("\xad", "")  
    text = re.sub(r'[\u200B\u2060\uFEFF]', '', text)  
    return text

def fix_word_splits(text):
    
    return re.sub(r"(\w+)-\s+(\w+)", r"\1\2", text) #fix word splits from pdf conversion (ie. 'ge- nomics' - 'genomics')

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

    # \( ... \)
    text = re.sub(r"\\\((.*?)\\\)", replace_inline, text)
    #\[ ... \]
    text = re.sub(r"\\\[(.*?)\\\]", replace_block, text)

    #more latex symbols
    text = text.replace(r"\phi", "φ").replace(r"\theta", "θ").replace(r"\alpha", "α").replace(r"\beta", "β")
    text = text.replace(r"\gamma", "γ").replace(r"\delta", "δ").replace(r"\lambda", "λ").replace(r"\mu", "μ")
    text = text.replace(r"\pi", "π").replace(r"\sigma", "σ").replace(r"\tau", "τ").replace(r"\Omega", "Ω")
    text = text.replace(r"\in", "∈").replace(r"\cdot", "·").replace(r"\times", "×").replace(r"\pm", "±")
    text = text.replace(r"\int", "∫").replace(r"\sum", "∑").replace(r"\prod", "∏").replace(r"\frac", "/")

    return text

def remove_control_characters(text):

    return re.sub(r"[\x00-\x1F\x7F-\x9F]", "", text)  #remove control chars (except whitespace)


def clean_ai_text(text):
    
    text = ftfy.fix_text(text)  
    text = decode_unicode(text)
    text = fix_word_splits(text)
    text = convert_latex_math(text)
    text = remove_control_characters(text) 

    
    text = text.replace('\"', '“').replace('\'', '’')  # Convert straight quotes to curly (trying to get around python string handling with " ")

    text = re.sub(r'\s+', ' ', text).strip()  #remove extra spaces
    return text


#splits text at major topic shifts (decided by the transformer model) - also prevents tiny splits and tries to reduce embedding computation with the sentence_skip param
def split_by_topic(text, min_chunk_size=50, sentence_skip=1):

    
    # Step 1: 
    sentences = re.split(r'(?<=[.!?])\s+', text)  # Split text into sentences (at punctuation)
    
    #compute sentence embeddings only for every nth sentence (to speed up processing)
    selected_sentences = sentences[::sentence_skip]  #skips every `sentence_skip` sentences
    embeddings = np.array(model.encode(selected_sentences, batch_size=32, show_progress_bar=False))

    #compute differences between consecutive sentence embeddings
    diffs = np.linalg.norm(np.diff(embeddings, axis=0), axis=1)

    #topic-change threshold (ie. lower perc = more splits, higher perc = less splits)
    threshold = np.percentile(diffs, 85)

    #split where topic changes occur
    splits = []
    current_chunk = []
    last_valid_chunk = None  #try and handle numbers in final topic (otherwise, last identified topic will be the page number of last page)

    for i, sentence in enumerate(sentences):
        current_chunk.append(sentence)

        if i % sentence_skip == 0 and i < len(diffs) and diffs[i // sentence_skip] > threshold:
            if sum(len(s) for s in current_chunk) > min_chunk_size:  #set chunk size
                splits.append(" ".join(current_chunk))
                last_valid_chunk = splits[-1]  #keep track of last chunk
                current_chunk = []

    if current_chunk:
        #stop last split from being just a number
        if len(current_chunk) == 1 and re.match(r"^\d+$", current_chunk[0].strip()):
            if last_valid_chunk:  #append the number to the last chunk
                splits[-1] += " " + current_chunk[0]
        else:
            splits.append(" ".join(current_chunk))  #otherwise append remaining text

    return splits

#create 'ai versions' of each content block after the splitting happens
#prompt the LLM to try mimic the human writing and keep the structure as best as possible
# def generate_ai_versions(human_text):

#     response = client.chat.completions.create(
#         model="gpt-4o",
#         max_tokens=16300,
#         temperature=0.7,  # Increase randomness
#         top_p=0.85,  # Reduce high-probability word choices
#         messages=[
#             {"role": "system", "content": "You are a skilled assistant trained to rewrite academic text to make it indistinguishable from human-written text."},
#             {"role": "user", "content": f"""
#             Rewrite the following text in a way that best mimics human writing.
#             - **DO NOT summarize or shorten.**  
#             - **Maintain the same word count or slightly expand the text.**  
#             - **Ensure the output has AT LEAST as many words as the input.**  
#             - **Do not remove key details or simplify concepts.**  
#             - **Maintain paragraph structures and overall format.**  
#             Here is the text to rewrite:

#             Text to rewrite:
#             {human_text.strip()}
#             """}
#         ]
#     )
#     return clean_ai_text(response.choices[0].message.content.strip())


def generate_ai_versions(human_text):

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=16300,
        temperature=0.9,  # Slightly increase randomness for more natural variation
        top_p=0.9,  # Keep diversity but within logical bounds
        messages=[
            {"role": "system", "content": "You are a skilled academic writer. Your task is to rewrite text so that it mimics natural human writing perfectly, making it indistinguishable from a human-written version."},
            {"role": "user", "content": f"""
            Rewrite the following text so that it appears authentically human-written, making subtle but meaningful changes in phrasing, structure, and word choice. 

            ### Instructions:
            - **Do NOT simply rephrase word-for-word.** Introduce **natural variations** that a human would.
            - **Maintain the original meaning but reword naturally.**
            - **Vary sentence structures slightly** to reflect how humans naturally write.
            - **Use a mix of shorter and longer sentences** to add rhythm to the text.
            - **Use varied vocabulary and synonyms where appropriate.**
            - **Occasionally restructure paragraphs for better flow** (if needed).
            - **Do NOT remove or simplify key concepts.**
            - **Maintain the same word count or slightly expand it** to sound natural.

            ### Text to rewrite:
            {human_text.strip()}
            """}
        ]
    )
    return clean_ai_text(response.choices[0].message.content.strip())

#progress bar for tracking the status of each topic/paper out of the total
def update_progress(topic_index, total_topics, paper_index, total_papers):
    """Displays progress bar for each individual article's topics."""
    bar_length = 40
    progress = topic_index / total_topics
    status = "Done!" if progress >= 1 else ""
    block = int(round(bar_length * progress))
    sys.stdout.write(
        f"\rProcessing Paper {paper_index}/{total_papers} - Topic {topic_index}/{total_topics}: [{'#' * block + '-' * (bar_length - block)}] {int(progress * 100)}% {status}   "
    )
    sys.stdout.flush()

#write 'ai versions' after each end of process to prevent data loss if the script crashes
def save_article_progress(filepath, ai_articles):
    """Saves processed AI-generated articles."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(ai_articles, f, indent=4, ensure_ascii=False)

#load article from data folder
articles = load_article_data('../data/evaluation.json')
ai_articles = []
total_papers = len(articles)

#loop through each article and process it
for paper_index, article_data in enumerate(articles, start=1):  
    article_content = article_data['contents']
    
    #clean the input text
    cleaned_content = clean_ai_text(article_content)

    #split by topic using sentence embeddings
    topic_sections = split_by_topic(cleaned_content)


    structured_contents = []
    
    #also apply cleaning to article summary
    cleaned_summary = clean_ai_text(article_data["summary"])

    for section_index, section_text in enumerate(topic_sections, start=1):
        cleaned_human_text = section_text

        ai_text = generate_ai_versions(cleaned_human_text)

        cleaned_ai_text=clean_ai_text(ai_text)
        structured_contents.append({
            "topic_number": section_index,
            "human": cleaned_human_text,
            "AI": cleaned_ai_text
        })

        #update progress per topic
        update_progress(section_index, len(topic_sections), paper_index, total_papers)

    #strcture the json with ai content
    ai_article = {
        "category": article_data["category"],
        "article_id": article_data["article_id"],
        "name of paper": article_data["name of paper"],
        "summary": cleaned_summary,
        "contents": structured_contents
    }
    
    ai_articles.append(ai_article)
    save_article_progress('../data/evaluation_ai.json', ai_articles)
    time.sleep(2)  #just in case:)

print("\nAI versions saved to /data/evaluation_ai.json.")
