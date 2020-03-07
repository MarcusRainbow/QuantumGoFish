from abc import ABC
from typing import List, Tuple
from random import randrange
from cards import Cards

class Player(ABC):
    """
    Interface that defines how players interact
    """
    def next_move(self, cards: Cards) -> Tuple[int, int]:
        """
        This player must ask one other player for a card of
        a given suit. Returns other_player, suit.
        """
        pass

    def has_card(self, suit: int, cards: Cards) -> bool:
        """
        Returns true if the player has this card.
        """
        pass

class HumanPlayer(Player):
    """
    Implementation of Player that wraps around user input.
    """
    def __init__(self, me: int):
        self.me = me

    def next_move(self, cards: Cards) -> Tuple[int, int]:
        while True:
            other_input = input("Which player would you like to ask? ")
            suit_input = input("Which suit do you want to ask for? ")
            try:
                other = int(other_input)
                suit = int(suit_input)
                if cards.legal(other, suit, self.me, True):
                    return other, suit
            except:
                if (other_input == 'q' or other_input == 'Q'
                        or suit_input == 'q' or suit_input == 'Q'):
                    exit()
                print("Player and suit must both be integers (q to exit)")
    
    def has_card(self, suit: int, cards: Cards) -> bool:
        """
        If we have definitely have or do not have the card, we
        do not ask the user. Otherwise we must ask
        """
        forced, has = cards.has_card(suit, self.me)
        if forced:
            return has
        while True:
            reply = input(f"Do you have a card of suit {suit}? ")
            if reply == "Y":
                return True
            elif reply == "N":
                return False
            print("Type Y or N")

class RandomPlayer(Player):
    """
    Implementation of Player that randomly selects a legal move.
    """
    def __init__(self, me: int):
        self.me = me

    def next_move(self, cards: Cards) -> Tuple[int, int]:
        number_of_players = cards.number_of_players()
        while True:
            other = randrange(number_of_players - 1)
            if other >= self.me:
                other += 1  # randomly selected other player
            card = randrange(number_of_players)
            if cards.legal(other, card, self.me, False):
                return other, card
    
    def has_card(self, suit: int, cards: Cards) -> bool:
        forced, has = cards.has_card(suit, self.me)
        if forced:
            return has
        
        return randrange(2) == 1

class TestPlayer(Player):
    """
    Implementation of Player that simply plays back a sequence
    of moves. Useful for testing.
    """
    def __init__(self, me: int, requests: List[Tuple[int, int]], responses: List[bool]):
        self.me = me
        self.requests = requests
        self.responses = responses

    def next_move(self, cards: Cards) -> Tuple[int, int]:
        return self.requests.pop(0)
    
    def has_card(self, suit: int, cards: Cards) -> bool:
        return self.responses.pop(0)
