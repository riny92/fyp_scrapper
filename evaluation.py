# INITIAL IMPLEMENTATION WITH MATRIX + THRESHHOLD + TOLERANCE FACTOR
import os
import json
import numpy as np
from Levenshtein import distance as levenshtein_distance
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def normalized_levenshtein(human, ai):
    return levenshtein_distance(human, ai) / max(len(human), len(ai))


def calculate_cosine_similarity(human, ai):
    vectorizer = TfidfVectorizer().fit_transform([human, ai])
    return cosine_similarity(vectorizer[0], vectorizer[1])[0][0]


def evaluate_paper(article_id, paragraphs, tolerance_factor=0.1):
    results = {
        "article_id": article_id,
        "evaluations": []
    }

    valid_paragraphs = [
        para for para in paragraphs if para.get("multilinear", 1) == 0 and para.get("ai")
    ]
    num_paragraphs = len(valid_paragraphs)

    if num_paragraphs == 0:
        return results

    ld_matrix = np.zeros((num_paragraphs, num_paragraphs))
    cs_matrix = np.zeros((num_paragraphs, num_paragraphs))

    for i in range(num_paragraphs):
        for j in range(num_paragraphs):
            human_text = valid_paragraphs[i]["human"][0]
            ai_text = valid_paragraphs[j]["ai"][0]

            ld_matrix[i][j] = normalized_levenshtein(human_text, ai_text)
            cs_matrix[i][j] = calculate_cosine_similarity(human_text, ai_text)

    for i in range(num_paragraphs):
        ld_diag = ld_matrix[i][i]
        cs_diag = cs_matrix[i][i]

        ld_off_avg = np.mean(np.delete(ld_matrix[i, :], i))
        cs_off_avg = np.mean(np.delete(cs_matrix[i, :], i))

        ld_threshold = ld_off_avg - (ld_off_avg * tolerance_factor)
        cs_threshold = cs_off_avg + (cs_off_avg * tolerance_factor)

        ld_verdict = "Good LD" if ld_diag >= ld_threshold else "Low LD"
        cs_verdict = "Good CS" if cs_diag <= cs_threshold else "High CS"

        verdict = "Good AI-generated text" if ld_verdict == "Good LD" and cs_verdict == "Good CS" \
            else f"Issues: {ld_verdict}, {cs_verdict}"

        topic_results = {
            "section": valid_paragraphs[i].get("section", ""),
            "paragraph": valid_paragraphs[i].get("paragraph", ""),
            "LD_diag": ld_diag,
            "LD_off_avg": ld_off_avg,
            "LD_threshold": ld_threshold,
            "CS_diag": cs_diag,
            "CS_off_avg": cs_off_avg,
            "CS_threshold": cs_threshold,
            "Verdict": verdict
        }

        results["evaluations"].append(topic_results)

    return results


def process_dataset(input_filepath, output_filepath, tolerance_factor=0.1):
    print(f"Loading {input_filepath} ...")
    data = load_json(input_filepath)
    evaluation_results = [
        evaluate_paper(article_id, paragraphs, tolerance_factor) for article_id, paragraphs in data.items()
    ]

    print(f"Saving evaluation report to {output_filepath} ...")
    save_json(output_filepath, evaluation_results)
    print("Evaluation complete!")

    summarize_failures(evaluation_results)


def summarize_failures(evaluation_results):
    failed_topics = []
    total_count = 0

    for article in evaluation_results:
        for topic in article["evaluations"]:
            total_count += 1
            if "Low LD" in topic["Verdict"] or "High CS" in topic["Verdict"]:
                failed_topics.append(topic)

    total_failed = len(failed_topics)
    passed_count = total_count - total_failed

    print("\nEvaluation Failure Breakdown: ")
    print(f"Topics failing LD (Low Structural Difference): {sum(1 for topic in failed_topics if 'Low LD' in topic['Verdict'])} / {total_count}")
    print(f"Topics failing CS (High Semantic Similarity): {sum(1 for topic in failed_topics if 'High CS' in topic['Verdict'])} / {total_count}")
    print(f"Topics that passed: {passed_count} / {total_count}")

DATASET_FOLDER = "."

def list_datasets():
    if not os.path.exists(DATASET_FOLDER):
        print("Error: 'datasets' folder not found.")
        return None

    datasets = [f for f in os.listdir(DATASET_FOLDER) if f.endswith('.json')]
    if not datasets:
        print("No datasets found in the folder.")
        return None

    print("\nAvailable Datasets:")
    for idx, dataset in enumerate(datasets, 1):
        print(f"{idx}. {dataset}")

    while True:
        try:
            choice = int(input("\nSelect a dataset by number: ")) - 1
            if 0 <= choice < len(datasets):
                return os.path.join(DATASET_FOLDER, datasets[choice])
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a valid number.")

def main():
    dataset_filename = list_datasets()
    if not dataset_filename:
        return

    try:
        tolerance_factor = float(input("Enter tolerance factor (default 0.1): ") or 0.1)
    except ValueError:
        print("Invalid input. Using default tolerance factor")
        tolerance_factor = 0.1

    output_filename = dataset_filename.replace(".json", "_evaluation.json")
    
    print("\nStarting evaluation...")
    process_dataset(dataset_filename, output_filename, tolerance_factor)
    print("\nDone.")

if __name__ == "__main__":
    main()

