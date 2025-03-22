import os
import sys
import json
import time
import re
import unicodedata
from openai import OpenAI
from dotenv import load_dotenv
from data_cleaning import clean_text  
import logging

#load API key from .env
load_dotenv()
client = OpenAI()
logging.basicConfig(level=logging.ERROR)

#show current loaded configuration at start
def log_config():
    print("\n===== AI Text Generation Configuration =====")
    print(f" Using LLM Model: {LLM_MODEL}")
    print(f" Max Tokens: {LLM_MAX_TOKENS}")
    print(f" Prompt Instructions:\n{LLM_INSTRUCTIONS.replace('\\n', '\n')}")  
    print("=" * 45)

#list available datasets
def list_datasets():
    datasets = [f for f in os.listdir() if f.endswith(".json")]
    if not datasets:
        print("\nNo datasets found.")
        sys.exit()
    
    print("\nAvailable datasets:")
    for idx, dataset in enumerate(datasets, 1):
        print(f"{idx}. {dataset}")
    
    return datasets

#prompt user to select a dataset
def select_dataset():
    datasets = list_datasets()
    choice = input("\nEnter the number of the dataset to use: ").strip()
    
    try:
        dataset_name = datasets[int(choice) - 1]
        return dataset_name
    except (ValueError, IndexError):
        print("\nInvalid choice. Exiting.")
        sys.exit()

#load the dataset
def load_dataset(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


#default settings, get overwritten by .env settings
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 16300))  
LLM_INSTRUCTIONS = os.getenv("LLM_INSTRUCTIONS", 
    "- **DO NOT summarize or shorten.**\n"
    "- **Maintain the same word count or slightly expand the text.**\n"
    "- **Ensure the output has AT LEAST as many words as the input.**\n"
    "- **Do not remove key details or simplify concepts.**\n"
    "- **Maintain paragraph structures and overall format.**"
)

#OpenAI call to generate AI text
def generate_ai_version(human_text):
    print(f"\nGenerating AI text for paragraph ({len(human_text.split())} words)...")
    
    start_time = time.time() 
    response = client.chat.completions.create(
        model=LLM_MODEL,
        max_tokens=LLM_MAX_TOKENS,  
        messages=[
            {"role": "system", "content": "You are a skilled assistant trained to rewrite academic text to mimic human writing."},
            {"role": "user", "content": f"""
            Rewrite the following text in a way that best mimics human writing.
            {LLM_INSTRUCTIONS}  
            
            Here is the text to rewrite:
            {human_text.strip()}
            """}
        ]
    )
    
    generated_text = clean_text(response.choices[0].message.content.strip())
    elapsed_time = time.time() - start_time
    print(f"AI text generated in {elapsed_time:.2f} seconds.")
    
    return generated_text

#save the dataset after processing each paragraph
def save_dataset(filename, updated_data):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(updated_data, file, indent=4, ensure_ascii=False)

#process dataset and generate AI text
def process_dataset(dataset, filename):
    total_papers = len(dataset)
    total_paragraphs = sum(len(paragraphs) for paragraphs in dataset.values())
    processed_paragraphs = 0  #tracker for processed paragraphs

    for paper_idx, (paper_id, paragraphs) in enumerate(dataset.items(), start=1):
        for para_idx, para in enumerate(paragraphs):
            if para["multilinear"] == 0 and not para["ai"]:  #generate if AI field is empty and not multilinear
                para["ai"] = [generate_ai_version(para["human"][0])]  
                
                #save progress 
                save_dataset(filename, dataset)

                #update progress 
                processed_paragraphs += 1
                print(f"\rProcessing paragraph {processed_paragraphs}/{total_paragraphs} (Paper {paper_idx}/{total_papers})...", end="")
                sys.stdout.flush()
    
    print("\nProcessing complete!")

def main():
    log_config()
    dataset_name = select_dataset()
    dataset = load_dataset(dataset_name)

    print("\nGenerating AI versions of human text (this will take some time)...")
    process_dataset(dataset, dataset_name)

if __name__ == "__main__":
    main()
