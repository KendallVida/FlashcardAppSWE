import json
import math
import os
import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, ttk

class Flashcard:
    """
    Base class for all types of flashcard
    Uses SM-2 scheduling algorithm
    """

    def __init__(self, question, answer, tags=""):
        #Card content
        self.question = question
        self.answer = answer
        self.tags = tags

        #SM-2 spaced-repetition fields
        self.interval = 1       # Days until next review
        self.repetitions = 0    # Consecutive correct answers
        self.easiness = 2.5     # Difficulty multiplier (min 1.3)
        self.next_review = date.today().isoformat()

    #  Scheduling

    def is_due(self):
        return date.today() >= date.fromisoformat(self.next_review) # Return true if card is due for review today

    def update_schedule(self, quality):
        if quality >= 3:
            # Correct, advance interval
            if self.repetitions == 0:
                self.interval = 1
            elif self.repetitions == 1:
                self.interval = 6
            else:
                self.interval = round(self.interval * self.easiness)
            self.repetitions += 1
        else:
            # Incorrect, start over
            self.repetitions = 0
            self.interval = 1

        # Adjust how easy card is based on recall quality
        self.easiness = max(1.3, self.easiness + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        self.next_review = (date.today() + timedelta(days=self.interval)).isoformat()

    # Answer Checking

    def check_answer(self, user_input):
        # Return True if input is correct
        return user_input.strip().lower() == self.answer.strip().lower()

    # Convert to/from plain dict to JSON

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "question": self.question,
            "answer": self.answer,
            "tags": self.tags,
            "interval": self.interval,
            "repetitions": self.repetitions,
            "easiness": self.easiness,
            "next_review": self.next_review,
        }

    @classmethod
    def from_dict(cls, data):
        card = cls(data["question"], data["answer"], data.get("tags", ""))
        card.interval = data["interval"]
        card.repetitions = data["repetitions"]
        card.easiness = data["easiness"]
        card.next_review = data["next_review"]
        return card

class BasicCard(Flashcard):
    CARD_TYPE = "Basic"

    def hint(self):
        return f"Starts with: '{self.answer[0]}'" if self.answer else ""

class MultipleChoiceCard(Flashcard):
    CARD_TYPE = "Multiple Choice"

    def __init__(self, question, answer, choices, tags=""):
        super().__init__(question, answer, tags)
        self.choices = choices  # List of options

    def check_answer(self, user_input):
        return user_input.strip().lower() == self.answer.strip().lower()

    def to_dict(self):
        data = super().to_dict()
        data["choices"] = self.choices
        return data

    @classmethod
    def from_dict(cls, data):
        card = cls(
            data["question"],
            data["answer"],
            data.get("choices", []),
            data.get("tags", "")
        )
        card.interval = data["interval"]
        card.repetitions = data["repetitions"]
        card.easiness = data["easiness"]
        card.next_review = data["next_review"]
        return card