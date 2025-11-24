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

"__________ ALGORITHMS __________"
ALGORITHMS: Dict[str, Dict[str, str]] = {
    "hybrid":{
        "name": "Hybrid BKT + SR",
        "description": (
            "Tracks mastery via BKT. Adapts p_learn/p_slip based on "
            "prediction error (Calibration). Bandit scheduling."
        ),
    },
    "random": {
        "name": "Regular Study",
        "description": "Baseline for validation. Random selection of due cards."
    }
}

"""__________ CALCULATIONS __________"""
def calculate_bkt_update(
        p_known: float,
        p_learn: float,
        p_slip: float,
        p_guess: float,
        is_correct: bool
) -> float:
    s = min(max(p_slip, 1e-4), 0.99)
    g = min(max(p_guess, 1e-4), 0.99)
    t = min(max(p_learn, 0.0), 0.99)

    if is_correct:
        numer = p_known * (1 - s)
        denom = numer + (1 - p_known) * g
    else:
        numer = p_known * s
        denom = numer + (1 - p_known) * (1 - g)

    posterior = p_known if denom <= 0 else numer/denom

    posterior = posterior + (1 - posterior) * t

    return max(0.0, min(1.0, posterior))

def predict_correctness(
        p_known: float,
        p_slip: float,
        p_guess: float,
) -> float:
    return p_known * (1 - p_slip) + (1 - p_known) * p_guess

"""__________ DATA MODELS __________"""
@dataclass
class Skill:
    skill_id: int
    name: str

    p_learn: float = 0.15
    p_slip: float = 0.10
    p_guess: float = 0.20

    def adapt_parameters(
            self, p_known: float,
            is_correct: bool,
            learning_rate: float = 0.05):

        predicted_prob = predict_correctness(p_known, self.p_slip, self.p_guess)
        actual = 1.0 if is_correct else 0.0
        error = actual - predicted_prob

        self.p_slip = max(0.01, min(0.4, self.p_slip - (learning_rate * error)))
        self.p_learn = max(0.01, min(0.5, self.p_learn + (learning_rate * error * 0.5)))


    def to_dict(self) -> dict:
        return { k: v for k, v in self.__dict__.items() }

    @staticmethod
    def from_dict(d: dict) -> 'Skill':
        s = Skill(skill_id=d["skill_id"], name=d["name"])
        for k, v in d.items():
            if hasattr(s, k): setattr(s, k, v)
        return s

@dataclass
class Card:
    card_id: int
    front: str
    back: str
    skill_ids: List[int] = field(default_factory=list)

    p_known: float = 0.2
    attempts: int = 0
    correct: int = 0

    last_review: Optional[datetime] = None
    next_due: Optional[datetime] = None
    interval_days: float = 0.0

    def to_dict(self) -> dict:

        d = {k: v for k, v in self.__dict__.items()}
        d['last_review'] = self.last_review.isoformat() if self.last_review else None
        d['next_due'] = self.next_due.isoformat() if self.next_due else None

        return d

    @staticmethod
    def from_dict(d: dict) -> 'Card':
        c = Card(card_id=d["card_id"], front=d["front"], back=d["back"],)
        for k, v in d.items():
            if k not in ['last_review', 'next_due'] and hasattr(c, k):
                setattr(c, k, v)
        if d.get("last_review"): c.last_review = datetime.datetime.fromisoformat(d["last_review"])
        if d.get("next_due"): c.next_due = datetime.datetime.fromisoformat(d["next_due"])
        return c

@dataclass
class Deck:
    cards: List[Card] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)
    next_card_id: int = 1
    next_skill_id: int = 1

    epsilon: float = 0.2

    def get_skill(self, sid: int) -> Optional[Skill]:
        return next((s for s in self.skills if s.skill_id == sid), None)

    def to_dict(self) -> dict:
        return {
            "next_card_id": self.next_card_id,
            "next_skill_id": self.next_skill_id,
            "epsilon": self.epsilon,
            "cards": [c.to_dict() for c in self.cards],
            "skills": [s.to_dict() for s in self.skills],
        }

    @staticmethod
    def from_dict(d: dict) -> "Deck":
        deck = Deck()
        deck.next_card_id = d.get('next_card_id', 1)
        deck.next_skill_id = d.get('next_skill_id', 1)
        deck.epsilon = d.get('epsilon', 0.2)
        deck.cards = [Card.from_dict(x) for x in d.get('cards', [])]
        deck.skills = [Skill.from_dict(x) for x in d.get('skills', [])]
        return deck

SAVE_FILE = "smart_cards_state.json"
LOG_FILE = "smart_cards_log.json"


"""__________ MASTERY LOGIC __________"""

def compute_priority(card: Card) -> float:
    if card.next_due is None: return 2.0

    now = datetime.datetime.now()
    hours_overdue = (now - card.next_due).total_seconds() / 3600
    urgency = max(0.0, math.log(1 + max(0.0, hours_overdue)))

    mastery_gap = 1.0 - card.p_known
    exploration = 1.0 / math.sqrt(1 + card.attempts)
    return (0.5 * urgency) + (0.3 * mastery_gap) + (0.2 * exploration)

