import re
import os
import sys

# ––– shared pieces –––
SPACE = r"(?:[ ]?\n[ \t]*|[ ])"
EXT = r"(?:[ ]?,?[ ]?(?:ext\.?|extension|x)[ ]?\d{1,5}\b)?"

START = r"(?<![\w$])(?<!\d[-./(])"
END = r"(?![\w])(?![-./]\d)"

# ––– north american –––
COUNTRY = r"(?:\+?1[ .-]?)"
PAREN_AREA = rf"(?:\([2-9]\d{{2}}\)|\[[2-9]\d{{2}}\]){SPACE}?"
BARE_AREA = rf"[2-9]\d{{2}}(?:[/-]{SPACE}?|\.|{SPACE})"
EXCHANGE = r"[2-9]\d{2}"
LINE = r"\d{4}"

NANP_WITH_AREA = (
    rf"{COUNTRY}?(?:{PAREN_AREA}{EXCHANGE}[ .-]?{LINE}"
    rf"|{BARE_AREA}{EXCHANGE}(?:[ .-]|{SPACE}){LINE})"
)
RANGE_BEFORE = r"(?<!residues )(?<!acids )(?<!positions )(?<!nucleotides )(?<!from )(?<!between )(?<!pages )(?<!pp\. )"
RANGE_AFTER = r"(?!\s+(?:of|bp|kb|nt|aa|nucleotides|residues|amino)\b)"
NANP_LOCAL = rf"{RANGE_BEFORE}(?!\d00-\d\d00\b){EXCHANGE}-{LINE}{RANGE_AFTER}"

# ––– vanity numbers ––
VANITY_AREA = rf"(?:{COUNTRY}?8(?:00|88|77|66|55|44|33)[ .-]|{COUNTRY}?{PAREN_AREA})"
VANITY_BODY = (
    r"(?-i:(?=(?:[A-Z0-9]-?){7,11}(?![\w-]))"
    r"(?=[\d-]*[A-Z])"
    r"[A-Z0-9]+(?:-[A-Z0-9]+){0,3})"
)
VANITY = rf"{VANITY_AREA}{VANITY_BODY}"

# ––– international w/ "+" –––
INTL = r"\+(?!1\b)[2-9]\d{0,2}(?:[ .-]?(?:\(\d{1,4}\)|\d{1,4})){2,6}"
PHONE_REGEX = (
    rf"{START}(?:"
    rf"{VANITY}"
    rf"|(?:{NANP_WITH_AREA}|{NANP_LOCAL}){EXT}"
    rf"|{INTL}"
    rf"){END}"
)

# ––– loose numbers post-cue –––
CUE = (
    r"\b(?:tel(?:ephone)?|phones?|ph|fax(?:es)?|facsimile|call|"
    r"toll[- ]free|hotline|voice|TDD|TTY|contact)\b\.?"
)
FILLER = (
    r"(?:\s*[:.]?\s*"
    r"(?:(?:numbers?|nos?\.|is|at|on|us|me|them|toll[- ]free|voice|TDD|"
    r"\(toll[- ]free\))\s*[:.]?\s*){0,3})"
)
LOOSE = (
    rf"\+?(?:\(\d{{1,5}}\){SPACE}?)?\d{{1,8}}"
    rf"(?:(?:[./-]|{SPACE})(?:\(\d{{1,5}}\)|\d{{1,8}})){{0,5}}"
)
CUED_NUMBER = rf"(?P<num>(?:{PHONE_REGEX}|{START}{LOOSE}{EXT}{END}))"
CUED_REGEX = rf"{CUE}{FILLER}{CUED_NUMBER}"
NEXT_IN_LIST = rf"[ \t]*(?:,|;|or|and|/)\s*{CUED_NUMBER}"

PHONE_RE = re.compile(PHONE_REGEX, re.IGNORECASE)
CUED_RE = re.compile(CUED_REGEX, re.IGNORECASE)
NEXT_RE = re.compile(NEXT_IN_LIST, re.IGNORECASE)

def digit_count(s):
    return sum(c.isdigit() for c in s)

def plausible(s):
    """digit-count check: exp. 7–15 (5+ for cued local nums)"""
    n = digit_count(s.split("x")[0].split("ext")[0])
    return 5 <= n <= 15

def find_phones(text):
    spans = []
    for m in PHONE_RE.finditer(text):
        s = m.group(0)
        if s.startswith("+") and not 8 <= digit_count(s) <= 15:
            continue
        spans.append(m.span())
    for m in CUED_RE.finditer(text):
        while m:
            if plausible(m.group("num")):
                spans.append(m.span("num"))
            m = NEXT_RE.match(text, m.end("num"))
    spans.sort(key=lambda sp: (sp[0], -sp[1]))
    kept = []
    for a, b in spans:
        if kept and a < kept[-1][1]:
            if b > kept[-1][1] and b - a > kept[-1][1] - kept[-1][0]:
                kept[-1] = (a, b)
            continue
        kept.append((a, b))
    for a, b in kept:
        yield " ".join(text[a:b].strip(" .-/\n\t").split())

def main(argv):
    if len(argv) < 2:
        sys.exit("usage: python3 telephone_regexp.py INPUT.txt [OUTPUT.txt]")
    in_path = argv[1]
    out_path = argv[2] if len(argv) > 2 else "output/telephone_output.txt"
    os.makedirs("output", exist_ok=True)
    with open(in_path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    matches = list(find_phones(text))
    with open(out_path, "w", encoding="utf-8") as out:
        for s in matches:
            out.write(s + "\n")
    for s in matches:
        print(s)
    print(f"[{len(matches)} telephone numbers written to {out_path}]", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv)