"""
Braeden Connors
Project Started on 11/17/2025

Final Project; Smart Card
(A smart flashcard application)
"""

# Card Model and BKT Algorithm

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Card:
    card_id: int
    front: str
    back: str

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
    last_outcome_correct: Optional[bool] = None

    def update_bkt(self) -> None:
        """
        :return:
        """

    @property
    def accuracy(self) -> float:
        """

        :return:
        """

    def to_dict(self) -> dict:
        """

        :return:
        """

@dataclass
class Deck:
    """

    """
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