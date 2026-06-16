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

class ClozeCard(Flashcard):
    CARD_TYPE = "Cloze"

CARD_CLASSES = {"BasicCard": BasicCard,
                "MultipleChoiceCard": MultipleChoiceCard,
                "ClozeCard": ClozeCard
                }

def card_from_dict(data):
    #Reconstructs correct flashcard subclass from a saved dictionary
    cls = CARD_CLASSES.get(data.get("type"), BasicCard)
    return cls.from_dict(data)

class Deck:
    #Collection of Flashcards object with file persistence

    SAVE_FILE = "flashcard_data.json"

    def __init__(self):
        self.cards = []

    def add_card(self, card):
        #Add flashcard to the deck
        self.cards.append(card)

    def remove_card(self, index):
        #Remove card at a given list index
        if 0 <= index < len(self.cards):
            self.cards.pop(index)

    def due_cards(self):
        #Return a list of cards that are due for review today
        return [card for card in self.cards if card.is_due()]

    def save(self):
        #Serialise cards to JSON file
        data = [card.to_dict() for card in self.cards]
        with open(self.SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        #Load cards from JSON file
        if not os.path.exists(self.SAVE_FILE):
            return
        with open(self.SAVE_FILE, "r") as f:
            data=json.load(f)
            self.cards = [card_from_dict(d) for d in data]