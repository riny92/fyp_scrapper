#maybe useful metrics to see if the data is good for our purpose

import json
import os
import re
import unicodedata
import ftfy
from Levenshtein import distance as levenshtein_distance
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.translate.bleu_score import sentence_bleu
from bert_score import score as bert_score
from textstat import flesch_kincaid_grade

#load from json
def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

#save results
def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

#some basic cleaning (just in case)
def clean_text(text):
    text = ftfy.fix_text(text) 
    text = unicodedata.normalize("NFKC", text) 
    text = re.sub(r'\s+', ' ', text).strip()  
    return text

#Levenshtein Distance (Measures how many character edits are needed) -> consistancy/accuracy metric
def calculate_levenshtein(human, ai):
    return levenshtein_distance(human, ai)

#Cosine Similarity (Measures word-level similarity) -> semantic accuracy metric
def calculate_cosine_similarity(human, ai):
    vectorizer = TfidfVectorizer().fit_transform([human, ai])
    return cosine_similarity(vectorizer[0], vectorizer[1])[0][0]

#BLEU Score (Measures n-gram overlap) -> lexical consistancy metric
def calculate_bleu(human, ai):
    return sentence_bleu([human.split()], ai.split())

#BERTScore (Deep semantic similarity using transformers) -> semantic consistency metric
def calculate_bert_score(human, ai):
    P, R, F1 = bert_score([ai], [human], lang="en")
    return F1.mean().item()

#Readability Scores (Flesch-Kincaid Grade Level) -> clarity metric
def calculate_readability(text):
    return flesch_kincaid_grade(text)

#evaluate Paragraph
def evaluate_paragraph(human, ai):
    return {
        "levenshtein_distance": calculate_levenshtein(human, ai),
        "cosine_similarity": calculate_cosine_similarity(human, ai),
        "bleu_score": calculate_bleu(human, ai),
        "bert_score": calculate_bert_score(human, ai),
        "readability_human": calculate_readability(human),
        "readability_ai": calculate_readability(ai),
    }

#process the json data and evaluate
def process_data(input_filepath, output_filepath):
    print(f"📂 Loading {input_filepath} ...")
    data = load_json(input_filepath)
    evaluation_results = []

    for paper in data:
        paper_results = {
            "article_id": paper["article_id"],
            "name": paper["name of paper"],
            "evaluations": []
        }

        for section in paper["contents"]:
            section_title = section["section_title"]
            paragraph_number = section["paragraph_number"]
            human_text = clean_text(section["human"])
            ai_text = clean_text(section["AI"])

            # Run evaluation metrics
            eval_metrics = evaluate_paragraph(human_text, ai_text)
            eval_metrics["section_title"] = section_title
            eval_metrics["paragraph_number"] = paragraph_number

            paper_results["evaluations"].append(eval_metrics)

        evaluation_results.append(paper_results)

    print(f"saving evaluation report to {output_filepath} ...")
    save_json(output_filepath, evaluation_results)
    print("complete!")

input_file = "../data/temporary_ai.json"
output_file = "../data/evaluation_report.json"

process_data(input_file, output_file)
