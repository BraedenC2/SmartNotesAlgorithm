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
            "Tracks mastery via BKT. Adapts p_learn/p_slip based on "
            "prediction error (Calibration). Bandit scheduling."
        ),
    },
    "random": {
        "name": "Regular Study",
        "description": "Baseline for validation. Random selection of due cards."
    }
}


# Calculations

def calculate_bkt_update(
        p_known: float,
        p_learn: float,
        p_slip: float,
        p_guess: float,
        is_correct: bool
) -> float:
    s = min(max(p_slip, 1e-4), 0.99)
    g = min(max(p_guess, 1e-4), 0.99)
    t = min(max(p_known, 0.0), 0.99)

    if is_correct:
        numer = p_known * (1 -s)
        denon = numer + (1 - p_known) * g
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
    return p_known * (1-p_slip) + (1-p_known) * p_guess

# data models:

@dataclass
class Skill:
    skill_id: int
    name: str

    #not adjustable by the user... Now adaptive!
    #p_init: float = 0.2
    p_learn: float = 0.15
    p_slip: float = 0.1
    p_guess: float = 0.2

    def adapt_parameters(self, p_known: float, is_correct: bool, learning_rate: float = 0.05):
        predicted_prob = predict_correctness(p_known, self.p_slip, self.p_guess)
        actual = 1.0 if is_correct else 0.0
        error = actual - predicted_prob

        self.p_learn = max(0.01, min(0.4, self.p_slip -(learning_rate * error)))
        self.p_learn = max(0.01, min(0.5, self.p_learn +(learning_rate * error * 0.5)))


    def to_dict(self) -> dict:
        return {
            k: v for k, v in self.__dict__.items()
        }

    @staticmethod
    def from_dict(d: dict) -> 'Skill':
        s = Skill(skill_id=d["skill_id"], name=d["name"], p_learn=d["p_learn"])
        for k,v in d.items():
            if hasattr(s, k): setattr(s, k, v)
        return s

@dataclass
class Card:
    card_id: int
    front: str
    back: str
    skill_ids: List[int] = field(default_factory=list)


   # p_init: float = 0.2
    #p_learn: float = 0.15
   # p_slip: float = 0.1
   # p_guess: float = 0.2
    p_known: float = 0.2

    #stats
    attempts: int = 0
    correct: int = 0
    # last_outcome_correct: Optional[bool] = None

    #scheduling
    last_review: Optional[datetime] = None
    next_due: Optional[datetime] = None
    interval_days: float = 0.0
    """
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
        """

    def to_dict(self) -> dict:

        d = {k: v for k, v in self.__dict__.items()}
        d['last_review'] = self.last_review.isoformat() if self.last_review else None
        d['next_due'] = self.next_due.isoformat() if self.next_due else None

        return d
        """
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
            
        }"""
    @staticmethod
    def from_dict(d: dict) -> 'Card':
        c = Card(card_id=d["card_id"], front=d["front"], back=d["back"],)
        for k, v in d.items():
            if k not in ['last_review', 'next_due'] and hasattr(c, k):
                setattr(c, k, v)
        if d.get("last_review"): c.last_review = datetime.datetime.fromisoformat(d["last_review"])
        if d.get("next_due"): c.next_due = datetime.datetime.fromisoformat(d["next_due"])
        return c
        # def parse_dt(s: Optional[str]) -> Optional[datetime]:
        #     if s is None:
        #         return None
        #     try:
        #         return datetime.datetime.fromisoformat(s)
        #     except Exception:
        #         return None
        #
        # return Card(
        #     card_id=d['card_id'],
        #     front=d['front'],
        #     back=d['back'],
        #     skill_ids=d.get('skill_ids', []),
        #
        #     p_init=d.get("p_init", 0.2),
        #     p_learn=d.get("p_learn", 0.15),
        #     p_slip=d.get("p_slip", 0.1),
        #     p_guess=d.get("p_guess", 0.2),
        #     p_known=d.get("p_known", d.get("p_init", 0.2)),
        #
        #     attempts=d.get('attempts',0),
        #     correct=d.get('correct',0),
        #     last_outcome_correct=d.get('last_outcome_correct',None),
        #     last_review=parse_dt(d.get('last_review')),
        #     next_due=parse_dt(d.get('next_due')),
        #     interval_days=d.get('interval_days', 0.0),
        #
        # )
    # @property
    # def accuracy(self) -> float:
    #     if self.attempts == 0:
    #         return 0.0
    #     return self.correct / self.attempts



