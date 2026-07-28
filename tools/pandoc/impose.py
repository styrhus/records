#!/usr/bin/env python3
"""Booklet imposition: place the pages of a PDF two-up on A4 landscape sheets
in folding order, so the duplex-printed stack (flip on short edge) folds in
half into a booklet. Page count is padded to a multiple of 4 with the filler
page (a page-coloured blank) or white if none is given. --pad-before-last
inserts the padding before the final page instead, keeping it the back cover.

Usage: impose.py [--pad-before-last] input.pdf output.pdf [blank.pdf]
"""
import sys

from pypdf import PdfReader, PdfWriter, Transformation

A4_W, A4_H = 841.8898, 595.2756  # A4 landscape in points


def main():
    args = [a for a in sys.argv[1:] if a != "--pad-before-last"]
    pad_before_last = len(args) < len(sys.argv) - 1
    src, dst = args[0], args[1]
    pages = list(PdfReader(src).pages)
    filler = PdfReader(args[2]).pages[0] if len(args) > 2 else None
    at = len(pages) - 1 if pad_before_last and pages else len(pages)
    while len(pages) % 4:
        pages.insert(at, filler)

    writer = PdfWriter()
    n = len(pages)
    for k in range(n // 4):
        # sheet k front: [n-2k, 2k+1]; back: [2k+2, n-2k-1] (1-based pages)
        for left, right in ((pages[n - 2 * k - 1], pages[2 * k]),
                            (pages[2 * k + 1], pages[n - 2 * k - 2])):
            sheet = writer.add_blank_page(A4_W, A4_H)
            for page, x in ((left, 0.0), (right, A4_W / 2)):
                if page is None:
                    continue
                w = float(page.mediabox.width)
                h = float(page.mediabox.height)
                ctm = Transformation().scale(A4_W / 2 / w, A4_H / h).translate(x, 0)
                sheet.merge_transformed_page(page, ctm)

    with open(dst, "wb") as f:
        writer.write(f)


if __name__ == "__main__":
    main()
