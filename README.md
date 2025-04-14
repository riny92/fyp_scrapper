# FYP_SCRAPPER

This repository supports my Final Year Project:  
**Generating a Corpus for Testing Tools for Detecting AI-generated Text in Educational Context**

---

## Overview

The goal of this project is to create a structured dataset containing both human-written and AI-generated academic text, in order to support future development and benchmarking of AI-detection tools within educational contexts.

The project pipeline includes:
- Scraping real scientific papers from [arXiv.org](https://arxiv.org/)
- Structuring the content by section and paragraph
- Generating AI-written equivalents using a language model (via OpenAI API)
- Storing both versions side-by-side
- Running text-level evaluations to assess the quality and similarity
- Performing GPT-based classification experiments to test detectability

---

## Repository Structure

### Core Scripts

| File | Description |
|------|-------------|
| `main.py` | Central menu that allows access to all modules via CLI. |
| `ai_gen.py` | Generates AI equivalents for human-written paragraphs using OpenAI API. |
| `evaluation.py` | Calculates Levenshtein Distance (LD) and Cosine Similarity (CS) across the dataset. |
| `gpt_evaluation.py` | Feeds paragraphs into GPT to simulate a binary AI/HUMAN classifier and measures performance. |
| `reader.py` | Allows you to view any stored article from a dataset by selecting its ID. |
| `dataset_management.py` | Includes options to list, rename, remove, or merge dataset JSON files. |
| `category_finder.py` | Scrapes available category codes from arXiv’s taxonomy page. |
| `data_cleaning.py` | Handles content processing like whitespace, newline, and any other symbols cleanup. |
| `HTML_processing.py` | Reads and processes raw HTML content from arXiv into structured sections and paragraphs with text. |

---

### Folder Descriptions

| Folder | Description |
|--------|-------------|
| `evaluation_reports/` | JSON files with the results of CS/LD and GPT classification evaluations. |
| `graphs/` | Jupyter Notebook file along with the visualizations and plots generated from evaluation results. |
| `old_implementation_attempts/` | Previous versions and discarded prototype logic. |
| `data/` | Attempts at collecting data using the previous deprecated methods. |
| `scrappers/` | Old code for scraping data from arXiv and Core repositories, which is not longer used. |
| `openAI/` | Earlier attempts at generating AI version of human text, which have not been used in the final implementation. |

---

### Key Data Files

| File | Description |
|------|-------------|
| `first_5_subset.json`, `middle_5_subset.json`, `last_5_subset.json` | Example subsets extracted from the main dataset used for evaluation testing. |
| `the_dataset.json` | The full combined dataset of human and AI-paragraph pairs. |
| `.env` | Contains OpenAI API key and generation settings (model, prompt, max tokens).|

---

## Evaluation Approach

- **CS vs. LD Metrics**: Each paragraph pair (human vs. AI) is evaluated for similarity and structural difference.
- **GPT Detection**: Both human and AI content is fed back into GPT acting as a binary classifier, to try simulate detection performance.
- Reports are saved as JSON in `evaluation_reports/` and visualized in `graphs/`.

---

## Getting Started

1. Clone the repo  
2. Add your OpenAI credentials to a `.env` file  
3. Run `main.py` and follow the CLI options to scrape, generate, view, or evaluate your dataset

Example `.env`:
```env
OPENAI_API_KEY=...
MODEL=gpt-4o
MAX_TOKENS=600
PROMPT=Rewrite the following paragraph...
