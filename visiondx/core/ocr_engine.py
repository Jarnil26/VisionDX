"""
VisionDX — OCR Engine

Handles both digital PDFs (with text layer via pdfplumber) and
scanned PDFs (image-based via pdf2image + Tesseract OCR + OpenCV preprocessing).
"""
from __future__ import annotations

import io
import os
import re
from pathlib import Path
from typing import NamedTuple

import pytesseract
from loguru import logger
from PIL import Image

from visiondx.config import settings
from visiondx.utils.text_cleaner import clean_text

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


class PageText(NamedTuple):
    page_number: int
    text: str
    source: str  # "pdfplumber" | "tesseract"


class PDFExtractor:
    """
    Extract text from PDF files.

    Strategy:
      1. Try pdfplumber (fast, lossless for digital PDFs)
      2. If page text < MIN_CHARS threshold → fall back to Tesseract OCR
      3. Apply OpenCV preprocessing for OCR pages (grayscale, denoise, threshold)
    """

    MIN_CHARS_PER_PAGE = 50  # threshold below which we assume scanned page

    def extract(self, pdf_path: str | Path) -> str:
        """
        Full extraction pipeline. Returns concatenated cleaned text from all pages.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        pages = self._extract_pages(pdf_path)
        full_text = "\n\n".join(p.text for p in pages if p.text.strip())
        return clean_text(full_text)

    def _extract_pages(self, pdf_path: Path) -> list[PageText]:
        results: list[PageText] = []
        try:
            import pdfplumber

            with pdfplumber.open(str(pdf_path)) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    if len(text.strip()) >= self.MIN_CHARS_PER_PAGE:
                        logger.debug(f"Page {i}: pdfplumber extracted {len(text)} chars")
                        results.append(PageText(i, text, "pdfplumber"))
                    else:
                        logger.debug(f"Page {i}: sparse text ({len(text)} chars), falling back to OCR")
                        ocr_text = self._ocr_page_via_image(pdf_path, i - 1)
                        results.append(PageText(i, ocr_text, "tesseract"))
        except Exception as e:
            logger.warning(f"pdfplumber failed ({e}), falling back to full OCR")
            results = self._full_ocr(pdf_path)

        return results

    def _ocr_page_via_image(self, pdf_path: Path, page_index: int) -> str:
        """Convert a single PDF page to image and OCR it."""
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(
                str(pdf_path),
                dpi=300,
                first_page=page_index + 1,
                last_page=page_index + 1,
            )
            if not images:
                return ""
            return self._ocr_image(images[0])
        except Exception as e:
            logger.error(f"OCR page {page_index} failed: {e}")
            return ""

    def _full_ocr(self, pdf_path: Path) -> list[PageText]:
        """Convert entire PDF to images and OCR all pages."""
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(str(pdf_path), dpi=300)
            results = []
            for i, img in enumerate(images, start=1):
                text = self._ocr_image(img)
                results.append(PageText(i, text, "tesseract"))
            return results
        except Exception as e:
            logger.error(f"Full OCR failed: {e}")
            return []

    def _ocr_image(self, pil_image: Image.Image) -> str:
        """
        Apply OpenCV preprocessing and run Tesseract OCR.
        Steps: grayscale → denoise → adaptive threshold → Tesseract
        """
        try:
            import cv2
            import numpy as np

            # Convert PIL to numpy array
            img_array = np.array(pil_image.convert("RGB"))

            # 1. Grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

            # 2. Light denoise
            gray = cv2.fastNlMeansDenoising(gray, h=10)

            # 3. Adaptive threshold (handles uneven lighting in scans)
            thresh = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                blockSize=11,
                C=2,
            )

            # 4. Deskew (rotate to fix tilted scans)
            thresh = self._deskew(thresh)

            # Convert back to PIL for Tesseract
            processed = Image.fromarray(thresh)

            # 5. Tesseract with page segmentation mode 6 (uniform text block)
            config = "--psm 6 -l eng"
            text = pytesseract.image_to_string(processed, config=config)
            return text

        except ImportError:
            logger.warning("OpenCV not available, running raw Tesseract on original image")
            return pytesseract.image_to_string(pil_image, config="--psm 6 -l eng")
        except Exception as e:
            logger.error(f"OCR image processing failed: {e}")
            return ""

    @staticmethod
    def _deskew(image) -> "np.ndarray":
        """Detect and correct skew angle of scanned document."""
        try:
            import cv2
            import numpy as np

            coords = np.column_stack(np.where(image < 128))
            if len(coords) == 0:
                return image
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            # Only deskew if angle is significant
            if abs(angle) < 0.5:
                return image
            h, w = image.shape
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            deskewed = cv2.warpAffine(
                image, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
            return deskewed
        except Exception:
            return image


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Convenience function — extract text from a PDF file."""
    extractor = PDFExtractor()
    return extractor.extract(pdf_path)
