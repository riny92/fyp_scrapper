import json
import numpy as np
from Levenshtein import distance as levenshtein_distance
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

#load json data
def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

#save json data
def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

#Levenshtein Distance 
def normalized_levenshtein(human, ai):
    return levenshtein_distance(human, ai) / max(len(human), len(ai))  #normalize by text length

#Cosine Similarity
def calculate_cosine_similarity(human, ai):
    vectorizer = TfidfVectorizer().fit_transform([human, ai])
    return cosine_similarity(vectorizer[0], vectorizer[1])[0][0]

#evaluate paper with a tolerance factor (0.1 = no tolerance - can be increased)
def evaluate_paper(paper, tolerance_factor=0.1):
    results = {
        "article_id": paper["article_id"],
        "name": paper["name of paper"],
        "evaluations": []
    }

    contents = paper["contents"]
    num_topics = len(contents)

    #compute LD and CS matrices
    ld_matrix = np.zeros((num_topics, num_topics))
    cs_matrix = np.zeros((num_topics, num_topics))

    for i in range(num_topics):
        for j in range(num_topics):
            human_text = contents[i]["human"]
            ai_text = contents[j]["AI"]

            ld_matrix[i][j] = normalized_levenshtein(human_text, ai_text)
            cs_matrix[i][j] = calculate_cosine_similarity(human_text, ai_text)

    #evaluate each of the topics
    for i in range(num_topics):
        ld_diag = ld_matrix[i][i]  
        ld_off_values = np.delete(ld_matrix[i, :], i)  
        ld_off_avg = np.mean(ld_off_values)  

        cs_diag = cs_matrix[i][i] 
        cs_off_values = np.delete(cs_matrix[i, :], i)  
        cs_off_avg = np.mean(cs_off_values)  

        #put in the tolerance factor 
        ld_threshold = ld_off_avg - (ld_off_avg * tolerance_factor)  
        cs_threshold = cs_off_avg + (cs_off_avg * tolerance_factor) 

        #give a verdict
        ld_verdict = "Good LD" if ld_diag >= ld_threshold else "Low LD"
        cs_verdict = "Good CS" if cs_diag <= cs_threshold else "High CS"

        topic_results = {
            "topic_number": contents[i]["topic_number"],
            "LD_diag": ld_diag,
            "LD_off_avg": ld_off_avg,
            "LD_threshold": ld_threshold,
            "CS_diag": cs_diag,
            "CS_off_avg": cs_off_avg,
            "CS_threshold": cs_threshold,
            "Verdict": "Good AI generated text" if ld_verdict == "Good LD" and cs_verdict == "Good CS"
                        else f"Issues: {ld_verdict}, CS: {cs_verdict}"
        }

        results["evaluations"].append(topic_results)

    return results

#process dataset and save results
def process_data(input_filepath, output_filepath, tolerance_factor=0.1):
    print(f"Loading {input_filepath} ...")
    data = load_json(input_filepath)
    evaluation_results = [evaluate_paper(paper, tolerance_factor) for paper in data]

    print(f"Saving evaluation report to {output_filepath} ...")
    save_json(output_filepath, evaluation_results)
    print("Complete!")

    #have a summary after processing
    summarize_failures(evaluation_results)

def summarize_failures(evaluation_results):
    failed_topics = []
    for paper in evaluation_results:
        for topic in paper["evaluations"]:
            if "Low LD" in topic["Verdict"] or "High CS" in topic["Verdict"]:
                failed_topics.append(topic)  

    total_failed = len(failed_topics)
    total_count = sum(len(paper["evaluations"]) for paper in evaluation_results)
    passed_count = total_count - total_failed  

    print("\nEvaluation Failure Breakdown: ")
    print(f"Topics failing LD (Low Structural Difference): {sum(1 for topic in failed_topics if 'Low LD' in topic['Verdict'])} / {total_count}")
    print(f"Topics failing CS (High Semantic Similarity): {sum(1 for topic in failed_topics if 'High CS' in topic['Verdict'])} / {total_count}")
    print(f"Topics that passed: {passed_count} / {total_count}")



input_file = "../data/demo_ai_transformers.json"
output_file = "../data/evaluation_results.json"

process_data(input_file, output_file, tolerance_factor=0.2)
