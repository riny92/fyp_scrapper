import os
import sys
import category_finder
import scraper
import reader
import dataset_management
import ai_gen  
import evaluation
import gpt_evaluation

#asks user what they want to do
def main_menu():
    while True:
        print("\n===== MAKE SURE TO NOT PUBLISH .ENV ON GITHUB =====")
        print("\n===== AI-Powered Academic Dataset Toolkit =====")
        print("1. Scrape new papers")
        print("2. Read scraped papers from existing datasets.")
        print("3. View arXiv categories")
        print("4. Dataset Management") 
        print("5. Generate AI versions of human text")  
        print("6. Dataset Evaluation")
        print("7. GPT Evaluation")

        print("8. Exit")
        
        choice = input("\nEnter the number of your choice: ").strip()
        
        if choice == "1":
            run_scraper()
        elif choice == "2":
            run_reader()
        elif choice == "3":
            run_category_finder()
        elif choice == "4":
            dataset_management.manage_datasets() 
        elif choice == "5":
            run_ai_generator() 

        elif choice == "6":
            run_evaluation()  
        elif choice =='7':
            run_gpt_evaluation()

        elif choice == "8":
            print("\nExiting...")
            sys.exit()
        else:
            print("\nInvalid choice. Please try again.")

def run_scraper():
    print("\n===== Scraping Papers from arXiv =====")
    categories = scraper.prompt_categories_and_papers()
    dataFileName = scraper.prompt_dataset_filename()

    existing_data = scraper.prompt_file_mode(dataFileName)

    for category, max_papers in categories.items():
        print(f"\nScraping {max_papers} papers from category: {category}")
        existing_data = scraper.scrape_category(category, max_papers, existing_data, dataFileName)

    print("\nScraping complete!")

def run_reader():
    print("\n===== Reading Scraped Papers =====")
    reader.main()

def run_category_finder():
    print("\n===== Listing arXiv Categories =====")
    categories = category_finder.fetch_arxiv_categories()

    if categories:
        print("\nAvailable arXiv Categories:\n")
        for cat in categories:
            print(cat)
    else:
        print("\nNo categories found.")

def run_ai_generator():
    print("\n===== AI Generation for Human Text =====")
    ai_gen.main()  


def run_evaluation():
    print("\n===== Evaluating AI-Generated Text =====")
    evaluation.main()

def run_gpt_evaluation():
    gpt_evaluation.main()

if __name__ == "__main__":
    main_menu()
