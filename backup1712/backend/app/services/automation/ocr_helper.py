import asyncio
import io
import base64
from PIL import Image
from typing import Optional, Tuple, List
import pyautogui
import numpy as np
import cv2

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

class OCRHelper:
    """
    OCR helper using EasyOCR for text recognition.
    Includes optimized image preprocessing for better accuracy.
    """
    
    def __init__(self):
        if not EASYOCR_AVAILABLE:
            raise ImportError("EasyOCR is not installed. Run: pip install easyocr")
        
        print("Initializing EasyOCR (this may take a moment)...")
        # Initialize EasyOCR with English only for speed
        # gpu=False for CPU mode
        self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        print("✓ EasyOCR initialized (English)")
    
    def _preprocess_image(self, img: Image.Image) -> np.ndarray:
        """
        Максимальная четкость для OCR.
        Optimized preprocessing pipeline.
        """
        # Convert PIL to OpenCV format
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # Увеличение контраста
        img_cv = cv2.convertScaleAbs(img_cv, alpha=1.3, beta=15)
        
        # Размытие для сглаживания
        img_cv = cv2.GaussianBlur(img_cv, (1, 1), 0)
        
        # Бинаризация (если фон светлый)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return processed

    async def find_text_on_screen(self, search_text: str, screenshot_b64: str = None) -> Optional[Tuple[int, int]]:
        """
        Find specific text on screen and return its center coordinates.
        Returns (x, y) tuple or None if not found.
        """
        if screenshot_b64:
            img_data = base64.b64decode(screenshot_b64)
            img = Image.open(io.BytesIO(img_data))
        else:
            img = pyautogui.screenshot()
        
        # Preprocess image
        img_processed = self._preprocess_image(img)
        
        # Run OCR
        # readtext returns: [([[x1,y1], [x2,y2], [x3,y3], [x4,y4]], text, confidence), ...]
        result = self.reader.readtext(img_processed)
        
        if not result:
            return None
        
        # Normalize search text
        search_normalized = search_text.lower().replace(' ', '')
        
        # Parse results
        for detection in result:
            bbox, text, confidence = detection
            text_normalized = text.lower().replace(' ', '')
            
            # Check for match
            if search_normalized in text_normalized:
                # Calculate center of bounding box
                x = int((bbox[0][0] + bbox[2][0]) / 2)
                y = int((bbox[0][1] + bbox[2][1]) / 2)
                print(f"✓ Found '{search_text}' at ({x}, {y}) [confidence: {confidence:.2f}]")
                return (x, y)
        
        # Fuzzy fallback
        import difflib
        texts = [detection[1] for detection in result]
        matches = difflib.get_close_matches(search_text, texts, n=1, cutoff=0.85)  # Stricter matching
        
        if matches:
            best_match = matches[0]
            for detection in result:
                if detection[1] == best_match:
                    bbox = detection[0]
                    x = int((bbox[0][0] + bbox[2][0]) / 2)
                    y = int((bbox[0][1] + bbox[2][1]) / 2)
                    print(f"✓ Found fuzzy match '{best_match}' for '{search_text}' at ({x}, {y})")
                    return (x, y)
        
        return None

    async def find_all_text_on_screen(self, screenshot_b64: str = None) -> List[dict]:
        """
        Find all text on screen with coordinates.
        Returns list of dicts: [{'text': str, 'x': int, 'y': int, 'confidence': float}, ...]
        """
        if screenshot_b64:
            img_data = base64.b64decode(screenshot_b64)
            img = Image.open(io.BytesIO(img_data))
        else:
            img = pyautogui.screenshot()
        
        # Preprocess image
        img_processed = self._preprocess_image(img)
        
        # Run OCR
        result = self.reader.readtext(img_processed)
        
        if not result:
            return []
        
        results = []
        for detection in result:
            bbox, text, confidence = detection
            
            if text and confidence > 0.3:  # Filter low confidence
                x = int((bbox[0][0] + bbox[2][0]) / 2)
                y = int((bbox[0][1] + bbox[2][1]) / 2)
                results.append({
                    'text': text,
                    'x': x,
                    'y': y,
                    'confidence': confidence
                })
        
        return results
