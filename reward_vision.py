"""Read yellow challenge amounts without including the wallet coin below."""
import cv2
import numpy as np


def result_number_image(img, zone):
    """Isolate cyan result digits, excluding the grey unit and caption."""
    x, y, w, h = zone
    roi = img[y:y+h, x:x+w]
    if roi.size == 0:
        return None
    mask = cv2.inRange(cv2.cvtColor(roi, cv2.COLOR_BGR2HSV),
                       np.array([80, 90, 80]), np.array([115, 255, 255]))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    ids = [i for i in range(1, count)
           if stats[i, cv2.CC_STAT_HEIGHT] >= 20
           and stats[i, cv2.CC_STAT_AREA] >= 80]
    if not ids:
        return None
    boxes = stats[ids]
    x1, y1 = boxes[:,0].min(), boxes[:,1].min()
    x2 = (boxes[:,0]+boxes[:,2]).max()
    y2 = (boxes[:,1]+boxes[:,3]).max()
    clean = np.isin(labels[y1:y2,x1:x2], ids).astype('uint8')*255
    clean = cv2.copyMakeBorder(255-clean, 12,12,12,12,cv2.BORDER_CONSTANT,value=255)
    return cv2.resize(clean,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)


def read_result_number(img, zone, ocr):
    prepared = result_number_image(img, zone)
    if prepared is None:
        return 0
    _, encoded = cv2.imencode('.png', prepared)
    text = ocr.classification(encoded.tobytes()).strip()
    # Reject mixed text rather than silently dropping a missing zero (40o -> 40).
    return int(text) if text.isascii() and text.isdigit() else 0


def challenge_number_image(img, zone):
    x, y, w, h = zone
    roi = img[y:y+h, x:x+w]
    if roi.size == 0:
        return None
    mask = cv2.inRange(cv2.cvtColor(roi, cv2.COLOR_BGR2HSV),
                       np.array([15, 50, 50]), np.array([45, 255, 255]))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    components = [(i, tuple(map(int, stats[i]))) for i in range(1, count)
                  if stats[i, cv2.CC_STAT_HEIGHT] >= 12
                  and stats[i, cv2.CC_STAT_AREA] >= 30]
    if not components:
        return None
    # Digits share a baseline. Do not let an unrelated yellow coin expand
    # the crop to several lines, which made the old OCR read 800 as 0/8/9.
    groups = []
    for _, (_, yy, _, hh, _) in components:
        group = [(i, s) for i, s in components
                 if abs(s[1] + s[3]/2 - yy - hh/2) < max(hh, s[3])*.4]
        groups.append(group)
    group = max(groups, key=lambda g: sum(s[4] for _, s in g))
    x1 = min(s[0] for _, s in group)
    y1 = min(s[1] for _, s in group)
    x2 = max(s[0]+s[2] for _, s in group)
    y2 = max(s[1]+s[3] for _, s in group)
    clean = np.isin(labels[y1:y2, x1:x2], [i for i, _ in group]).astype('uint8')*255
    clean = cv2.copyMakeBorder(255-clean, 8, 8, 8, 8, cv2.BORDER_CONSTANT, value=255)
    return cv2.resize(clean, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)


def read_challenge_number(img, zone, ocr):
    prepared = challenge_number_image(img, zone)
    if prepared is None:
        return 0
    _, encoded = cv2.imencode('.png', prepared)
    text = ocr.classification(encoded.tobytes()).strip().upper()
    text = text.translate(str.maketrans({'O':'0', 'Q':'0', 'I':'1', 'L':'1', 'S':'5', 'B':'8'}))
    return int(text) if text.isdigit() else 0
