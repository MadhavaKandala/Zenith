#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
OCR Skill — Read text from images and screenshots using Tesseract.

Actions:
  - read_text: Extract text from a specified image file
  - screenshot_text: Capture the screen and extract all visible text
"""

import sys
import os

# Add project root to path for core module imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from core.vision.ocr import OCREngine

_ocr = None


def _get_ocr():
    """Lazy-initialize the OCR engine singleton."""
    global _ocr
    if _ocr is None:
        _ocr = OCREngine()
    return _ocr


def read_text(params):
    """Extract text from an image file specified in the utterance or entities."""
    ocr = _get_ocr()

    # Try to get the image path from entities
    entities = params.get('entities', [])
    image_path = None

    for entity in entities:
        if entity.get('entity') == 'file_path' or entity.get('entity') == 'path':
            image_path = entity.get('sourceText', entity.get('resolution', {}).get('value'))
            break

    if not image_path:
        # Try utterance for a file path pattern
        utterance = params.get('utterance', '')
        import re
        path_match = re.search(r'[A-Za-z]:\\[^\s]+|/[^\s]+\.\w+', utterance)
        if path_match:
            image_path = path_match.group()

    if not image_path:
        return print('{"key": "no_path", "data": {"speech": "I need an image path to read text from, sir. Please specify the file location."}}')

    if not os.path.isfile(image_path):
        return print(f'{{"key": "file_not_found", "data": {{"speech": "I cannot find that file, sir. Please check the path: {image_path}"}}}}')

    try:
        text = ocr.extract_text(image_path)
        if text:
            # Truncate for speech output
            speech_text = text[:500] + ('...' if len(text) > 500 else '')
            return print(f'{{"key": "text_found", "data": {{"speech": "Here is what I found in the image, sir: {speech_text}"}}}}')
        else:
            return print('{"key": "no_text", "data": {"speech": "I could not detect any text in that image, sir."}}')
    except RuntimeError as e:
        return print(f'{{"key": "ocr_unavailable", "data": {{"speech": "OCR is not available on this system, sir. {str(e)}"}}}}')
    except Exception as e:
        return print(f'{{"key": "error", "data": {{"speech": "An error occurred while reading the image, sir: {str(e)}"}}}}')


def screenshot_text(params):
    """Capture the current screen and extract text via OCR."""
    ocr = _get_ocr()

    try:
        text = ocr.screenshot_to_text()
        if text:
            speech_text = text[:500] + ('...' if len(text) > 500 else '')
            return print(f'{{"key": "screen_text", "data": {{"speech": "Here is what I can read on your screen, sir: {speech_text}"}}}}')
        else:
            return print('{"key": "no_screen_text", "data": {"speech": "I could not detect any text on your screen, sir."}}')
    except RuntimeError as e:
        return print(f'{{"key": "ocr_unavailable", "data": {{"speech": "OCR is not available: {str(e)}"}}}}')
    except Exception as e:
        return print(f'{{"key": "error", "data": {{"speech": "Screen reading failed, sir: {str(e)}"}}}}')
