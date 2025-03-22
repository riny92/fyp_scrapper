import os
import json

DATASET_FOLDER = "." 

#lists all available datasets within the same folder
def list_datasets():
    """L."""
    datasets = [f for f in os.listdir(DATASET_FOLDER) if f.endswith(".json")]
    if not datasets:
        print("\nNo datasets found.")
    else:
        print("\nAvailable datasets:")
        for idx, dataset in enumerate(datasets, 1):
            print(f"{idx}. {dataset}")
    return datasets

#removes a dataset file
def remove_dataset():
    datasets = list_datasets()
    if not datasets:
        return

    choice = input("\nEnter the number of the dataset to delete -or q to cancel: ").strip()
    if choice.lower() == "q":
        return

    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(datasets):
            os.remove(datasets[choice_idx])
            print(f"\nDataset '{datasets[choice_idx]}' deleted successfully.")
        else:
            print("\nInvalid selection.")
    except ValueError:
        print("\nInvalid input type")

#renames a dataset file
def rename_dataset():
    datasets = list_datasets()
    if not datasets:
        return

    choice = input("\nEnter the number of the dataset to rename - or q to cancel: ").strip()
    if choice.lower() == "q":
        return

    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(datasets):
            new_name = input("\nEnter the new name for the dataset ").strip()
            if not new_name.endswith(".json"):
                new_name += ".json"

            old_path = os.path.join(DATASET_FOLDER, datasets[choice_idx])
            new_path = os.path.join(DATASET_FOLDER, new_name)

            if os.path.exists(new_path):
                print("\nA file with this name already exists.")
            else:
                os.rename(old_path, new_path)
                print(f"\nDataset renamed to '{new_name}'.")
        else:
            print("\nInvalid selection.")
    except ValueError:
        print("\nInvalid input type")

#merges two dataset files by appending entries from one to another
def merge_datasets():
    datasets = list_datasets()
    if len(datasets) < 2:
        print("\nAt least two datasets are needed to merge.")
        return

    choice1 = input("\nEnter the number of the first dataset to merge: ").strip()
    choice2 = input("Enter the number of the second dataset to merge: ").strip()

    try:
        idx1 = int(choice1) - 1
        idx2 = int(choice2) - 1

        if idx1 == idx2:
            print("\nYou cannot merge a dataset with itself")
            return

        if 0 <= idx1 < len(datasets) and 0 <= idx2 < len(datasets):
            dataset1_path = os.path.join(DATASET_FOLDER, datasets[idx1])
            dataset2_path = os.path.join(DATASET_FOLDER, datasets[idx2])

            with open(dataset1_path, "r", encoding="utf-8") as f1, open(dataset2_path, "r", encoding="utf-8") as f2:
                data1 = json.load(f1)
                data2 = json.load(f2)

            merged_data = {**data1, **data2}  

            output_file = input("\nEnter the name of the newly merged dataset: ").strip()
            if not output_file.endswith(".json"):
                output_file += ".json"

            with open(os.path.join(DATASET_FOLDER, output_file), "w", encoding="utf-8") as f:
                json.dump(merged_data, f, indent=4, ensure_ascii=False)

            print(f"\nDatasets merged successfully into '{output_file}'.")
        else:
            print("\nInvalid selection.")
    except ValueError:
        print("\nInvalid input type.")

#dataset management menu
def manage_datasets():
    while True:
        print("\n===== Dataset Management =====")
        print("1. List datasets")
        print("2. Remove a dataset")
        print("3. Rename a dataset")
        print("4. Merge two datasets")
        print("5. Go back to main menu")

        choice = input("\nEnter the number of your choice: ").strip()

        if choice == "1":
            list_datasets()
        elif choice == "2":
            remove_dataset()
        elif choice == "3":
            rename_dataset()
        elif choice == "4":
            merge_datasets()
        elif choice == "5":
            return
        else:
            print("\nInvalid choice. Please try again.")

