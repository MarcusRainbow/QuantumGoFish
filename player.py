from abc import ABC
from typing import List, Tuple, Set
from random import randrange
from collections import Counter
from copy import deepcopy
from cards import Cards, Hand
from game import play
from time import perf_counter
import numpy as np

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
    def __init__(self, max_depth = 1000, max_has_depth = 10, preferences = None):
        """
        The max_depth specifies how far ahead the player will look
        before making a move. For example, zero means only consider
        the immediate move, so don't play into an immediate lose.

        The max_has_depth specifies how far ahead the player will look
        before saying whether they have a card. For example, zero means
        only worry about the immediate effect.

        If preferences is specified, it states who the each of the 
        players wants to win. It is a list of lists of player numbers.

        If other_player is supplied, we share its cache.
        """
        self.max_depth = max_depth
        self.max_has_depth = max_has_depth
        self.preferences = preferences
        self.log_level = -1

        # dictionary of moves and their outcomes, matching the results of
        # _evaluate_move. This cache is shared between all players that are
        # represented by this instance of CleverPlayer
        self._cached_moves = {}

    def next_move(self, this: int, cards: Cards, history: Set[int]) -> Tuple[int, int]:
        other, suit, _ = self._evaluate_move(this, cards, history, self.max_depth)
        return other, suit

    def _evaluate_move(self, this: int, cards: Cards, history: Set[int], depth: int) -> Tuple[int, int, int]:
        """
        Like next_move, but it also returns a result, which says what 
        the final best-case result is as a result of this move.

        Returns a tuple of (other_player, suit, result)
        """
        permutation = cards.permutation(this)

        # just for now, override the cache
        # return self._evaluate_move_uncached(this, cards, history, depth, permutation)

        # see whether this move is in the cache
        pos = cards.position_given_permutation(permutation, this)
        # if self.log_level < 0 and pos == 132524224923:
        #     print(f"_evaluate_move: pos {pos}: permutation {permutation} history {history}")
        #     self.log_level = 0
        
        # if self.log_level >= 0:
        #     print(f"{' ' * self.log_level}_evaluate_move: cards {cards} this={this}")
        #     self.log_level += 1

        n = len(permutation)
        if pos in self._cached_moves:
            other_c, suit_c, result_c = self._cached_moves[pos]
            other = (other_c + this) % n
            result = result_c if result_c < 0 else (result_c + this) % n
            suit = int(permutation[suit_c])

            # if self.log_level >= 0:
            #     self.log_level -= 1
            #     print(f"{' ' * self.log_level}_evaluate_move: ask {other} for {suit}: {result} (cached)")
            #     if self.log_level == 0 and pos == 132524224923:
            #         self.log_level = -1

            # # Just for debugging, check that the non-cached result is the same
            # # Note that because of the way we check for repeats by looking in
            # # the history, it is possible that a draw may be possible via more
            # # than one route, and different drawing moves may result from
            # # different histories. We therefore do not worry if the moves are
            # # different but both result in a draw.
            # if pos == 132524224923:
            #     other_u, suit_u, result_u = self._evaluate_move_uncached(this, cards, history, depth, permutation)
            #     if result == -1 and result_u == -1:
            #         pass    # don't worry about the moves if both result in a draw
            #     elif other_u != other or suit_u != suit or result_u != result:
            #         print(f"cache fail ({pos}): cards={cards} cached=({other_c}, {suit_c}, {result_c}) => ({other}, {suit}, {result}) uncached={other_u, suit_u, result_u} this={this} perm={permutation}")

            return other, suit, result

        # find the best move and cache it
        other, suit, result = self._evaluate_move_uncached(this, cards, history, depth, permutation)
        other_c = (other - this) % n
        result_c = result if result < 0 else (result - this) % n
        found = np.where(permutation == suit)
        assert len(found) == 1 and len(found[0]) == 1
        suit_c = int(found[0][0])
        self._cached_moves[pos] = (other_c, suit_c, result_c)

        # if self.log_level >= 0:
        #     self.log_level -= 1
        #     print(f"{' ' * self.log_level}_evaluate_move: ask {other} for {suit}: {result} (uncached)")
        #     if self.log_level == 0 and pos == 132524224923:
        #         self.log_level = -1

        return other, suit, result

    def _evaluate_move_uncached(self, this: int, cards: Cards, history: Set[int], depth: int, permutation: np.ndarray) -> Tuple[int, int, int]:
        """
        Like _evaluate_move, but not using the cache.
        """
        # try all the legal moves. (We know there must be some, as the player has some cards)
        legal_moves = cards.legal_moves_given_permutation(this, permutation)
        assert len(legal_moves) > 0
        draw = None
        out_of_depth = None
        lose = None
        immediate_lose = None
        if self.preferences:
            preferences = self.preferences[this]
            other_winners = [None] * len(preferences)
        else:
            preferences = None
            other_winners = None

        for other, suit in legal_moves:
            copy_cards = deepcopy(cards)
            has = self.has_card(other, this, suit, copy_cards, history)
            if has:
                copy_cards.transfer(suit, other, this, False)
            else:
                copy_cards.no_transfer(suit, other, this, False)
            winner = copy_cards.test_winner(this)
            if winner == Cards.ILLEGAL_CARDS:
                print(f"WARNING: illegal cards after move has={has} suit={suit} other={other} this={this} moves={legal_moves}")
                cards.show(this)
                print("becomes")
                copy_cards.show(copy_cards.next_player(this))
                print("-------------")
                continue

            # if this move wins immediately, play it
            if winner == this:
                return other, suit, winner
            
            # if this move loses immediately, keep looking
            if winner != Cards.NO_WINNER:
                immediate_lose = other, suit, winner
                continue
            
            # if we have hit our maximum depth, assume this is a draw
            if depth == 0:
                out_of_depth = (other, suit, -1)
                continue

            # if this move results in a draw, remember it
            next_player = copy_cards.next_player(this)
            position = copy_cards.position_given_permutation(permutation, next_player)
            # if position == 34401731532:
            #     print(f"testing for draw, with cards {copy_cards} and this={this}")
            if position in history:
                # if position == 34401731532:
                #     print(f"draw at position {position} with cards {copy_cards} and this={this}")
                draw = (other, suit, -1)
                continue        # stop looking if we have hit a draw                

            # remember this position, so we recognise a subsequent draw
            copy_history = deepcopy(history)
            copy_history.add(position)

            # Allow the next player to play their best move
            _, _, next_winner = self._evaluate_move(next_player, copy_cards, copy_history, depth - 1)
            
            # If this results in a win for us, play this move
            if next_winner == this:
                return other, suit, winner
            
            # If it results in a draw, record it
            if next_winner < 0:
                draw = (other, suit, -1)
            
            # if there is a preference list, look along it
            elif preferences and next_winner in preferences:
                pref = preferences.index(next_winner)
                other_winners[pref] = (other, suit, next_winner)

            # Record a losing move, in case we cannot win
            else:
                lose = (other, suit, next_winner)

        # force a draw if we can
        if draw is not None:
            return draw
        
        # if we were unable to probe to the end of any moves, use one
        if out_of_depth is not None:
            return out_of_depth
        
        # is there a preference to which other players we want to win?
        if other_winners:
            for other_winner in other_winners:
                if other_winner:
                    return other_winner

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
        yes_winner = copy_cards.test_winner(other)
        if yes_winner == this:
            return True     # saying yes gives us an immediate win!

        # If this results in an immediate win for someone else or an illegal position, say no
        # TODO: Consider raising a warning if Cards.ILLEGAL_CARDS
        if yes_winner != Cards.NO_WINNER:
            return False

        # if the max depth is zero, do no lookahead -- just say yes
        if self.max_has_depth == 0:
            return True

        # Allow the next player to play their best move
        next_player = copy_cards.next_player(this)
        copy_history = deepcopy(history)
        _, _, next_yes_winner = self._evaluate_move(next_player, copy_cards, copy_history, self.max_has_depth - 1)
        
        # If this results in a win for us, say yes
        if next_yes_winner == this:
            return True
        
        # If it results in a draw, record it
        yes_results_in_draw = next_yes_winner < 0

        # now try saying no
        copy_cards = deepcopy(cards)
        copy_cards.no_transfer(suit, this, other, False)
        no_winner = copy_cards.test_winner(other)
        if no_winner == this:
            return False    # saying no gives us an immediate win

        # if this results in an immediate win for someone else or illegal cards, say yes
        # TODO: Consider raising a warning if Cards.ILLEGAL_CARDS
        if no_winner != Cards.NO_WINNER:
            return True

        # Allow the next player to play their best move
        copy_history = deepcopy(history)
        _, _, next_no_winner = self._evaluate_move(next_player, copy_cards, copy_history, self.max_has_depth - 1)
        
        # If this results in a win for us, say no
        if next_no_winner == this:
            return False
        
        # If yes would have resulted in a draw, then say yes
        if yes_results_in_draw:
            return True

        # if there are any preferences for other players, choose the
        # answer that would give them a win
        if self.preferences:
            preferences = self.preferences[this]
            if next_yes_winner in preferences:
                yes_preference = preferences.index(next_yes_winner)
            else:
                yes_preference = len(preferences)
            if next_no_winner in preferences:
                no_preference = preferences.index(next_no_winner)
            else:
                no_preference = len(preferences)
            if yes_preference < no_preference:
                return True
            elif no_preference < yes_preference:
                return False
        
        # Nothing works -- just say no
        return False

