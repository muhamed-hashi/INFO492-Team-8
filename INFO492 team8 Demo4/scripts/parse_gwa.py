"""Parse the public GWA 'Response to RFI No. 1' PDF (IFB-06-ENG-2026) into data/gwa/rfi1_items.json.

    pip install pdfplumber pytesseract   (and the tesseract program)
    python3 scripts/parse_gwa.py RFI_No._1_for_IFB-06-ENG-2026.pdf data/gwa/rfi1_items.json

The PDF is a table: NO. | DATE | QUESTION/INQUIRY | RESPONSE. Many questions paste in a picture of the report they
ask about (and item 37's answer is only a picture). Those pictures are read with OCR and kept separately
(question_picture_text / response_picture_text) so the checker sees what a reader of the PDF sees, and so anyone
can tell typed text from OCR text. OCR text is imperfect; that is part of the real data.
"""
import json, re, sys
import pdfplumber
import pytesseract

COL_DATE, COL_RESPONSE = (60, 110), 371.5


def ocr(page, im):
    box = (max(im['x0'], 0), max(im['top'], 0), min(im['x1'], page.width), min(im['bottom'], page.height))
    pic = page.crop(box).to_image(resolution=300).original
    return ' '.join(pytesseract.image_to_string(pic).split())


def main(pdf_path, out_path):
    pdf = pdfplumber.open(pdf_path)
    items, cur = [], None
    for pno, page in enumerate(pdf.pages, 1):
        words = page.extract_words(keep_blank_chars=False, use_text_flow=False, x_tolerance=1.5)
        start = 0
        if pno == 1:
            start = max(w['bottom'] for w in words if w['text'] in ('NO.', 'QUESTION/INQUIRY'))
        footer = min([w['top'] for w in words if w['text'] == 'Offerors'] + [page.height])
        lines = {}
        for w in words:
            if w['top'] <= start: continue
            if w['text'].startswith('Docusign') or w['top'] < 40: continue
            lines.setdefault(round(w['top'] / 3), []).append(w)
        events = [('line', key * 3, sorted(lines[key], key=lambda w: w['x0'])) for key in lines]
        # a picture sits at the top of its table cell, a few points above the item number's text line
        events += [('pic', im['top'] + 8, im) for im in page.images
                   if im['top'] > max(start, 40) and im['bottom'] < footer and im['x0'] > 100]
        for kind, _, obj in sorted(events, key=lambda e: e[1]):
            if kind == 'pic':
                if cur is not None:
                    side = 'response_picture_text' if obj['x0'] >= COL_RESPONSE else 'question_picture_text'
                    cur[side].append(ocr(page, obj))
                continue
            ws = obj
            text = ' '.join(w['text'] for w in ws)
            if re.match(r'^(Page \d+ of \d+|Offerors are also notified|Christopher M\. Budasi)', text) or text.startswith('Envelope ID'):
                if text.startswith('Offerors'): cur = None
                continue
            starts_item = ws[0]['x0'] < 60 and re.match(r'^\d+\.$', ws[0]['text'])
            if cur is None and not starts_item: continue
            if starts_item:
                cur = {'no': int(ws[0]['text'][:-1]), 'date': '', 'question': [], 'response': [], 'page': pno,
                       'question_picture_text': [], 'response_picture_text': []}
                items.append(cur); ws = ws[1:]
            for w in ws:
                if COL_DATE[0] <= w['x0'] < COL_DATE[1] and re.match(r'^\d{1,2}/\d{1,2}/\d{2}$', w['text']):
                    cur['date'] = w['text']
                elif w['x0'] < COL_RESPONSE:
                    cur['question'].append(w['text'])
                else:
                    cur['response'].append(w['text'])
    for it in items:
        it['question'] = ' '.join(it['question']); it['response'] = ' '.join(it['response'])
        it['question_picture_text'] = ' | '.join(t for t in it['question_picture_text'] if t)
        it['response_picture_text'] = ' | '.join(t for t in it['response_picture_text'] if t)
    json.dump(items, open(out_path, 'w'), indent=1, ensure_ascii=False)
    print(len(items), 'items; numbered 1..44 in order:', [i['no'] for i in items] == list(range(1, 45)))
    print('with a picture in the question:', [i['no'] for i in items if i['question_picture_text']])
    print('with a picture in the answer:', [i['no'] for i in items if i['response_picture_text']])


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
