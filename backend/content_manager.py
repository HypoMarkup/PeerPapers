from typing import Optional


class ContentManager:
    base64PDF: Optional[str]
    numberOfQuestions: int

    def __init__(self):
        self.base64PDF = None

    def set_pdf(self, base64PDF: str):
        self.base64PDF = base64PDF

    def get_pdf(self):
        return self.base64PDF

    def set_number_of_questions(self, num):
        self.numberOfQuestions = num

    def get_number_of_questions(self):
        return self.numberOfQuestions
