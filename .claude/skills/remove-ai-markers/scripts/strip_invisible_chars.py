#!/usr/bin/env python3
"""Strip invisible/zero-width Unicode characters sometimes left by AI text
generation or watermarking tools, and normalize a few punctuation marks
that read as obviously machine-generated in Korean resume documents.

Usage:
    python3 strip_invisible_chars.py <file> [--write]

Without --write, prints a diff-like report and does not modify the file.
With --write, overwrites the file in place with the cleaned text.
"""
import argparse
import sys

INVISIBLE_CHARS = {
    "​": "ZERO WIDTH SPACE",
    "‌": "ZERO WIDTH NON-JOINER",
    "‍": "ZERO WIDTH JOINER",
    "‎": "LEFT-TO-RIGHT MARK",
    "‏": "RIGHT-TO-LEFT MARK",
    "⁠": "WORD JOINER",
    "⁡": "FUNCTION APPLICATION",
    "⁢": "INVISIBLE TIMES",
    "⁣": "INVISIBLE SEPARATOR",
    "⁤": "INVISIBLE PLUS",
    "﻿": "ZERO WIDTH NO-BREAK SPACE (BOM)",
    "­": "SOFT HYPHEN",
}

PUNCTUATION_NORMALIZATION = {
    "—": "-",   # em dash -> hyphen
    "–": "-",   # en dash -> hyphen
    "‘": "'",   # left single quote
    "’": "'",   # right single quote
    "“": '"',   # left double quote
    "”": '"',   # right double quote
    "…": "...",  # ellipsis
}


def clean(text: str):
    found = {}
    out_chars = []
    for ch in text:
        if ch in INVISIBLE_CHARS:
            found[ch] = found.get(ch, 0) + 1
            continue
        if ch in PUNCTUATION_NORMALIZATION:
            found.setdefault(ch, 0)
            found[ch] += 1
            out_chars.append(PUNCTUATION_NORMALIZATION[ch])
            continue
        out_chars.append(ch)
    return "".join(out_chars), found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="Path to the text file to check/clean")
    parser.add_argument("--write", action="store_true", help="Overwrite the file with cleaned text")
    args = parser.parse_args()

    with open(args.file, "r", encoding="utf-8") as f:
        text = f.read()

    cleaned, found = clean(text)

    if not found:
        print(f"No invisible/AI-watermark characters found in {args.file}.")
        return

    print(f"Found suspicious characters in {args.file}:")
    for ch, count in found.items():
        name = INVISIBLE_CHARS.get(ch) or PUNCTUATION_NORMALIZATION.get(ch, repr(ch))
        print(f"  U+{ord(ch):04X} ({name}): {count} occurrence(s)")

    if args.write:
        with open(args.file, "w", encoding="utf-8") as f:
            f.write(cleaned)
        print(f"\nCleaned text written back to {args.file}.")
    else:
        print("\nRun again with --write to overwrite the file with cleaned text.")


if __name__ == "__main__":
    sys.exit(main())