def test_two_clever_players():
    start = perf_counter()
    player = CleverPlayer(1000, 1000)
    players = [player, player]
    result = play(players)
    if result == -1:
        print("Result is a draw")
    else:
        print(f"Win for player {result}")
    print(f"elapsed time: {perf_counter() - start} seconds")
    assert result == -1, "test_two_clever_players: expecting a draw"
    print("----------------")
    print()

def test_three_clever_players():
    start = perf_counter()
    player = CleverPlayer(1000, 1000)
    players = [player, player, player]
    result = play(players)
    if result == -1:
        print("Result is a draw")
    else:
        print(f"Win for player {result}")
    print(f"elapsed time: {perf_counter() - start} seconds")
    # assert result == -1, "test_three_clever_players: expecting a draw"
    print("----------------")
    print()

def three_biased_players(preferences: List[List[int]]):
    player = CleverPlayer(1000, 1000, preferences)
    players = [player, player, player]
    result = play(players)
    if result == -1:
        print("Result is a draw")
    else:
        print(f"Win for player {result}")
    return result

def test_three_clever_biased_players():
    """
    See what happens if players 0 and 1 both prefer player 2 to win if they
    cannot, and player 2 wants player 0.
    """
    start = perf_counter()
    result = three_biased_players([[2], [2], [0]])
    print(f"elapsed time: {perf_counter() - start} seconds")
    # assert result == 2, "test_three_clever_biased_players: expecting a win for player 2"
    print("----------------")
    print()

