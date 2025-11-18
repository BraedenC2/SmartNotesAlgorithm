"""
Braeden Connors
Project Started on 11/17/2025

Final Project; Smart Card
(A smart flashcard application)
"""
import datetime
import json
import os
import random
# Card Model and BKT Algorithm

from dataclasses import dataclass, field
from typing import Optional, List


# data models:

@dataclass
class Skill:
    skill_id: int
    name: str

    #BKT parameters (adjustable by the user in the future)
    p_init: float = 0.2
    p_learn: float = 0.15
    p_slip: float = 0.1
    p_guess: float = 0.2

    # Shouldnt be adjusted by user.
    p_known: float = 0.2

    #Reporting states:
    attempts: int = 0
    correct: int = 0


    def update_bkt(self) -> None:
        """
        :return:
        """

    @property
    def accuracy(self) -> float:
        if self.attempts == 0:
            return 0.0
        return self.correct / self.attempts

    def to_dict(self) -> dict:
        return {
            'skill_id': self.skill_id,
            'name': self.name,
            'p_init': self.p_init,
            'p_learn': self.p_learn,
            'p_slip': self.p_slip,
            'p_guess': self.p_guess,
            'p_known': self.p_known,
            'attempts': self.attempts,
            'correct': self.correct,
        }

    @staticmethod
    def from_dict(d: dict) -> 'Skill':
        return Skill(
            skill_id=d['skill_id'],
            name=d['name'],
            p_init=d.get('p_init', 0.2),
            p_learn=d.get('p_learn', 0.15),
            p_slip=d.get('p_slip', 0.1),
            p_guess=d.get('p_guess', 0.2),
            p_known=d.get('p_known', d.get('p_init', 0.2)),
            attempts=d.get('attempts', 0),
            correct=d.get('correct', 0),
        )

@dataclass
class Card:
    card_id: int
    front: str
    back: str
    skill_ids: List[int] = field(default_factory=list)

    #stats
    attempts: int = 0
    correct: int = 0
    last_outcome_correct: Optional[bool] = None

    #scheduling
    last_review: Optional[datetime] = None
    next_due: Optional[datetime] = None
    interval_days: float = 0.0

    #last_outcome_correct: Optional[bool] = None

    def to_dict(self) -> dict:
        return {
            'card_id': self.card_id,
            'front': self.front,
            'back': self.back,
            'skill_ids': self.skill_ids,
            'attempts': self.attempts,
            'correct': self.correct,
            'last_outcome_correct': self.last_outcome_correct,
            'last_review': self.last_review,
            'next_due': self.next_due,
            'interval_days': self.interval_days,
        }
    @staticmethod
    def from_dict(d: dict) -> 'Card':
        def parse_dt(s: Optional[str]) -> Optional[datetime]:
            if s is None:
                return None
            try:
                return datetime
            except Exception:
                return None

        return Card(
            card_id=d['card_id'],
            front=d['front'],
            back=d['back'],
            skill_ids=d.get('skill_ids', []),
            attempts=d.get('attempts',0),
            correct=d.get('correct',0),
            last_outcome_correct=d.get('last_outcome_correct',None),
            last_review=parse_dt(d.get('last_review')),
            next_due=parse_dt(d.get('next_due')),
            interval_days=d.get('interval_days', 0.0),

        )
    @property
    def accuracy(self) -> float:
        if self.attempts == 0:
            return 0.0
        return self.correct / self.attempts



@dataclass
class Deck:
    cards: List[Card] = field(default_factory=list)
    next_id: int = 1
    def add_card(self, card: Card) -> None:
        """

        :param card:
        :return:
        """
    def get_card_by_id(self, card_id: int) -> Card:
        """

        :param card_id:
        :return:
        """

    def is_empty(self) -> bool:
        return len(self.cards) == 0

    def to_dict(self) -> dict:
        return {
            "next_id": self.next_id,
            "cards": self.cards,
        }

    @staticmethod
    def from_dict(d: dict) -> "Deck":
        deck = Deck()
        deck.next_id = d.get('next_id', 1)
        deck.cards = [Card.from_dict(cd) for cd in d.get('cards', [])]
        return deck

#SAVING PROGRESS
# this is where the states will save to
SAVE_FILE = "smart_cards_state.json"
LOG_FILE = "smart_cards_log.json"