@dataclass
class Deck:
    cards: List[Card] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)
    next_card_id: int = 1
    next_skill_id: int = 1

    # current_algorithm: str = "hybrid"
    epsilon: float = 0.2
    # min_growth: float = 1.5
    # max_growth: float = 4.0

    def get_skill(self, sid: int) -> Optional[Skill]:
        return next((s for s in self.skills if s.skill_id == sid), None)

    # def add_card(self, front: str, back: str, skill_ids: List[int]) -> Card:
    #     card = Card(
    #         card_id=self.next_card_id,
    #         front=front.strip(),
    #         back=back.strip(),
    #         skill_ids=skill_ids,
    #     )
    #     self.cards.append(card)
    #     self.next_card_id += 1
    #     return card
    #
    # def get_card_by_id(self, cid: int) -> Optional[Card]:
    #     for c in self.cards:
    #         if c.card_id == cid:
    #             return c
    #     return None
    #
    # def get_skill_by_id(self, sid: int) -> Optional[Skill]:
    #     for s in self.skills:
    #         if s.skill_id == sid:
    #             return s
    #     return None
    #
    # def get_or_create_skill_by_name(self, name: str) -> Skill:
    #     name = name.strip()
    #     for s in self.skills:
    #         if s.name.lower() == name.lower():
    #             return s
    #     skill = Skill(
    #         skill_id=self.next_skill_id,
    #         name=name,
    #     )
    #     self.skills.append(skill)
    #     self.next_skill_id += 1
    #     return skill
    #
    # def is_empty(self) -> bool:
    #     return len(self.cards) == 0


# saving and loading

    def to_dict(self) -> dict:
        return {
            "next_card_id": self.next_card_id,
            "next_skill_id": self.next_skill_id,
            "epsilon": self.epsilon,
            "cards": [c.to_dict() for c in self.cards],
            "skills": [s.to_dict() for s in self.skills],

            # "current_algorithm": self.current_algorithm,
            # "min_growth": self.min_growth,
            # "max_growth": self.max_growth,
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


        deck.current_algorithm = d.get('current_algorithm', 'hybrid'),
        deck.min_growth = d.get('min_growth', 1.5),
        deck.max_growth = d.get('max_growth', 4.0),

        if not deck.skills and deck.cards:
            default_skill = Skill(skill_id =deck.next_skill_id, name= "general")
            deck.skills.append(default_skill)
            deck.next_skill_id += 1
            for c in deck.cards:
                if not c.skill_ids:
                    c.skill_ids.append(default_skill.skill_id)


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

def compute_priority(deck: Deck, card: Card) -> float:
    if card.next_due is None: return 2.0

    now = datetime.datetime.now()
    hours_overdue = (now - card.next_due).total_seconds() / 3600
    urgency = max(0.0, math.log(1 + max(0, hours_overdue)))

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

    return max(candidates, key=lambda c: compute_priority(deck, c))

def compute_card_mastery(deck: Deck, card: Card) -> float:
    algo = deck.current_algorithm
    if algo == "pure_sr":
        return card.accuracy
    else:
        return card.p_known

def update_model(deck: Deck, card: Card, is_correct: bool):
    """"""

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
        "skill_ids": card.skill_ids,
        "is_correct": is_correct,
        "user_resp": user_resp,
        "skill_masteries_before": skill_masteries_before,
        "skill_masteries_after": skill_masteries_after,
        "card_mastery_before": mastery_before,
        "card_mastery_after": mastery_after,
        "card_attempts_total": card.attempts,
        "card_correct_total": card.correct,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

# ----- UI ------

def print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70 + "\n")

def wait_for_enter(msg: str = "Press enter to continue...") -> None:
    input(msg)

def prompt_float(prompt: str, current:float) -> float:
    s = input(f"{prompt} [current: {current}]: ").strip()
    if not s:
        return current
    try:
        return float(s)
    except ValueError:
        print("Invalid number")
        return current


# -----MENU-----

