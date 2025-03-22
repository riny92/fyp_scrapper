import os
import json

def list_json_files():
    files = [f for f in os.listdir() if f.endswith('.json')]
    return files

def choose_file(files):
    if not files:
        print("No JSON files found in the directory.")
        exit()

    print("\nAvailable datasets:")
    for idx, file in enumerate(files):
        print(f"{idx + 1}. {file}")

    while True:
        choice = input("\nEnter the number of the dataset you want to open: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(files):
            return files[int(choice) - 1]
        else:
            print("Invalid choice. Please enter a valid number.")

def load_dataset(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def choose_article(articles):
    article_ids = list(articles.keys())

    print("\nAvailable articles:")
    for idx, article_id in enumerate(article_ids):
        print(f"{idx + 1}. {article_id}")

    while True:
        choice = input("\nEnter the number of the article you want to read: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(article_ids):
            return article_ids[int(choice) - 1]
        else:
            print("Invalid choice. Please enter a valid number.")

def display_article(article):
    print("\n" + "="*80)
    print(f"Article Content:")
    print("="*80)

    for entry in article:
        section = entry['section']
        paragraph_num = entry['paragraph']
        text = ' '.join(entry['human']) 
        print(f"\n[Section: {section} - Paragraph {paragraph_num}]")
        print(text)

    print("\n" + "="*80)
    print("End of Article")
    print("="*80)

def main():
    files = list_json_files()
    chosen_file = choose_file(files)
    print(f"\nOpening dataset: {chosen_file}")

    dataset = load_dataset(chosen_file)

    if not dataset:
        print(f"No articles found in {chosen_file}")
        exit()

    chosen_article_id = choose_article(dataset)
    chosen_article = dataset[chosen_article_id]

    print(f"\nOpening article: {chosen_article_id}")
    display_article(chosen_article)

if __name__ == "__main__":
    main()