def test_three_clever_players_of_all_types():
    """
    Try all combinations of preferences for the three player game
    """
    start = perf_counter()
    for i0 in [1, 2]:
        for i1 in [0, 2]:
            for i2 in [0, 1]:
                preferences = [[i0], [i1], [i2]]
                result = three_biased_players(preferences)
                print(f"With second preferences {preferences}: ", end='')
                if result == -1:
                    print("Result is a draw")
                else:
                    print(f"Win for player {result}")

    print(f"elapsed time: {perf_counter() - start} seconds")
    print("----------------")
    print()

def test_four_clever_players():
    start = perf_counter()
    player = CleverPlayer(1000, 1000)
    players = [player, player, player, player]
    result = play(players)
    if result == -1:
        print("Result is a draw")
    else:
        print(f"Win for player {result}")
    print(f"elapsed time: {perf_counter() - start} seconds")
    assert result == 1, "test_four_clever_players: expecting a win for player 1"
    print("----------------")
    print()

def test_next_move():
    """
    With history {1359256201, 4599097738, 28122892300, 17653942292, 17388062740, 17582622744, 406947864},
    and cards 2??x2/2?x2/221100?x2, player 0 to play, what is the best next move?

    Compare this with {1342245512, 44174741641, 1359256201, 275286032, 402786328}
    and cards 221100?x0/0??x0/0?x0, player 1 to play, which ought to have the same result,
    allowing for player rotation.
    """
    h0 = Hand()
    h0.known_cards = Counter({2: 1})
    h0.number_of_unknown_cards = 2
    h0.known_voids = {2}
    h1 = Hand()
    h1.known_cards = Counter({2: 1})
    h1.number_of_unknown_cards = 1
    h1.known_voids = {2}
    h2 = Hand()
    h2.known_cards = Counter({2: 2, 1: 2, 0: 2})
    h2.number_of_unknown_cards = 1
    h2.known_voids = {2}
    h3 = Hand()
    h3.known_cards = Counter({3: 2})
    h3.number_of_unknown_cards = 1
    h3.known_voids = {0, 1}
    cards = Cards(3)
    cards.hands = [h0, h1, h2]

    this = 0
    permutation = cards.permutation(this)
    pos = cards.position_given_permutation(permutation, this)
    print(f"test_next_move: cards={cards} pos={pos}")
    assert pos == 17519659660

if __name__ == "__main__":
    # test_next_move()
    test_two_clever_players()
    test_three_clever_players()
    test_three_clever_biased_players()
    test_three_clever_players_of_all_types()
    # test_four_clever_players()
