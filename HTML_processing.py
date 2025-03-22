import requests
from bs4 import BeautifulSoup
import logging
from data_cleaning import clean_text
from pylatexenc.latex2text import LatexNodes2Text
import re
import logging

logging.getLogger("pylatexenc.latexwalker").setLevel(logging.ERROR)
logging.basicConfig(level=logging.ERROR)

#extract latex content from math tags
def flatten_math(mathTag):
    """Extracts and cleans LaTeX math expressions."""
    for tag_name in ["mrow", "annotation-xml", "annotation"]:
        for tag in mathTag.find_all(tag_name):
            tag.decompose()  

    math_text = " ".join(mathTag.stripped_strings)  
    try:
        return LatexNodes2Text().latex_to_text(math_text)  
    except Exception as e:
        logging.warning(f"Failed to convert latex: {math_text} - Error: {e}")
        return math_text


#checks if a paragraph contains a structured format (lists, code, etc..)
def is_multiline_structure(paraDiv):
    return paraDiv.find(["ul", "ol", "pre"]) is not None


#extracts paragraph text while cleaning math expressions and detecting multiline structures
def getParaTextWithMath(paraDiv):
    
    for tag_name in ["span", "mrow", "annotation-xml", "annotation"]:
        for tag in paraDiv.find_all(tag_name):
            tag.decompose()  

    for boldTag in paraDiv.find_all(["b", "strong"]):
        boldTag.insert_before(f" {boldTag.get_text().strip()} ")  #keep bold text 

    for italicTag in paraDiv.find_all(["i", "em"]):
        italicTag.insert_before(f" {italicTag.get_text().strip()} ")  #keep italic text 

    for mathTag in paraDiv.find_all("math"):
        math_text = flatten_math(mathTag)
        mathTag.replace_with(f" {math_text} ")  #readable math text

    #detect multilinear structures and flag 
    multilinear = 1 if is_multiline_structure(paraDiv) else 0

    return clean_text(paraDiv.get_text("").strip()), multilinear  



def is_valid_paragraph(text):
    cleaned_text = text.strip()
    if len(cleaned_text) < 5 or len(cleaned_text.split()) < 3 or re.match(r'^[\W_]+$', cleaned_text):
        return False
    return True



def get_section_title(sectionTag):

    titleTag = sectionTag.find(["h2", "h3", "h4", "h5", "h6"], class_="ltx_title", recursive=False)
    if titleTag:
        section_name = titleTag.get_text().strip()
        if section_name:
            return clean_text(section_name)

    titleDiv = sectionTag.find("div", class_="ltx_title", recursive=False)
    if titleDiv:
        section_name = titleDiv.get_text().strip()
        if section_name:
            return clean_text(section_name)


    return f"Untitled Section"


def process_section(sectionTag, section_name, section_counter, article_contents):
    
    #gett the section title (ensured to be non-empty)
    section_name = get_section_title(sectionTag)  
    section_counter[section_name] = section_counter.get(section_name, 0)

    #extract paragraphs
    paras = sectionTag.find_all("div", class_="ltx_para", recursive=False)
    for paraDiv in paras:
        try:
            paraStr, multilinear = getParaTextWithMath(paraDiv)
            if is_valid_paragraph(paraStr):
                section_counter[section_name] += 1
                article_contents.append({
                    "section": section_name,
                    "paragraph": section_counter[section_name],
                    "multilinear": multilinear,
                    "human": [paraStr],
                    "ai": []
                })
        except Exception as e:
            logging.warning(f"Failed processing paragraph in section '{section_name}': {e}")

    #process nested subsections
    nested_sections = sectionTag.find_all("section", recursive=False)
    for nested_section in nested_sections:
        process_section(nested_section, section_name, section_counter, article_contents)





#handles HTML processing and extracts structured & normal paragraphs
def process_article_html(article_id, html_url, existing_data):
    response = requests.get(html_url, timeout=15)

    if response.status_code == 404:
        return existing_data  #skip article if HTML is missing

    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    articleTag = soup.find("article", class_="ltx_document")

    if not articleTag:
        return existing_data  #skip if article tag is missing

    article_contents = []
    section_counter = {}

    #process abstract
    abstractTag = articleTag.find("div", class_="ltx_abstract", recursive=False)
    if abstractTag:
        abstractP = abstractTag.find("p", class_="ltx_p", recursive=False)
        if abstractP:
            paraStr, multilinear = getParaTextWithMath(abstractP)
            if is_valid_paragraph(paraStr):
                article_contents.append({
                    "section": "Abstract",
                    "paragraph": 1,
                    "multilinear": multilinear,
                    "human": [paraStr],
                    "ai": []
                })

    #process sections
    sections = articleTag.find_all("section", "ltx_section", recursive=False)
    for sectionTag in sections:
        sectionHTwo = sectionTag.find("h2", class_="ltx_title", recursive=False)
        if sectionHTwo:
            section_name = getParaTextWithMath(sectionHTwo)[0]
            section_counter[section_name] = section_counter.get(section_name, 0)
            process_section(sectionTag, section_name, section_counter, article_contents)

    #skip empty content
    if not article_contents:
        return existing_data  

    existing_data[article_id] = article_contents
    return existing_data
