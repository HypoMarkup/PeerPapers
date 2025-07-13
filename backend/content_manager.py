from typing import Optional


class ContentManager:
    base64PDF: Optional[str]

    def __init__(self):
        self.base64PDF = None

    def set_pdf(self, base64PDF: str):
        self.base64PDF = base64PDF

    def get_pdf(self):
        return self.base64PDF
