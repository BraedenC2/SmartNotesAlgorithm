"""
Braeden Connors
Project Started on 11/17/2025

Final Project; Smart Card
(A smart flashcard application)
"""

# Card Model and BKT Algorithm

from dataclasses import dataclass, field
@dataclass
class Card:
    card_id: int
    front: str
    back: str

    #BKT parameters (adjustable)
    p_init: float = 0.2
    p_learn: float = 0.15
    p_slip: float = 0.1
    p_guess: float = 0.2

    #current knowledge state:
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
        """

        :return:
        """

    def to_dict(self) -> dict:
        """

        :return:
        """

@dataclass
class Desk:
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

