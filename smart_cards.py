"""
Braeden Connors
Project Started on 11/17/2025

Final Project; Smart Card
(A smart flashcard application)
"""
import datetime
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

def save_deck(deck: Deck) -> None:
    """
    Will save the deck into a json file
    :param deck:
    :return:
    """

def load_deck() -> Deck:
    """"""

# ----- Bandit -----

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

def action_mastery_report(deck: Deck) -> None:
    print("Master Report Mode")






def main() -> None:
    while True:
        print("Welcome to SmartCards!")
        print("MENU:")
        print("1. Add new card")
        print("2. Study Mode")
        print("3. View all cards")
        print("4. Mastery Report Mode")
        print("5. Exit the program")

        user_input = input("Enter your choice: ")
        if user_input == "1":
            action_add_card(Deck())
        elif user_input == "2":
            action_study(Deck())
        elif user_input == "3":
            """view all cards"""
        elif user_input == "4":
            action_mastery_report(Deck())
        elif user_input == "5":
            print("Thank you for using SmartCards!")
            break
        else:
            print("Invalid input")


if __name__ == "__main__":
    main()