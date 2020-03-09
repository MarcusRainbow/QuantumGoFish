from abc import ABC
from typing import List, Tuple, Set
from random import randrange
from copy import deepcopy
from cards import Cards
from game import play

class Player(ABC):
    """
    Interface that defines how players interact
    """
    def next_move(self, this: int, cards: Cards, history: Set[int]) -> Tuple[int, int]:
        """
        This player must ask one other player for a card of
        a given suit. Returns other_player, suit.
        """
        pass

    def has_card(self, this: int, other: int, suit: int, cards: Cards, history: Set[int]) -> bool:
        """
        Returns true if the player has this card.
        """
        pass

class HumanPlayer(Player):
    """
    Implementation of Player that wraps around user input.
    """
    def __init__(self):
        pass

    def next_move(self, this: int, cards: Cards, history: Set[int]) -> Tuple[int, int]:
        while True:
            other_input = input("Which player would you like to ask? ")
            suit_input = input("Which suit do you want to ask for? ")
            try:
                other = int(other_input)
                suit = int(suit_input)
                if cards.legal(other, suit, this, True):
                    return other, suit
            except:
                if (other_input == 'q' or other_input == 'Q'
                        or suit_input == 'q' or suit_input == 'Q'):
                    exit()
                print("Player and suit must both be integers (q to exit)")
    
    def has_card(self, this: int, other: int, suit: int, cards: Cards, history: Set[int]) -> bool:
        """
        If we have definitely have or do not have the card, we
        do not ask the user. Otherwise we must ask
        """
        forced, has = cards.has_card(suit, this, other)
        if forced:
            return has
        while True:
            reply = input(f"Do you have a card of suit {suit}? ")
            if reply == "Y" or reply == "y":
                return True
            elif reply == "N" or reply == "n":
                return False
            print("Y or N")

class RandomPlayer(Player):
    """
    Implementation of Player that randomly selects a legal move.
    """
    def __init__(self):
        pass

    def next_move(self, this: int, cards: Cards, history: Set[int]) -> Tuple[int, int]:
        number_of_players = cards.number_of_players()
        while True:
            other = randrange(number_of_players - 1)
            if other >= this:
                other += 1  # randomly selected other player
            card = randrange(number_of_players)
            if cards.legal(other, card, this, False):
                return other, card
    
    def has_card(self, this: int, other: int, suit: int, cards: Cards, history: Set[int]) -> bool:
        forced, has = cards.has_card(suit, this, other)
        if forced:
            return has
        
        return randrange(2) == 1

class TestPlayer(Player):
    """
    Implementation of Player that simply plays back a sequence
    of moves. Useful for testing.
    """
    def __init__(self, requests: List[Tuple[int, int]], responses: List[bool]):
        self.requests = requests
        self.responses = responses

    def next_move(self, this: int, cards: Cards, history: Set[int]) -> Tuple[int, int]:
        return self.requests.pop(0)
    
    def has_card(self, this: int, other: int, suit: int, cards: Cards, history: Set[int]) -> bool:
        return self.responses.pop(0)

class CleverPlayer(Player):
    """
    Implementation of Player that looks ahead, playing the best move
    available.
    """
    def __init__(self):
        pass

    def next_move(self, this: int, cards: Cards, history: Set[int]) -> Tuple[int, int]:
        other, suit, _ = self._evaluate_move(this, cards, history)
        return other, suit

    def _evaluate_move(self, this: int, cards: Cards, history: Set[int]) -> Tuple[int, int, int]:
        """
        Like next_move, but it also returns a result, which says what 
        the final best-case result is as a result of this move.
        """
        # try all the legal moves. If there are none, it is stalemate
        legal_moves = cards.legal_moves(this)
        assert len(legal_moves) > 0
        next_player = (this + 1) % cards.number_of_players()
        draw = None
        lose = None
        immediate_lose = None
        for other, suit in legal_moves:
            copy_cards = deepcopy(cards)
            has = self.has_card(other, this, suit, copy_cards, history)
            if has:
                copy_cards.transfer(suit, other, this, False)
            else:
                copy_cards.no_transfer(suit, other, this, False)
            winner = copy_cards.test_winner(this)

            # if this move wins immediately, play it
            if winner == this:
                return other, suit, winner
            
            # if this move loses immediately, keep looking
            if winner >= 0:
                immediate_lose = other, suit, winner
                continue
            
            # if this move results in a draw, remember it
            position = copy_cards.position()
            immediate_draw = position in history
            if immediate_draw:
                draw = (other, suit, -1)
            copy_history = deepcopy(history)
            copy_history.add(position)
            if immediate_draw:
                continue        # stop looking if we have hit a draw

            # Allow the next player to play their best move
            _, _, next_winner = self._evaluate_move(next_player, copy_cards, copy_history)
            
            # If this results in a win for us, play this move
            if next_winner == this:
                return other, suit, winner
            
            # If it results in a draw, record it
            if next_winner < 0:
                draw = (other, suit, -1)

            # Record a losing move, in case we cannot win
            else:
                lose = (other, suit, next_winner)

        # force a draw if we can
        if draw is not None:
            return draw

        # an eventual lose is slightly better than an immediate one
        if lose is not None:
            return lose
 
        # nothing works. Just play any losing move
        assert immediate_lose is not None
        return immediate_lose
    
    def has_card(self, this: int, other: int, suit: int, cards: Cards, history: Set[int]) -> bool:
        # if the move is forced, don't think about it
        forced, has = cards.has_card(suit, this, other)
        if forced:
            return has

        # otherwise make the move that results in a win or failing that a draw
        # try saying yes, which is generally the best option.
        copy_cards = deepcopy(cards)
        copy_cards.transfer(suit, this, other, False)
        winner = copy_cards.test_winner(other)
        if winner == this:
            return True     # saying yes gives us an immediate win!

        # if this results in an immediate win for someone else, say no
        if winner >= 0:
            return False

        # Allow the next player to play their best move
        next_player = (other + 1) % cards.number_of_players()
        copy_history = deepcopy(history)
        _, _, next_winner = self._evaluate_move(next_player, copy_cards, copy_history)
        
        # If this results in a win for us, say yes
        if next_winner == this:
            return True
        
        # If it results in a draw, record it
        yes_results_in_draw = next_winner < 0

        # now try saying no
        copy_cards = deepcopy(cards)
        copy_cards.no_transfer(suit, this, other, False)
        winner = copy_cards.test_winner(other)
        if winner == this:
            return False    # saying no gives us an immediate win

        # if this results in an immediate win for someone else, say yes
        if winner >= 0:
            return True

        # Allow the next player to play their best move
        copy_history = deepcopy(history)
        _, _, next_winner = self._evaluate_move(next_player, copy_cards, copy_history)
        
        # If this results in a win for us, say no
        if next_winner == this:
            return False
        
        # If yes would have resulted in a draw, then say yes
        if yes_results_in_draw:
            return True
        
        # Nothing works -- just say no
        return False

def test_two_clever_players():
    players = [CleverPlayer(), CleverPlayer()]
    result = play(players)
    if result == -1:
        print("Result is a draw")
    else:
        print(f"Win for player {result}")
    assert result == -1, "test_two_clever_players: expecting a draw"
    print("----------------")
    print()

def test_three_clever_players():
    players = [CleverPlayer(), CleverPlayer(), CleverPlayer()]
    result = play(players)
    if result == -1:
        print("Result is a draw")
    else:
        print(f"Win for player {result}")
    assert result == -1, "test_two_clever_players: expecting a draw"
    print("----------------")
    print()

if __name__ == "__main__":
    test_two_clever_players()
    test_three_clever_players()
