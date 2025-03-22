#AFTER  2503.03498 error => complete maths handling
import unicodedata
import re
import ftfy
from pylatexenc.latex2text import LatexNodes2Text


#normalize Unicode text and fix problematic characters
def decode_unicode(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("ﬂ", "fl").replace("ﬁ", "fi")  
    text = text.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")  
    text = text.replace("−", "-").replace("—", "-").replace("–", "-")  
    text = text.replace("\xad", "")  
    text = re.sub(r'[\u200B\u2060\uFEFF]', '', text)  
    return text

#fix any word splits caused by line breaks
def fix_word_splits(text):
    return re.sub(r"(\w+)-\s+(\w+)", r"\1\2", text)

#convert Latex math expressions
def convert_latex_math(text):

    def replace_inline(match):
        latex_expr = match.group(1)
        try:
            return f"${LatexNodes2Text().latex_to_text(latex_expr)}$"
        except Exception:
            return match.group(0)

    def replace_block(match):
        latex_expr = match.group(1)
        try:
            return f"$$ {LatexNodes2Text().latex_to_text(latex_expr)} $$"
        except Exception:
            return match.group(0)

    text = re.sub(r"\\\((.*?)\\\)", replace_inline, text)
    text = re.sub(r"\\\[(.*?)\\\]", replace_block, text)

    #replacements for common symbols
    text = text.replace(r"\phi", "φ").replace(r"\theta", "θ").replace(r"\alpha", "α").replace(r"\beta", "β")
    text = text.replace(r"\gamma", "γ").replace(r"\delta", "δ").replace(r"\lambda", "λ").replace(r"\mu", "μ")
    text = text.replace(r"\pi", "π").replace(r"\sigma", "σ").replace(r"\tau", "τ").replace(r"\Omega", "Ω")
    text = text.replace(r"\in", "∈").replace(r"\cdot", "·").replace(r"\times", "×").replace(r"\pm", "±")
    text = text.replace(r"\int", "∫").replace(r"\sum", "∑").replace(r"\prod", "∏").replace(r"\frac", "/")

    return text

def remove_control_characters(text):
    return re.sub(r"[\x00-\x1F\x7F-\x9F]", "", text)

def clean_inline_latex(text):

    #subscripts and superscripts
    text = re.sub(r'_{(\w+)}', r'_\1', text)
    text = re.sub(r'\^{(\w+)}', r'^\1', text)

    #remove \mathbf, \text, etc
    text = re.sub(r'\\(text|mathbf|mathit|mathrm){([^}]*)}', r'\2', text)

    #remove \quad 
    text = re.sub(r'\\quad', ' ', text)

    #remove double backslashes
    text = text.replace('\\\\', '\\')

    return text


def simplify_inline_math(text):

    #subscripts (x_{i} -> x_i)
    text = re.sub(r'_{(\w+)}', r'_\1', text)

    #superscripts (x^{i} -> x^i)
    text = re.sub(r'\^{(\w+)}', r'^\1', text)

    # sum/product/integral limits (∑_{i=1}^{n} -> ∑_i=1^n)
    text = re.sub(r'\\(sum|prod|int)_{(.*?)}\^{(.*?)}', r'\1_\2^\3', text)

    #remove any backslashes left over
    text = text.replace('\\', '')

    return text

#all cleaning
def clean_text(text):
    text = ftfy.fix_text(text)
    text = decode_unicode(text)
    text = clean_inline_latex(text)  
    text = simplify_inline_math(text)  

 
    text = re.sub(r'\\[a-zA-Z]+', '', text) 
    text = re.sub(r'\$\$?.*?\$\$?', '', text)  

    text = fix_word_splits(text)
    text = convert_latex_math(text)
    text = remove_control_characters(text)

    text = text.replace('\"', '“').replace('\'', '’')  

    text = re.sub(r'\s+', ' ', text).strip() 

    
    #brackets around simple variables
    text = re.sub(r'\(\s*(\\?[a-zA-Z]+(?:\{.*?\})?)\s*\)', r'\1', text)

    #brackets from LaTeX variables like ( Lambda )
    text = re.sub(r'\(\s*([a-zA-Z0-9_\\\^\{\}]+)\s*\)', r'\1', text)

    text = re.sub(r'(mathcal|mathbb|mathrm|mathbf|operatorname)\s*\{([^}]+)\}', r'\2', text)

    greek_map = {
        "Lambda": "Λ", "Sigma": "Σ", "Gamma": "Γ", "Delta": "Δ", "Omega": "Ω",
        "lambda": "λ", "sigma": "σ", "gamma": "γ", "delta": "δ", "omega": "ω",
        "phi": "φ", "theta": "θ", "alpha": "α", "beta": "β", "tau": "τ", "mu": "μ",
        "pi": "π"
    }
    for word, symbol in greek_map.items():
        text = re.sub(rf'\b{word}\b', symbol, text)


    return text