def save_deck(deck: Deck, path: str = SAVE_FILE) -> None:
    with open(path, "w", enchoding="utf-8") as f:
        json.dump(deck.to_dict(), f, indent=2)



def load_deck(path: str = SAVE_FILE) -> Deck:
    if not os.path.exists(path):
        return Deck()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data= json.load(f)
        return Deck.from_dict(data)
    except Exception:
        return Deck()

# ----- Mastery Logics -----

def compute_card_mastery(deck: Deck, card: Card) -> float:
    vals = []
    for sid in card.skill_ids:
        skill = deck.get_skill_by_id(sid)
        if skill is not None:
            vals.append(skill.p_known)
    if not vals:
        return 0.2
    return sum(vals) / len(vals)

def compute_card_priority(card: Card) -> float:
    now = datetime.datetime.now()

    if card.next_due is None:
        due_score = 1.0


def select_next_card(deck: Deck, epsilon: float= 0.2) -> Optional[Card]:
    if deck.is_empty():
        return None

    if random.random() < epsilon:
        return random.choice(deck.cards)

    best_card = None
    best_score = -1.0
    for card in deck.cards:
        score = compute_card_priority(card)
        if score > best_score:
            best_score = score
            best_card = card

    return best_card


# ----- UI ------

def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60 + "\n")

def prinpt_int(print: str) -> None:
    """"""

def wait_for_enter(msg: str = "Press enter to continue...") -> None:
    input(msg)



# -----MENU-----

def action_add_card(deck: Deck) -> None:
    print("Add new card: ")
    front = input("Front: (term/question)")
    back = input("Back: (Definition/Answer)")
    card = deck.add_card(front, back)
    print(f"\nCard #{card.card_id} created")

def action_study(deck: Deck) -> None:
    print("Study Mode")
    print("Instructions: ")
    print("1. You will be prompted for a card (the front)")
    print("2. Try to recall the answer yourself")
    print("3. See the answer, judge yourself")
    print("'y' - you got it right, 'n' - you got it wrong, 'q' = quit\n")

def action_mastery_report_cards(deck: Deck) -> None:
    print_header("Master Report Cards")
    if deck.is_empty():
        print_header("No cards")
        wait_for_enter()
        return

    sorted_cards = sorted(deck.cards, key=lambda c: compute_card_mastery(deck, c))

    print(f"{'ID':<4} {'Mastery':<10} {'Attempts':<9} {'Accuracy':<10} Front")
    print("-" * 80)
    for c in sorted_cards:
        mastery = f"{compute_card_mastery(deck, c):.3f}"
        acc = f"{c.accuracy:.2f}"
        print(f"{c.card_id:<4} {mastery:<10} {c.attempts:<9} {acc:<10} {c.front}")
    print()
    wait_for_enter()


def action_mastery_report_skills(deck: Deck) -> None:
    print_header("Master Report Skills")
    if not deck.skills:
        print("No skills available")
        wait_for_enter()
        return

    sorted_skills = sorted(deck.skills, key=lambda s: s.p_known)

    print(f"{'ID':<4} {'Skill':<20} {'Mastery':<10} {'Attempts':<9} {'Accuracy':<10}")
    print("-" * 70)
    for s in sorted_skills:
        mastery = f"{s.p_known:.3f}"
        acc = f"{s.accuracy:.2f}"
        print(f"{s.skill_id:<4} {s.name:<20} {mastery:<10} {s.attempts:<9} {acc:<10}")
    print()
    wait_for_enter()





def main() -> None:
    deck = load_deck()
    while True:
        print("Welcome to SmartCards!")
        print("MENU:")
        print("1. Add new card")
        print("2. Study Mode")
        print("3. View all cards")
        print("4. Mastery Report (Cards)")
        print("5. Mastery Report (Skills)")
        print("6. Save and Quit")
        print("0. Exit without saving")

        user_input = input("Enter your choice: ")
        if user_input == "1":
            action_add_card(deck)
        elif user_input == "2":
            action_study(deck)
        elif user_input == "3":
            """view all cards"""
        elif user_input == "4":
            action_mastery_report_cards(deck)
        elif user_input == "5":
            """"""
        elif user_input == "6":
            save_deck(deck)
            print_header(f"Smart Cards Saved")
            break
        elif user_input == "0":
            print("Exiting...")
            break
        else:
            print("Invalid input")


if __name__ == "__main__":
    main()