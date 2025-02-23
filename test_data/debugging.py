import json
import re
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

def load_articles(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def save_debug_output(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def identify_sections(content):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
            "role": "system",
            "content": "You are an expert in extracting section titles from academic papers. "
                        "Your task is to accurately identify and list section titles without hallucinating or "
                        "misplacing sections. Maintain the correct order and avoid creating section breaks in the middle of a paragraph."
            },
            {"role": "user", 
            "content": f"""Extract section titles from the following academic paper excerpt:
            {content}

            **Guidelines:**
            - **Return ONLY section titles that actually appear in the text.** Do NOT create new section titles.
            - **Maintain the order of sections as they appear.**
            - **Do NOT split paragraphs incorrectly.** If a section title is ambiguous or unclear, ignore it.
            - **Ensure that 'References' or similar sections are separate and not merged with other content.**
            - If no clear sections exist, return `"Full Document"`."""}
        ]
    )

    section_list = response.choices[0].message.content.strip()
    return [title.strip() for title in section_list.split("\n")]

def format_regex_pattern(section_titles):
    formatted_titles = [re.escape(title).replace(r"\ ", r"\s*") for title in section_titles]
    regex_pattern = "|".join(formatted_titles)
    return regex_pattern

def split_content(content, section_titles):
    if not section_titles or section_titles == ["Full Document"]:
        print("No section titles detected. Treating as full document.")
        return [("Full Document", content)]

    print("\nIdentified Sections:")
    for section in section_titles:
        print(f" - {section}")

    regex_pattern = format_regex_pattern(section_titles)
    print(f"\nRegex Pattern Used: {regex_pattern}")

    split_sections = re.split(f"({regex_pattern})", content)

    structured_sections = []
    for i in range(1, len(split_sections), 2):
        title = split_sections[i].strip()
        text = split_sections[i + 1].strip() if i + 1 < len(split_sections) else ""
        structured_sections.append((title, f"{title} {text}"))

    return structured_sections

articles = load_articles('../data/broken.json')
debug_output = []

for article_index, article_data in enumerate(articles, start=1):
    print(f"\nProcessing Paper {article_index}/{len(articles)}")

    article_content = article_data['contents']
    section_titles = identify_sections(article_content)

    split_sections = split_content(article_content, section_titles)

    print("\nsplit Sections Debugging:")
    for idx, (title, content) in enumerate(split_sections):
        preview = content[:200].replace("\n", " ") 
        print(f"Section {idx}: {title}")
        print(f"Content Preview: {preview}...\n")

    debug_output.append({
        "article_id": article_data["article_id"],
        "name": article_data["name of paper"],
        "identified_sections": section_titles,
        "regex_pattern": format_regex_pattern(section_titles),
        "split_sections": [{"title": title, "content": content} for title, content in split_sections]
    })

save_debug_output('../test_data/debug.json', debug_output)

print("debugging output saved to /test_data/debug.json")