def get_next_card(deck: Deck, algorithm: str = "hybrid") -> Optional[Card]:
    candidates = [c for c in deck.cards if c.next_due is None or c.next_due <= datetime.datetime.now()]
    if not candidates: return None

    if algorithm == "random":
        return random.choice(candidates)

    if random.random() < deck.epsilon:
        return random.choice(candidates)

    return max(candidates, key=lambda c: compute_priority(c))

def update_model(deck: Deck, card: Card, is_correct: bool):
    if card.skill_ids:
        skills = [deck.get_skill(sid) for sid in card.skill_ids if deck.get_skill(sid)]
        if skills:
            p_learn = sum(s.p_learn for s in skills) / len(skills)
            p_slip = sum(s.p_slip for s in skills) / len(skills)
            p_guess = sum(s.p_guess for s in skills) / len(skills)
        else:
            p_learn = 0.15
            p_slip = 0.1
            p_guess = 0.2
    else:
        p_learn = 0.15
        p_slip = 0.1
        p_guess = 0.2

    card.p_known = calculate_bkt_update(card.p_known, p_learn, p_slip, p_guess, is_correct)

    for sid in card.skill_ids:
        s = deck.get_skill(sid)
        if s:
            s.adapt_parameters(card.p_known, is_correct)

    now = datetime.datetime.now()
    factor = 1.5 + (2.0 * card.p_known)
    if is_correct:
        raw_int = card.interval_days * factor
        new_int = max(1.0, min(raw_int, 36500.0))
    else:
        new_int = 0.0

    card.interval_days = new_int
    card.last_review = now

    if new_int >0:
        try:
            card.next_due = now + datetime.timedelta(days=new_int)
        except OverflowError:
            card.next_due = now.replace(year=9999)
    else:
        card.next_due = now

    card.attempts += 1
    if is_correct: card.correct += 1


"""__________ UI __________"""

def print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70 + "\n")


"""__________ MENU __________"""

def action_study(deck: Deck) -> None:
    print_header("\nStudy Session")
    while True:
        card = get_next_card(deck, "hybrid")
        if not card:
            print("No cards due")
            break

        print(f"\n[Card #{card.card_id}] P(Known): {card.p_known:.2f}")
        print(f"Q: {card.front}")
        input("Press Enter to reveal....")
        print(f"A: {card.back}")

        res = input("Correct? (y/n/q): ").lower().strip()
        if res == 'q': break
        update_model(deck, card, (res == 'y'))
        print("Model updated")


class VirtualStudent:
    def __init__(self, deck: Deck):
        self.memory = {c.card_id: 0.1 for c in deck.cards}

    def attempt(self, card: Card) -> bool:
        current_mem = self.memory[card.card_id]
        success = random.random() < current_mem

        if success:
            self.memory[card.card_id] = min(0.99, current_mem + 0.1)
        else:
            self.memory[card.card_id] = min(0.99, current_mem + 0.2)

        return success

def action_simulate(deck: Deck):
    print_header("\nValidation Simulation")
    print("-Comparing 'Smart Hybrid' vs 'Random' scheduler-")
    test_cards = deck.cards if deck.cards else [Card(i, f"Q{i}", f"A{i}") for i in range(20)]
    results = {}
    for algo in ["random", "hybrid"]:
        sim_deck = Deck()
        sim_deck.cards = [Card(c.card_id, c.front, c.back) for c in test_cards]
        sim_deck.skills = [Skill(1, "General")]
        for c in sim_deck.cards: c.skill_ids = [1]

        student = VirtualStudent(sim_deck)
        steps = 100

        for _ in range(steps):
            for c in sim_deck.cards: c.next_due = datetime.datetime.now()

            card = get_next_card(sim_deck, algorithm=algo)
            if not card: break
            outcome = student.attempt(card)
            update_model(sim_deck, card, outcome)

        avg_retention = sum(student.memory.values()) / len(student.memory)
        results[algo] = avg_retention

    print(f"\nResults (Average Student Retention after 100 steps):")
    print(f"Random Scheduler: {results['random']:.2%}")
    print(f"Hybrid BKT+SRS:   {results['hybrid']:.2%}")

    if results['hybrid'] > results['random']:
        print("\n[SUCCESS] The Smart Scheduler outperformed regular studying.")
    else:
        print("\n[NOTE] More data needed for significant lift.")

    input("Press Enter to return...")



def main() -> None:


    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            deck = Deck.from_dict(json.load(f))
    else:
        deck = Deck()
        s = Skill(1, "Demonstration Deck")
        deck.skills.append(s)
        deck.cards.append(Card(1, "Front", "Back", [1]))
        deck.cards.append(Card(2, "Hola", "Hello", [1]))

    while True:

        print(f"\nSmartCards | Cards: {len(deck.cards)} | Skills: {len(deck.skills)}")
        print("1) Study (Smart Hybrid)")
        print("2) Offline Validation (Simulation)")
        print("3) Add Card")
        print("4) Save and Quit")

        opt = input("Choice: ")
        if opt == "1":
            action_study(deck)
        elif opt == "2":
            action_simulate(deck)
        elif opt == "3":
            f = input("Front: ")
            b = input("Back: ")
            deck.cards.append(Card(deck.next_card_id, f, b, [1]))
            deck.next_card_id += 1
        elif opt == "4":
            with open(SAVE_FILE, "w") as f:
                json.dump(deck.to_dict(), f, indent=2)
            break

if __name__ == "__main__":
    main()