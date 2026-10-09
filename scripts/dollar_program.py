import re
import os
import sys

WS = r"[ \t\n]+"        # whitespace, may span a line break
SP = r"[ \t\n-]+"       # whitespace or hyphen

# ––– number words –––
ONES = r"(?:one|two|three|four|five|six|seven|eight|nine)"
TEENS = r"(?:ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen)"
TENS = r"(?:twenty|thirty|forty|fourty|fifty|sixty|seventy|eighty|ninety)"
LARGE = r"(?:thousand|million|billion|trillion)"

# 1–99
SMALL = rf"(?:{TENS}(?:{SP}{ONES})?|{TEENS}|{ONES})\b"

# 100–999
HUND = rf"(?:(?:{SMALL}{SP})?hundred(?:(?:{SP}|{WS}and{WS}){SMALL})?|{SMALL})"

# one group with an optional scale
GROUP = rf"(?:{HUND}(?:(?:{WS}and{WS}a{WS}half)?{SP}{LARGE}\b)?|{LARGE}\b)"

# a scale can be followed by another group
AFTER_LARGE = r"(?:(?<=thousand)|(?<=million)|(?<=billion)|(?<=trillion))"
WORDNUM = rf"{GROUP}(?:{AFTER_LARGE}(?:{SP}|,?{WS}and{WS}){GROUP})*"

# words that only work pre-scale
QUANT = (
    r"(?:an?|half\s+an?|(?:a\s+)?few|(?:a\s+)?couple(?:\s+of)?|several|many|some)"
)
WORDNUM_Q = rf"(?:{QUANT}{SP}(?=(?:hundred|{LARGE})\b))?{WORDNUM}"

# ––– numerals –––
NUMERAL = r"(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)"
NUMERAL_Q = rf"{NUMERAL}(?:{SP}(?:hundred|{LARGE})\b)*"
QUANTITY = rf"(?:{NUMERAL_Q}|{WORDNUM_Q})(?:{WS}and{WS}a{WS}half)?"
ARTICLE = r"(?:half[ \t\n]+)?an?"
AMOUNT = rf"(?:{QUANTITY}|{ARTICLE})"

# ––– currency vocab (not sure if all needed) –––
NATION = (
    r"(?:U\.S\.|US|American|Canadian|Australian|New\s+Zealand|Hong\s+Kong|"
    r"Singapore(?:an)?|New\s+Taiwan|Taiwan(?:ese)?|Spanish|Mexican|Jamaican|"
    r"Liberian|Zimbabwe(?:an)?|Bahamian|Barbad(?:os|ian)|Belize(?:an)?|"
    r"Bermud(?:a|ian)|Brunei|Cayman(?:\s+Islands)?|Fiji(?:an)?|Guyan(?:a|ese)|"
    r"Namibian|Trinidad(?:\s+and\s+Tobago)?|(?:East(?:ern)?\s+)?Caribbean|"
    r"Solomon\s+Islands|international|Confederate)"
)

# letters that come pre-"$"
PREFIX = (
    r"(?:U\.S\.|US|HK|NZ|NT|Can|CA|CDN|AU|EC|TT|BZ|Bds|FJ|SI|SG|S|C|A|I|J|Z|N|L|B)"
)

# ISO 4217 codes for dollar currencies
CODES = (
    r"(?:USD|CAD|AUD|NZD|HKD|SGD|TWD|JMD|BSD|BBD|BZD|BMD|BND|FJD|GYD|LRD|NAD|TTD|XCD|ZWD|KYD|SBD)"
)
DOLLAR_WORD = r"(?:dollars?|bucks)\b"
CENT_WORD = r"cents?\b"

# scale post-"$" amount
SIGN_SCALE = (
    rf"(?:[ \t\n-]?(?:hundred|{LARGE})s?\b"
    rf"(?:{WS}(?:(?:US|U\.S\.){WS})?dollars?\b)?"
    r"|[ ]?(?:bn|mn|mln|mil|tn)\b|(?-i:[KkMmB])\b)"
)

# reject inflation base years
NOT_YEAR_REF = rf"(?!(?:1[89]|20)\d\d{SP}(?:{NATION}{WS})?dollar)"

# ––– patterns –––
SIGN_AMOUNT = rf"(?-i:{PREFIX})?\$[ ]?{NUMERAL}(?<![.,]){SIGN_SCALE}?"
CODE_AMOUNT = (
    rf"(?-i:{CODES})[ ]?{NUMERAL_Q}"
    rf"|{NUMERAL_Q}[ ]?(?-i:{CODES})\b"
)
WORD_AMOUNT = rf"(?<!-){NOT_YEAR_REF}{AMOUNT}{SP}(?:{NATION}{WS})?{DOLLAR_WORD}"
VAGUE_AMOUNT = (
    rf"(?:(?:tens|hundreds|thousands|millions|billions|trillions){WS}of{WS})+"
    rf"(?:{NATION}{WS})?dollars\b"
)
CENT_AMOUNT = rf"(?<!-){AMOUNT}{SP}(?:(?:US|U\.S\.){WS})?{CENT_WORD}"
CENT_TAIL = rf"(?:,?{WS}and{WS}(?:{CENT_AMOUNT}|a{WS}half\b))?"
DOLLAR_REGEX = (
    r"(?<!\w)(?:"
    rf"(?:{SIGN_AMOUNT}|{WORD_AMOUNT}|{VAGUE_AMOUNT}){CENT_TAIL}"
    rf"|{CODE_AMOUNT}"
    rf"|{CENT_AMOUNT}"
    r")(?![\w$])"
)
DOLLAR_RE = re.compile(DOLLAR_REGEX, re.IGNORECASE)

def find_dollars(text):
    "yield each $ amount in text, ws normalized"
    for m in DOLLAR_RE.finditer(text):
        yield " ".join(m.group(0).split())

def main(argv):
    if len(argv) < 2:
        sys.exit("usage: python3 dollar_program.py INPUT.txt [OUTPUT.txt]")
    in_path = argv[1]
    out_path = argv[2] if len(argv) > 2 else "output/dollar_output.txt"
    os.makedirs("output", exist_ok=True)
    with open(in_path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    matches = list(find_dollars(text))
    with open(out_path, "w", encoding="utf-8") as out:
        for s in matches:
            out.write(s + "\n")
    for s in matches:
        print(s)
    print(f"[{len(matches)} dollar amounts written to {out_path}]", file=sys.stderr)

if __name__ == "__main__":
    main(sys.argv)