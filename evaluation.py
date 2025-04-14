import os
import json
import numpy as np
from Levenshtein import distance as levenshtein_distance
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)


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

    ld_matrix = np.full((num_paragraphs, num_paragraphs), np.nan)
    cs_matrix = np.full((num_paragraphs, num_paragraphs), np.nan)

    for i in range(num_paragraphs):
        for j in range(num_paragraphs):
            try:
                human_text = valid_paragraphs[i]["human"][0]
                ai_text = valid_paragraphs[j]["ai"][0]
                ld_matrix[i][j] = normalized_levenshtein(human_text, ai_text)
                cs_matrix[i][j] = calculate_cosine_similarity(human_text, ai_text)
            except Exception as e:
                continue  #skip problematic entries

    for i in range(num_paragraphs):
        ld_diag = ld_matrix[i][i]
        cs_diag = cs_matrix[i][i]

        cs_off_vals = np.delete(cs_matrix[i, :], i)
        cs_off_avg = np.nanmean(cs_off_vals)

        topic_results = {
            "section": valid_paragraphs[i].get("section", ""),
            "paragraph": valid_paragraphs[i].get("paragraph", ""),
            "LD_diag": float(ld_diag) if not np.isnan(ld_diag) else None,
            "CS_diag": float(cs_diag) if not np.isnan(cs_diag) else None,
            "CS_off_avg": float(cs_off_avg) if not np.isnan(cs_off_avg) else None
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
    summarize_results(evaluation_results)

def summarize_results(evaluation_results):
    total = 0
    cs_diag_better_count = 0
    ld_values = []

    for article in evaluation_results:
        for topic in article["evaluations"]:
            cs_diag = topic["CS_diag"]
            cs_off_avg = topic["CS_off_avg"]
            ld_diag = topic["LD_diag"]

            if cs_diag is not None and cs_off_avg is not None:
                total += 1
                if cs_diag > cs_off_avg:
                    cs_diag_better_count += 1
            if ld_diag is not None and ld_diag > 0.1:
                ld_values.append(ld_diag)

    if ld_values:
        ld_min = min(ld_values)
        ld_max = max(ld_values)
    else:
        ld_min = ld_max = 0

    print("\n--- Evaluation Summary ---")
    print(f"Paragraphs where CS_diag > CS_off_avg: {cs_diag_better_count} / {total}")
    print(f"LD_diag range: [{round(ld_min, 4)}, {round(ld_max, 4)}]")

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
