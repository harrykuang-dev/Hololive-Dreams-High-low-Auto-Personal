from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from poker_core import JOKER_ID, card_id


def read_template_image(path: str | Path, flags: int) -> np.ndarray:
    """Read a template from a Windows path that may contain Chinese characters."""
    try:
        encoded = np.fromfile(str(path), dtype=np.uint8)
    except OSError as exc:
        raise RuntimeError(f"无法读取模板文件：{path}（{exc}）") from exc
    if encoded.size == 0:
        raise RuntimeError(f"模板文件为空或不存在：{path}")
    image = cv2.imdecode(encoded, flags)
    if image is None:
        raise RuntimeError(f"无法解码模板：{path}")
    return image


@dataclass(frozen=True)
class RecognizedCard:
    card_id: int
    rank: str
    suit: str
    rank_score: float
    suit_score: float
    rank_margin: float


class CardRecognizer:
    """Hololive Dreams 2560x1440 card recognizer.

    The recognizer first verifies that five *face-up white cards* are visible.
    This prevents the betting screen, card backs, menus, and animations from
    being interpreted as playable cards.
    """

    def __init__(self, template_dir: str | Path):
        template_dir = Path(template_dir)
        self.rank_templates: dict[str, list[np.ndarray]] = {}
        for path in sorted((template_dir / "ranks").glob("*.png")):
            label = path.stem.split("_")[0]
            self.rank_templates.setdefault(label, []).append(self._load_mask(path))
        self.suit_templates: dict[str, list[np.ndarray]] = {}
        for path in sorted((template_dir / "suits").glob("*.png")):
            label = path.stem[0]
            self.suit_templates.setdefault(label, []).append(self._load_mask(path))
        self.joker_corner = self._load_mask(template_dir / "joker_corner.png")
        self.joker_card = read_template_image(template_dir / "joker_card.png", cv2.IMREAD_GRAYSCALE)
        if not self.rank_templates or len(self.suit_templates) != 4 or self.joker_card is None:
            raise RuntimeError("模板文件不完整。")

    @staticmethod
    def _load_mask(path: Path) -> np.ndarray:
        image = read_template_image(path, cv2.IMREAD_GRAYSCALE)
        return (image > 127).astype(np.uint8) * 255

    @staticmethod
    def _foreground_mask(crop: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        _, s, v = cv2.split(hsv)
        # Black glyphs, or saturated red glyphs.
        mask = ((v < 155) | ((s > 85) & (v < 250))).astype(np.uint8) * 255
        return cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))

    @staticmethod
    def _remove_top_left_border_noise(mask: np.ndarray) -> np.ndarray:
        """Remove a small rounded-card-border fragment from the rank crop.

        At 1080p the antialiased top-left card border can enter the rank crop as
        a separate component touching both the top and left edges.  Including
        that fragment expands the normalization box and can make digits such as
        9 resemble another rank.  Real rank glyphs are inset from both edges, so
        only small components touching both edges are discarded.
        """
        binary = (mask > 0).astype(np.uint8)
        count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
        if count <= 1:
            return mask

        largest_area = int(stats[1:, cv2.CC_STAT_AREA].max())
        cleaned = mask.copy()
        for component in range(1, count):
            x, y, _w, _h, area = (int(v) for v in stats[component])
            if x == 0 and y == 0 and area < max(24, int(largest_area * 0.25)):
                cleaned[labels == component] = 0
        return cleaned

    @staticmethod
    def _normalize(mask: np.ndarray, size: int = 64, largest_only: bool = False) -> np.ndarray:
        if largest_only:
            count, labels, stats, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
            if count > 1:
                component = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
                mask = (labels == component).astype(np.uint8) * 255

        ys, xs = np.where(mask > 0)
        if len(xs) == 0:
            return np.zeros((size, size), dtype=np.uint8)
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        glyph = mask[y0:y1, x0:x1]
        padding = 5
        max_dim = size - 2 * padding
        scale = min(max_dim / glyph.shape[1], max_dim / glyph.shape[0])
        width = max(1, round(glyph.shape[1] * scale))
        height = max(1, round(glyph.shape[0] * scale))
        resized = cv2.resize(glyph, (width, height), interpolation=cv2.INTER_NEAREST)
        out = np.zeros((size, size), dtype=np.uint8)
        px = (size - width) // 2
        py = (size - height) // 2
        out[py : py + height, px : px + width] = resized
        return out

    @staticmethod
    def _shape_score(a: np.ndarray, b: np.ndarray) -> float:
        best = 0.0
        aa = a > 0
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                transform = np.float32([[1, 0, dx], [0, 1, dy]])
                shifted = cv2.warpAffine(b, transform, (b.shape[1], b.shape[0]), borderValue=0) > 0
                union = np.logical_or(aa, shifted).sum()
                if union:
                    score = float(np.logical_and(aa, shifted).sum()) / float(union)
                    best = max(best, score)
        return best

    @staticmethod
    def _is_red(crop: np.ndarray) -> bool:
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        red = (((h < 14) | (h >= 165)) & (s > 90) & (v > 80)).sum()
        black = ((v < 120) & (s < 120)).sum()
        return int(red) > max(12, int(black * 0.30))

    @staticmethod
    def _width_at(mask: np.ndarray, fraction: float) -> float:
        ys, xs = np.where(mask > 0)
        if len(xs) == 0:
            return 0.0
        y0, y1 = int(ys.min()), int(ys.max())
        x0, x1 = int(xs.min()), int(xs.max())
        row = min(mask.shape[0] - 1, max(0, round(y0 + fraction * max(1, y1 - y0))))
        row_x = np.where(mask[row] > 0)[0]
        return 0.0 if len(row_x) == 0 else float(row_x.max() - row_x.min() + 1) / max(1, x1 - x0 + 1)

    @staticmethod
    def _fallback_rects(width: int, height: int) -> list[tuple[int, int, int, int]]:
        # Normalized coordinates measured from the 2560x1440 gameplay screen.
        starts = (0.0752, 0.2524, 0.4297, 0.6069, 0.7837)
        return [
            (round(xn * width), round(0.3162 * height), round(0.1426 * width), round(0.3606 * height))
            for xn in starts
        ]

    @staticmethod
    def _card_face_score(screen: np.ndarray, rect: tuple[int, int, int, int]) -> float:
        """Score whether a fixed card slot contains a face-up card.

        The old detector averaged most of the card interior. Character cards can
        contain large dark illustrations, and HDR/screen-capture colour changes
        can lower the apparent white level. This version samples the mostly blank
        *edge ring* and bottom strip of the card. Face-up cards are neutral and
        bright there; the purple card backs are saturated in the same regions.
        """
        x, y, w, h = rect
        sh, sw = screen.shape[:2]
        x0 = max(0, x)
        x1 = min(sw, x + w)
        y0 = max(0, y)
        y1 = min(sh, y + h)
        if x1 - x0 < 20 or y1 - y0 < 20:
            return 0.0

        crop = screen[y0:y1, x0:x1]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        _, sat, val = cv2.split(hsv)
        ch, cw = val.shape
        yy, xx = np.mgrid[0:ch, 0:cw]
        xn = xx / max(1, cw)
        yn = yy / max(1, ch)

        inside = (xn > 0.04) & (xn < 0.96) & (yn > 0.04) & (yn < 0.96)
        artwork = (xn > 0.18) & (xn < 0.82) & (yn > 0.15) & (yn < 0.88)
        edge_ring = inside & ~artwork
        bottom_strip = (xn > 0.08) & (xn < 0.80) & (yn > 0.84) & (yn < 0.95)

        # Saturation is the strongest separator. The lower value threshold also
        # tolerates HDR/ICC capture differences where white may appear grey.
        neutral_bright = (sat < 90) & (val > 155)
        ring_ratio = float(neutral_bright[edge_ring].mean()) if edge_ring.any() else 0.0
        bottom_ratio = float(neutral_bright[bottom_strip].mean()) if bottom_strip.any() else 0.0

        # Retain a small contribution from the whole inner area. This helps when
        # the capture is slightly shifted while keeping card backs near zero.
        inner = (xn > 0.06) & (xn < 0.94) & (yn > 0.06) & (yn < 0.94)
        inner_ratio = float(neutral_bright[inner].mean()) if inner.any() else 0.0
        return 0.62 * ring_ratio + 0.28 * bottom_ratio + 0.10 * inner_ratio

    def hold_screen_score(
        self,
        screen: np.ndarray,
        rects: list[tuple[int, int, int, int]] | None = None,
    ) -> tuple[bool, float, tuple[float, ...]]:
        height, width = screen.shape[:2]
        if rects is None:
            rects = self._fallback_rects(width, height)
        scores = tuple(self._card_face_score(screen, rect) for rect in rects)
        if len(scores) != 5:
            return False, 0.0, scores
        average = float(sum(scores) / len(scores))
        # The edge-ring score has a very large gap between face-up cards and the
        # purple betting-screen backs. Keep the threshold permissive enough for
        # HDR capture and character artwork, while still rejecting card backs.
        valid = min(scores) >= 0.46 and average >= 0.64
        return valid, average, scores

    @staticmethod
    def selection_phase_score(screen: np.ndarray) -> tuple[bool, float, tuple[float, float, float, float]]:
        """Detect the purple outlined action button used on the hold-selection screen.

        This is intentionally visual and language-independent. The result / payout
        screen still shows five face-up cards, but it does not show this large
        rounded purple button. Requiring the button prevents the final revealed
        hand from being treated as a new decision hand.
        """
        height, width = screen.shape[:2]
        x0, x1 = int(0.39 * width), int(0.61 * width)
        y0, y1 = int(0.755 * height), int(0.855 * height)
        roi = screen[y0:y1, x0:x1]
        if roi.size == 0:
            return False, 0.0, (0.0, 0.0, 0.0, 0.0)

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        hue, sat, val = cv2.split(hsv)
        purple = (((hue >= 125) & (hue <= 170) & (sat > 80) & (val > 120))).astype(np.uint8) * 255
        white = (((sat < 75) & (val > 215))).astype(np.uint8) * 255
        kernel = np.ones((5, 5), np.uint8)
        purple = cv2.morphologyEx(purple, cv2.MORPH_CLOSE, kernel)
        white = cv2.morphologyEx(white, cv2.MORPH_CLOSE, kernel)

        def best_component(mask: np.ndarray) -> tuple[float, float, float]:
            count, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
            best = (0.0, 0.0, 0.0)
            rh, rw = mask.shape
            for i in range(1, count):
                _x, _y, w, h, area = (int(v) for v in stats[i])
                wr = w / max(1, rw)
                hr = h / max(1, rh)
                ar = area / max(1, rw * rh)
                if (wr, hr, ar) > best:
                    best = (wr, hr, ar)
            return best

        p_w, p_h, p_a = best_component(purple)
        w_w, w_h, w_a = best_component(white)
        # The actual button forms one wide purple component and one wide white
        # border component. Result screens contain only small text/coin shapes.
        valid = p_w >= 0.66 and p_h >= 0.48 and p_a >= 0.22 and w_w >= 0.66 and w_h >= 0.45
        score = min(1.0, 0.30 * p_w + 0.20 * p_h + 0.25 * min(1.0, p_a / 0.45) + 0.15 * w_w + 0.10 * w_h)
        return valid, float(score), (float(p_w), float(p_h), float(w_w), float(w_h))

    def find_card_rects(self, screen: np.ndarray) -> list[tuple[int, int, int, int]]:
        height, width = screen.shape[:2]
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
        white = cv2.inRange(hsv, (0, 0, 220), (180, 60, 255))
        white = cv2.morphologyEx(white, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        count, _, stats, _ = cv2.connectedComponentsWithStats(white)
        rects: list[tuple[int, int, int, int]] = []
        for i in range(1, count):
            x, y, w, h, area = (int(v) for v in stats[i])
            if not (0.08 * width < w < 0.20 * width):
                continue
            if not (0.25 * height < h < 0.50 * height):
                continue
            if not (0.20 * height < y < 0.55 * height):
                continue
            if area < 0.025 * width * height:
                continue
            if 0.58 <= w / h <= 0.82:
                rects.append((x, y, w, h))

        rects.sort(key=lambda item: item[0])
        if len(rects) == 5:
            valid, _, _ = self.hold_screen_score(screen, rects)
            if valid:
                return rects

        # Only use fixed coordinates when they also contain five white card faces.
        # The old version returned these coordinates unconditionally, which caused
        # the purple betting screen to be misread as five cards.
        fallback = self._fallback_rects(width, height)
        valid, _, _ = self.hold_screen_score(screen, fallback)
        return fallback if valid else []

    def _joker_similarity(self, card_crop: np.ndarray) -> float:
        gray = cv2.cvtColor(card_crop, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        inner = gray[int(0.02 * h) : int(0.98 * h), int(0.02 * w) : int(0.98 * w)]
        resized = cv2.resize(inner, (self.joker_card.shape[1], self.joker_card.shape[0]))
        a = cv2.equalizeHist(resized)
        b = cv2.equalizeHist(self.joker_card)
        return float(cv2.matchTemplate(a, b, cv2.TM_CCOEFF_NORMED)[0, 0])

    def recognize_card(self, screen: np.ndarray, rect: tuple[int, int, int, int]) -> RecognizedCard:
        x, y, w, h = rect
        card = screen[y : y + h, x : x + w]
        rank_crop = card[int(0.015 * h) : int(0.11 * h), int(0.01 * w) : int(0.22 * w)]
        suit_crop = card[int(0.10 * h) : int(0.23 * h), int(0.01 * w) : int(0.20 * w)]

        rank_foreground = self._foreground_mask(rank_crop)
        rank_foreground = self._remove_top_left_border_noise(rank_foreground)
        rank_mask = self._normalize(rank_foreground)
        rank_scores: list[tuple[float, str]] = []
        for label, templates in self.rank_templates.items():
            rank_scores.append((max(self._shape_score(rank_mask, t) for t in templates), label))
        rank_scores.sort(reverse=True)
        rank_score, rank = rank_scores[0]
        second_rank_score = rank_scores[1][0] if len(rank_scores) > 1 else 0.0
        rank_margin = float(rank_score - second_rank_score)

        # Check joker only when ordinary-rank confidence is weak.
        corner = card[0 : int(0.25 * h), 0 : int(0.25 * w)]
        joker_corner_mask = self._normalize(self._foreground_mask(corner))
        joker_corner_score = self._shape_score(joker_corner_mask, self.joker_corner)
        joker_card_score = self._joker_similarity(card)
        if rank_score < 0.58 and (joker_corner_score > 0.47 or joker_card_score > 0.42):
            return RecognizedCard(
                JOKER_ID,
                "JOKER",
                "",
                max(joker_corner_score, joker_card_score),
                1.0,
                1.0,
            )

        suit_binary = self._normalize(self._foreground_mask(suit_crop), largest_only=True)
        red = self._is_red(suit_crop)
        if red:
            d_score = max(self._shape_score(suit_binary, t) for t in self.suit_templates["D"])
            h_score = max(self._shape_score(suit_binary, t) for t in self.suit_templates["H"])
            # Template similarity is more reliable than a single width sample.
            # Use geometry only as a tiebreaker for nearly equal scores.
            if abs(h_score - d_score) >= 0.025:
                suit = "H" if h_score > d_score else "D"
            else:
                top_width = self._width_at(suit_binary, 0.17)
                suit = "H" if top_width > 0.62 else "D"
            suit_score = h_score if suit == "H" else d_score
        else:
            s_score = max(self._shape_score(suit_binary, t) for t in self.suit_templates["S"])
            c_score = max(self._shape_score(suit_binary, t) for t in self.suit_templates["C"])
            if abs(s_score - c_score) >= 0.025:
                suit = "S" if s_score > c_score else "C"
            else:
                upper_width = self._width_at(suit_binary, 0.35)
                suit = "S" if upper_width > 0.70 else "C"
            suit_score = s_score if suit == "S" else c_score

        return RecognizedCard(
            card_id(rank, suit),
            rank,
            suit,
            float(rank_score),
            float(suit_score),
            rank_margin,
        )

    def recognize(self, screen: np.ndarray) -> tuple[list[RecognizedCard], list[tuple[int, int, int, int]]]:
        rects = self.find_card_rects(screen)
        if not rects:
            return [], []
        cards = [self.recognize_card(screen, rect) for rect in rects]
        return cards, rects
