"""
Braeden Connors
Project Started on 11/17/2025

Final Project; Smart Card
(A smart flashcard application)
"""
import datetime
import json
import math
import os
import random

from dataclasses import dataclass, field
from typing import Optional, List, Dict

# ALGORITHMS

ALGORITHMS: Dict[str, Dict[str, str]] = {
    "hybrid":{
        "name": "Hybrid BKT + SR",
        "description": (
            "Card-level BKT for mastery, plus spaced repetition intervals "
            "that grow based on mastery, with bandit scheduling."
        ),
    },
    "pure_sr": {
        "name": "Pure Spaced Repetition",
        "description": (
            "No BKT. Mastery is estimated from card accuracy only. "
            "Intervals grow/shrink based on correctness; bandit scheduling still used."
        ),
    },
    "fast_bkt": {
        "name": "Fast-Learning BKT + SR",
        "description": (
            "Same as Hybrid BKT + SR, but with more aggressive learning parameters "
            "(higher p_learn, higher p_init)."
        )
    }



}


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


    def update_bkt(self, is_correct: bool) -> None:
        prior = self.p_known

        s = min(max(self.p_slip, 1e-4), 0.99)
        g = min(max(self.p_guess, 1e-4), 0.99)
        t = min(max(self.p_learn, 0.0), 0.5)

        if is_correct:
            numer = prior * (1 - s)
            denom = numer + (1 - prior) * g
        else:
            numer = prior * s
            denom = numer + (1 - prior) * (1 - g)

        if denom <= 0:
            posterior = prior
        else:
            posterior = numer / denom

        posterior = posterior + (1 - posterior) * t
        posterior = max(0.0, min(1.0, posterior))

        if not is_correct and posterior > prior:
            posterior = prior


        self.p_known = posterior
        self.attempts += 1
        if is_correct:
            self.correct += 1

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


    p_init: float = 0.2
    p_learn: float = 0.15
    p_slip: float = 0.1
    p_guess: float = 0.2
    p_known: float = 0.2

    #stats
    attempts: int = 0
    correct: int = 0
    last_outcome_correct: Optional[bool] = None

    #scheduling
    last_review: Optional[datetime] = None
    next_due: Optional[datetime] = None
    interval_days: float = 0.0

    def update_bkt(self, is_correct: bool, fast_mode: bool = False) -> None:
        prior = self.p_known

        s = min(max(self.p_slip, 1e-4), 0.99)
        g = min(max(self.p_guess, 1e-4), 0.99)

        if fast_mode:
            t = min(max(self.p_learn * 2.0, 0.0), 0.7)
        else:
            t = min(max(self.p_learn, 0.0), 0.5)

        if is_correct:
            numer = prior * (1 - s)
            denom = numer + (1 - prior) * g
        else:
            numer = prior * s
            denom = numer + (1 - prior) * (1 -g)

        if denom <= 0:
            posterior = prior
        else:
            posterior = numer / denom

        posterior = posterior + (1 - posterior) * t
        posterior = max(0.0, min(1.0, posterior))

        if not is_correct and posterior > prior:
            posterior = prior

        self.p_known = posterior

        self.attempts += 1
        if is_correct:
            self.correct += 1
        self.last_outcome_correct = is_correct

    def to_dict(self) -> dict:
        return {
            'card_id': self.card_id,
            'front': self.front,
            'back': self.back,
            'skill_ids': self.skill_ids,

            'p_init': self.p_init,
            'p_learn': self.p_learn,
            'p_slip': self.p_slip,
            'p_guess': self.p_guess,
            'p_known': self.p_known,

            'attempts': self.attempts,
            'correct': self.correct,
            'last_outcome_correct': self.last_outcome_correct,
            'last_review': self.last_review.isoformat() if self.last_review else None,
            'next_due': self.next_due.isoformat() if self.next_due else None,
            'interval_days': self.interval_days,
        }
    @staticmethod
    def from_dict(d: dict) -> 'Card':
        def parse_dt(s: Optional[str]) -> Optional[datetime]:
            if s is None:
                return None
            try:
                return datetime.datetime.fromisoformat(s)
            except Exception:
                return None

        return Card(
            card_id=d['card_id'],
            front=d['front'],
            back=d['back'],
            skill_ids=d.get('skill_ids', []),

            p_init=d.get("p_init", 0.2),
            p_learn=d.get("p_learn", 0.15),
            p_slip=d.get("p_slip", 0.1),
            p_guess=d.get("p_guess", 0.2),
            p_known=d.get("p_known", d.get("p_init", 0.2)),

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
    skills: List[Skill] = field(default_factory=list)
    next_card_id: int = 1
    next_skill_id: int = 1

    current_algorithm: str = "hybrid"
    epsilon: float = 0.2
    min_growth: float = 1.5
    max_growth: float = 4.0

    def add_card(self, front: str, back: str, skill_ids: List[int]) -> Card:
        card = Card(
            card_id=self.next_card_id,
            front=front.strip(),
            back=back.strip(),
            skill_ids=skill_ids,
        )
        self.cards.append(card)
        self.next_card_id += 1
        return card

    def get_card_by_id(self, cid: int) -> Optional[Card]:
        for c in self.cards:
            if c.card_id == cid:
                return c
        return None

    def get_skill_by_id(self, sid: int) -> Optional[Skill]:
        for s in self.skills:
            if s.skill_id == sid:
                return s
        return None

    def get_or_create_skill_by_name(self, name: str) -> Skill:
        name = name.strip()
        for s in self.skills:
            if s.name.lower() == name.lower():
                return s
        skill = Skill(
            skill_id=self.next_skill_id,
            name=name,
        )
        self.skills.append(skill)
        self.next_skill_id += 1
        return skill

    def is_empty(self) -> bool:
        return len(self.cards) == 0


# saving and loading

    def to_dict(self) -> dict:
        return {
            "next_card_id": self.next_card_id,
            "next_skill_id": self.next_skill_id,
            "cards": [c.to_dict() for c in self.cards],
            "skills": [s.to_dict() for s in self.skills],

            "current_algorithm": self.current_algorithm,
            "epsilon": self.epsilon,
            "min_growth": self.min_growth,
            "max_growth": self.max_growth,
        }

    @staticmethod
    def from_dict(d: dict) -> "Deck":
        deck = Deck()
        deck.next_card_id = d.get('next_card_id', 1)
        deck.next_skill_id = d.get('next_skill_id', 1)
        deck.cards = [Card.from_dict(cd) for cd in d.get('cards', [])]
        deck.skills = [Skill.from_dict(sd) for sd in d.get('skills', [])]

        deck.current_algorithm = d.get('current_algorithm', 'hybrid'),
        deck.epsilon = d.get('epsilon', 0.2),
        deck.min_growth = d.get('min_growth', 1.5),
        deck.max_growth = d.get('max_growth', 4.0),

        if not deck.skills and deck.cards:
            default_skill = Skill(skill_id =deck.next_skill_id, name= "general")
            deck.skills.append(default_skill)
            deck.next_skill_id += 1
            for c in deck.cards:
                if not c.skill_ids:
                    c.skill_ids.append(default_skill.skill_id)

        return deck

#SAVING PROGRESS
# this is where the states will save to
SAVE_FILE = "smart_cards_state.json"
LOG_FILE = "smart_cards_log.json"

def save_deck(deck: Deck, path: str = SAVE_FILE) -> None:
    with open(path, "w", encoding="utf-8") as f:
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
    algo = deck.current_algorithm
    if algo == "pure_sr":
        return card.accuracy
    else:
        return card.p_known

def update_card_schedule(card: Card, mastery: float, is_correct:bool, deck: Deck) -> None:
    now = datetime.datetime.now()
    algo = deck.current_algorithm

    if algo == "pure_sr":
        if is_correct:
            if card.interval_days < 1e-6:
                new_interval = 1.0
            else:
                new_interval = card.interval_days*2.0
        else:
            new_interval = 1
    else:
        min_g = deck.min_growth
        max_g = deck.max_growth
        factor = min_g + (max_g - min_g) * mastery
        if is_correct:
            if card.interval_days < 1e-6:
                new_interval = 1.0
            else:
                new_interval = card.interval_days*factor
        else:
            new_interval = 1.0

    card.interval_days = max(0.5, new_interval)
    card.last_review = now
    card.next_due = now + datetime.timedelta(days=card.interval_days)


def compute_card_priority(deck: Deck, card: Card) -> float:
    now = datetime.datetime.now()
    mastery = compute_card_mastery(deck, card)

    if card.next_due is None:
        due_score = 1.0
    else:
        dt = (card.next_due - now).total_seconds() / 3600.0
        if dt <= 0:
            overdue_hours=-dt
            due_score = 1.0 - math.exp(-overdue_hours/24.0)
        else:
            due_score = 1.0 / (1.0 + dt)

    urgency = 1.0 - mastery
    exploration = 0.2 * math.exp(-0.2 * card.attempts)

    last = card.last_outcome_correct
    if last:
        outcome_adjust = -0.05
    elif last is False:
        outcome_adjust = 0.05
    else:
        outcome_adjust = 0.0

    priority = 0.7 * urgency + 0.25 * due_score + exploration + outcome_adjust
    return max(0.0, min(1.0, priority))


def select_next_card(deck: Deck, epsilon: float= 0.2) -> Optional[Card]:
    if deck.is_empty():
        return None

    now = datetime.datetime.now()
    due_cards: List[Card] = [
        c for c in deck.cards
        if c.next_due is None or c.next_due <= now
    ]

    if not due_cards:
        return None

    if random.random() < deck.epsilon:
        return random.choice(deck.cards)

    best_card = None
    best_score = -1.0
    for card in due_cards:
        score = compute_card_priority(deck, card)
        if score > best_score:
            best_score = score
            best_card = card

    return best_card

def log_interaction (
        deck: Deck,
        card: Card,
        is_correct:bool,
        user_resp: str,
        skill_masteries_before: Dict[int, float],
        skill_masteries_after: Dict[int, float],
        mastery_before: float,
        mastery_after: float,
) -> None:
    now = datetime.datetime.now().isoformat()
    entry = {
        "timestamp": now,
        "algorithm": deck.current_algorithm,
        "card_id": card.card_id,
        "front": card.front,
        # ended here
    }

# ----- UI ------

def print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70 + "\n")

def wait_for_enter(msg: str = "Press enter to continue...") -> None:
    input(msg)



# -----MENU-----

# Make updates to the menu!!!!!
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