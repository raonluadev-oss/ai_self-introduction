#!/usr/bin/env python3
"""Strip invisible/steganographic Unicode characters that some AI writing
and detection tools use as hidden watermarks, and report what was found.

Usage:
    python3 strip_invisible_chars.py < input.txt > cleaned.txt
    python3 strip_invisible_chars.py input.txt          # writes <input>.clean.txt

Always prints a report to stderr, including any hidden ASCII payload decoded
from Unicode tag characters (a known steganographic channel) so the user can
see what was actually hidden in the text before it is discarded.
"""
import sys

# Characters silently removed by default: zero-width/invisible formatting
# characters with no visible effect on normal text.
ZERO_WIDTH = {
    0x200B: "ZERO WIDTH SPACE",
    0x200C: "ZERO WIDTH NON-JOINER",
    0x200D: "ZERO WIDTH JOINER",
    0x2060: "WORD JOINER",
    0x2061: "FUNCTION APPLICATION",
    0x2062: "INVISIBLE TIMES",
    0x2063: "INVISIBLE SEPARATOR",
    0x2064: "INVISIBLE PLUS",
    0xFEFF: "ZERO WIDTH NO-BREAK SPACE / BOM",
    0x180E: "MONGOLIAN VOWEL SEPARATOR",
    0x00AD: "SOFT HYPHEN",
}

# Unicode tag characters (U+E0001, U+E0020-U+E007F): no legitimate use in
# plain text; historically used to smuggle hidden ASCII payloads inside
# ordinary-looking text (each tag char maps back to an ASCII byte).
TAG_START, TAG_END = 0xE0000, 0xE007F

# Variation Selectors Supplement (U+E0100-U+E01EF): no standard use outside
# Ideographic Variation Sequences; also used as a hidden byte-encoding
# channel similar to tag characters.
VS_SUPP_START, VS_SUPP_END = 0xE0100, 0xE01EF

# Base-plane variation selectors (U+FE00-U+FE0F): legitimately used for
# emoji presentation, so we only *count* these, never strip them.
VS_BASE_START, VS_BASE_END = 0xFE00, 0xFE0F


def decode_tag_payload(codepoints):
    """Tag characters encode ASCII by offset from U+E0000."""
    chars = []
    for cp in codepoints:
        if cp == 0xE0001:
            continue  # LANGUAGE TAG marker, not a payload byte
        ascii_val = cp - 0xE0000
        if 0x20 <= ascii_val <= 0x7E:
            chars.append(chr(ascii_val))
    return "".join(chars)


def clean(text):
    removed_zw = {}
    tag_codepoints = []
    vs_supp_count = 0
    vs_base_count = 0
    out = []

    for ch in text:
        cp = ord(ch)
        if cp in ZERO_WIDTH:
            removed_zw[cp] = removed_zw.get(cp, 0) + 1
            continue
        if TAG_START <= cp <= TAG_END:
            tag_codepoints.append(cp)
            continue
        if VS_SUPP_START <= cp <= VS_SUPP_END:
            vs_supp_count += 1
            continue
        if VS_BASE_START <= cp <= VS_BASE_END:
            vs_base_count += 1
            out.append(ch)  # kept: legitimate emoji use
            continue
        out.append(ch)

    report = []
    total_zw = sum(removed_zw.values())
    if total_zw:
        report.append(f"invisible formatting characters removed: {total_zw}")
        for cp, count in sorted(removed_zw.items()):
            report.append(f"  U+{cp:04X} {ZERO_WIDTH[cp]}: {count}")
    if tag_codepoints:
        payload = decode_tag_payload(tag_codepoints)
        report.append(f"Unicode TAG steganography characters removed: {len(tag_codepoints)}")
        if payload:
            report.append(f"  decoded hidden payload: {payload!r}")
    if vs_supp_count:
        report.append(
            f"Variation Selectors Supplement (hidden byte channel) removed: {vs_supp_count}"
        )
    if vs_base_count:
        report.append(
            f"base-plane variation selectors kept (legitimate emoji use), found: {vs_base_count}"
        )
    if not report:
        report.append("no invisible/steganographic characters found")

    return "".join(out), "\n".join(report)


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        cleaned, report = clean(text)
        out_path = path + ".clean.txt" if not path.endswith(".txt") else path[:-4] + ".clean.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(cleaned)
        print(f"cleaned text written to: {out_path}", file=sys.stderr)
    else:
        text = sys.stdin.read()
        cleaned, report = clean(text)
        sys.stdout.write(cleaned)

    print("---", file=sys.stderr)
    print(report, file=sys.stderr)


if __name__ == "__main__":
    main()
