import requests
from bs4 import BeautifulSoup
import re

def getParaText(paraDiv):
    str = paraDiv.get_text("").strip()
    return re.sub("\n+", "\n", str)

def retrievePage(pageUrlStr):
    tempPage = requests.get(pageUrlStr)

    soupPage = BeautifulSoup(tempPage.content, "html.parser")

    articleTag = soupPage.find("article", class_="ltx_document")

    maths = articleTag.find_all("math", class_="ltx_Math")
    for mathTag in maths:
        tag = mathTag.find("mrow")
        if tag: tag.decompose()
        tag = mathTag.find("annotation-xml")
        if tag: tag.decompose()
        tag = mathTag.find("annotation", {"encoding": ["application/x-llamapun"]})
        if tag: tag.decompose()

    abstractTag = articleTag.find("div", class_="ltx_abstract", recursive=False)
    abstractP = abstractTag.find("p", class_="ltx_p", recursive=False)
    print("======== ABSTRACT")
    print(abstractP.text.strip())

    sections = articleTag.find_all("section", "ltx_section", recursive=False)
    for sectionTag in sections:
        sectionHTwo = sectionTag.find("h2", class_="ltx_title", recursive=False)
        print(f"=== {sectionHTwo.get_text().strip()}")

        paras = sectionTag.find_all("div", class_="ltx_para", recursive=False)
        for paraDiv in paras:
            paraStr = getParaText(paraDiv)
            print("======== Paragraph")
            print(paraStr)

        subsecs = sectionTag.find_all("section", class_="ltx_subsection", recursive=False)
        for subsecTag in subsecs:
            subSecHThree = subsecTag.find("h3", class_="ltx_title", recursive=False)
            print(f"=== === {subSecHThree.get_text().strip()}")

            paras = subsecTag.find_all("div", class_="ltx_para", recursive=False)
            for paraDiv in paras:
                paraStr = getParaText(paraDiv)
                print("======== Paragraph")
                print(paraStr)

            subsubsecs = subsecTag.find_all("section", class_="ltx_paragraph", recursive=False)
            for subsubTag in subsubsecs:
                subsubHFive = subsubTag.find("h5", class_="ltx_title", recursive=False)
                print(f"=== === === {subsubHFive.get_text().strip()}")

                paras = subsubTag.find_all("div", class_="ltx_para", recursive=False)
                for paraDiv in paras:
                    paraStr = getParaText(paraDiv)
                    print("======== Paragraph")
                    print(paraStr)

# retrievePage("https://arxiv.org/html/2503.00566v1")
# retrievePage("https://arxiv.org/html/2503.00248v1")
# retrievePage("https://arxiv.org/html/2503.00237v1")
# retrievePage("https://arxiv.org/html/2502.14866v1")
# retrievePage("https://arxiv.org/html/2503.06862v1")
retrievePage("https://arxiv.org/html/2503.07601")