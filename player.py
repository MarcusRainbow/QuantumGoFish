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
        other, suit, result, _ = self._evaluate_move(this, cards, history, self.max_depth)
        print(f"Result={result}")
        return other, suit

    def _evaluate_move(self, this: int, cards: Cards, history: Set[int], depth: int) -> Tuple[int, int, int, int]:
        """
        Like next_move, but it also returns a result, which says what 
        the final best-case result is as a result of this move.

        Returns a tuple of (other_player, suit, result, draw_position)
        """
        permutation = cards.permutation(this)

        # just for now, override the cache
        # return self._evaluate_move_uncached(this, cards, history, depth, permutation)

        # see whether this move is in the cache
        pos = cards.position_given_permutation(permutation, this)
        n = len(permutation)
        if pos in self._cached_moves:
            other_c, suit_c, result_c = self._cached_moves[pos]
            other = (other_c + this) % n
            result = result_c if result_c < 0 else (result_c + this) % n
            suit = int(permutation[suit_c])

            # Just for debugging, check that the non-cached result is the same
            # Note that because of the way we check for repeats by looking in
            # the history, it is possible that a draw may be possible via more
            # than one route, and different drawing moves may result from
            # different histories. We therefore do not worry if the moves are
            # different but both result in a draw.
            # other_u, suit_u, result_u = self._evaluate_move_uncached(this, cards, history, depth, permutation)
            # if result == -1 and result_u == -1:
            #     pass    # don't worry about the moves if both result in a draw
            # elif other_u != other or suit_u != suit or result_u != result:
            #     print(f"cache fail ({pos}): cards={cards} cached=({other_c}, {suit_c}, {result_c}) => ({other}, {suit}, {result}) uncached={other_u, suit_u, result_u} this={this} perm={permutation}")

            # Always return -1 as the draw position of any cached move. Since
            # the position was cached, we know that it is a genuine forcing draw,
            # so any position will do, so long as it is not in the history. We
            # know that -1 is not a valid position 
            return other, suit, result, -1

        # find the best move and cache it
        other, suit, result, draw_position = self._evaluate_move_uncached(this, cards, history, depth, permutation)
        other_c = (other - this) % n
        result_c = result if result < 0 else (result - this) % n
        found = np.where(permutation == suit)
        assert len(found) == 1 and len(found[0]) == 1
        suit_c = int(found[0][0])

        # Only save winning positions to the cache, as draws may only be a draw given
        # the current history, rather than being indicative of a draw in general. However,
        # if this is a draw and the position that caused the draw is not in our history,
        # we can record it.
        if result_c >= 0 or draw_position not in history:
            self._cached_moves[pos] = (other_c, suit_c, result_c)

        return other, suit, result, draw_position

    def _evaluate_move_uncached(self, this: int, cards: Cards, history: Set[int], 
            depth: int, permutation: np.ndarray) -> Tuple[int, int, int, int]:
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
                return other, suit, winner, -1
            
            # if this move loses immediately, keep looking
            if winner != Cards.NO_WINNER:
                # if any immediate lose was to a player we want to win, add that
                # to the list of other winners
                if preferences and winner in preferences:
                    pref = preferences.index(winner)
                    other_winners[pref] = (other, suit, winner, -1)
                else:
                    # otherwise just consider it a worst case
                    immediate_lose = (other, suit, winner, -1)
                continue
            
            # if we have hit our maximum depth, assume this is a draw
            if depth == 0:
                out_of_depth = (other, suit, -1, -1)
                continue

            # if this move results in a draw, remember it
            next_player = copy_cards.next_player(this)
            position = copy_cards.position_given_permutation(permutation, next_player)
            if position in history:
                draw = (other, suit, -1, position)
                continue        # stop looking if we have hit a draw                

            # remember this position, so we recognise a subsequent draw
            copy_history = deepcopy(history)
            copy_history.add(position)

            # Allow the next player to play their best move
            _, _, next_winner, draw_position = self._evaluate_move(next_player, copy_cards, copy_history, depth - 1)
            
            # If this results in a win for us, play this move
            if next_winner == this:
                return other, suit, next_winner, -1
            
            # If it results in a draw, record it
            if next_winner < 0:
                draw = (other, suit, -1, draw_position)
            
            # if there is a preference list, look along it
            elif preferences and next_winner in preferences:
                pref = preferences.index(next_winner)
                other_winners[pref] = (other, suit, next_winner, 0)

            # Record a losing move, in case we cannot win
            else:
                lose = (other, suit, next_winner, -1)

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

        # if the max depth is zero, do no lookahead -- just say yes
        # unless it results in an immediate lose
        if self.max_has_depth == 0:
            return yes_winner != Cards.NO_WINNER

        if self.preferences:
            preferences = self.preferences[this]
        else:
            preferences = None

        next_player = copy_cards.next_player(other)

        # If this results in an immediate win for someone else or an illegal position,
        # say no (unless we are thinking about second preferences)
        # TODO: Consider raising a warning if Cards.ILLEGAL_CARDS
        if yes_winner != Cards.NO_WINNER:
            if not preferences or yes_winner not in preferences:
                return False
        else:
            # Convert the yes_winner into an eventual winner after looking forward
            copy_history = deepcopy(history)
            _, _, yes_winner, _ = self._evaluate_move(next_player, copy_cards, copy_history, self.max_has_depth - 1)
            
            # If this results in a win for us, say yes
            if yes_winner == this:
                return True

        # now try saying no
        copy_cards = deepcopy(cards)
        copy_cards.no_transfer(suit, this, other, False)
        no_winner = copy_cards.test_winner(other)
        if no_winner == this:
            return False    # saying no gives us an immediate win

        # if this results in an immediate win for someone else or illegal cards, say yes
        if no_winner != Cards.NO_WINNER:
            if not preferences or no_winner not in preferences:
                return True
        else:
            # Allow the next player to play their best move
            copy_history = deepcopy(history)
            _, _, no_winner, _ = self._evaluate_move(next_player, copy_cards, copy_history, self.max_has_depth - 1)
        
            # If this results in a win for us, say no
            if no_winner == this:
                return False
        
        # If yes would have resulted in a draw, then say yes
        if yes_winner < 0:
            return True

        # If no would have resulted in a draw, then say no
        if no_winner < 0:
            return False

        # if there are any preferences for other players, choose the
        # answer that would give them a win
        if preferences:
            if yes_winner in preferences:
                yes_preference = preferences.index(yes_winner)
            else:
                yes_preference = len(preferences)
            if no_winner in preferences:
                no_preference = preferences.index(no_winner)
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
    See what happens if each player wants the previous player to win.
    """
    start = perf_counter()
    result = three_biased_players([[2], [0], [1]])
    print(f"elapsed time: {perf_counter() - start} seconds")
    assert result == -1, "test_three_clever_biased_players: expecting a draw"
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
    Starting from position 222?/000?/111? with player 0 to play, 
    and second choice 2, 0, 1, what is the best move? What is the
    best following move for player 2?
    """
    h0 = Hand()
    h0.known_cards = Counter({2: 3})
    h0.number_of_unknown_cards = 1
    h1 = Hand()
    h1.known_cards = Counter({0: 3})
    h1.number_of_unknown_cards = 1
    h2 = Hand()
    h2.known_cards = Counter({1: 3})
    h2.number_of_unknown_cards = 1
    cards = Cards(3)
    cards.hands = [h0, h1, h2]

    cards.show(0)

    player = CleverPlayer(1000, 1000, [[2], [0], [1]])

    history = set()
    depth = 1000
    other, suit, result, _ = player._evaluate_move(0, cards, history, depth)
    print(f"player 0 asks {other} for {suit} (result={result})")
    assert result == 1
    assert suit == 1
    assert other == 2

    # player 1 must say yes, as he has this card
    has = player.has_card(2, 0, 1, cards, history)
    assert has

    cards.transfer(suit, other, 0, False)
    winner = cards.test_winner(0)
    assert winner == -1     # nobody has won yet
    print()
    cards.show(1)

    # Now player 1 to move
    other, suit, result, _ = player._evaluate_move(1, cards, history, depth)
    print(f"player 1 asks {other} for {suit} (result={result})")
    assert result == 1
    assert suit == 0
    assert other == 2

    # player 2 must say no, otherwise 1 wins immediately
    has = player.has_card(2, 1, 0, cards, history)
    assert not has

    cards.no_transfer(suit, other, 1, False)
    winner = cards.test_winner(1)
    cards.show(2)
    assert winner == 1, "test_next_move: expecting a win for player 1"
    print("----------------")
    print()

if __name__ == "__main__":
    test_next_move()
    test_two_clever_players()
    test_three_clever_players()
    test_three_clever_biased_players()
    test_three_clever_players_of_all_types()
    test_four_clever_players()