def action_add_card(deck: Deck) -> None:
    print("Add new card: ")
    front = input("Front: (term/question): ").strip()

    if not front:
        print("Front cannot be empty. Card not added.")
        wait_for_enter()
        return

    back = input("Back: (Definition/Answer): ").strip()
    if not back:
        print("Back cannot be empty. Card not added.")
        wait_for_enter()
        return

    print("\nTag this card with skills.")
    skills_line = input("Skill names (comma-separated, blank for general): ").strip()

    if not skills_line:
        skill_names = ["general"]
    else:
        skill_names = [s.strip() for s in skills_line.split(",") if s.strip()]

    skill_ids: List[int] = []
    for name in skill_names:
        skill = deck.get_or_create_skill_by_name(name)
        if skill.skill_id not in skill_ids:
            skill_ids.append(skill.skill_id)

    card = deck.add_card(front, back, skill_ids)
    print(f"\nCard #{card.card_id} created with skills: "
          f"{', '.join(deck.get_skill_by_id(sid).name for sid in skill_ids)}")
    wait_for_enter()

def action_view_cards(deck: Deck) -> None:
    print("All Cards: ")
    if deck.is_empty():
        print("Empty deck")
        wait_for_enter()
        return

    print(f"Active algorithm: {ALGORITHMS[deck.current_algorithm]['name']}")
    print()
    print(f"{'ID':<4} {'Mastery':<10} {'Attempts':<9} {'Correct':<9} {'Due':<20} Front")
    print("-" * 90)
    now = datetime.datetime.now()

    for c in sorted(deck.cards, key=lambda x: x.card_id):
        mastery = f"{compute_card_mastery(deck, c):.2f}"
        due_str = (
            c.next_due.strftime("%Y-%m-%d %H:%M")
            if c.next_due is not None
            else "never"
        )
        if c.next_due is not None and c.next_due <= now:
            due_str += " (due)"

        print(f"{c.card_id:<4} {mastery:<10} {c.attempts:<9} {c.correct:<9} {due_str:<20} {c.front}")
        print()
        wait_for_enter()

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

    print(f"Current algorithm: {ALGORITHMS[deck.current_algorithm]['name']}\n")
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

def action_change_algorithm(deck: Deck) -> None:
    print_header("Change Algorithm")

def action_tune_parameters(deck: Deck) -> None:
    print_header("Tune Parameters")





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

    #deck = load_deck()

    while True:
        """
        print_header("Welcome to SmartCards!")
        print(f"Active algorithm: {ALGORITHMS[deck.current_algorithm]['name']}")
        print(f"Exploration epsilon: {deck.epsilon:.2f}")
        print()
        print("MENU:")
        print("1. Add new card")
        print("2. View all cards")
        print("3. Study cards")
        print("4. Mastery Report (Cards)")
        print("5. Mastery Report (Skills)")
        print("6. Change algorithm")
        print("7. Personalization")
        print("8. Save and Quit")
        print("0. Exit without saving")
        """

        print(f"\nSmartCards | Cards: {len(deck.cards)} | Skills: {len(deck.skills)}")
        print("1) Study (Smart Hybrid)")
        print("2) Offline Validation (Simulation)")
        print("3) Add Card")
        print("4) Save and Quit")

        opt = input("Choice: ")
        if opt == "1":
            action_study(deck)
        elif opt == "2":
            """"""
        elif opt == "3":
            f = input("Front: ")
            b = input("Back: ")
            deck.cards.append(Card(deck.next_card_id, f, b, [1]))
            deck.next_card_id += 1
        elif opt == "4":
            with open(SAVE_FILE, "w") as f:
                json.dump(deck.to_dict(), f, indent=2)
            break

"""
        user_input = input("Enter your choice: ").strip()
        if user_input == "1":
            action_add_card(deck)
        elif user_input == "2":
            action_view_cards()
        elif user_input == "3":
            action_study(deck)
        elif user_input == "4":
            action_mastery_report_cards(deck)
        elif user_input == "5":
            action_mastery_report_skills(deck)
        elif user_input == "6":
            action_change_algorithm(deck)
        elif user_input == "7":
            action_tune_parameters(deck)
        elif user_input == "8":
            save_deck(deck)
            print_header("Saved! Exiting...")
            break
        elif user_input == "0":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Try again.\n")
"""

if __name__ == "__main__":
    main()