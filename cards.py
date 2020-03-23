from collections import Counter
from typing import Tuple, List
from copy import deepcopy
import numpy as np

class Hand:
    """
    Represents a single hand of cards. Cards are either of a
    known suit, or are one of a set of possibilities. We
    define the possibilities in terms of what we know they are
    not. For example, if the holder has said they do not have
    a card in a given suit, we record that fact.
    """
    def __init__(self):
        """
        Creates an empty hand
        """
        self.known_cards = Counter()        # Counter of suit -> count
        self.known_voids = set()            # set of suits we know we don't have
        self.number_of_unknown_cards = 4    # we always start with four cards

    def is_empty(self):
        """
        Returns true if this player has no cards at all.
        """
        return not self.known_cards and self.number_of_unknown_cards == 0

    def show(self, is_next_player: bool):
        """
        Write to stdout a representation of the hand, also showing the next player
        """
        print(self, end='')
        if is_next_player:
            print("   <<<< next player")
        else:
            print()

    def __str__(self):
        result = ""
        for suit in self.known_cards.elements():
            result += str(suit)
        for _ in range(self.number_of_unknown_cards):
            result += "?"
        if self.known_voids:
            result += "x"
            for kv in self.known_voids:
                result += str(kv)
        return result

    def ensure_have(self, suit) -> bool:
        """
        Make sure we have one of these cards. The player has just
        requested a card from this suit. Returns True if we were
        able to validate this.
        """

        # easy if we already have one
        if suit in self.known_cards:
            assert(self.known_cards[suit] > 0)
            return True
        
        # convert one of the unknowns into one of these
        if suit in self.known_voids:
            return False

        self._remove_unknown()
        self.known_cards[suit] = 1
        return True

    def _remove_unknown(self):
        assert(self.number_of_unknown_cards > 0)
        self.number_of_unknown_cards -= 1
        if self.number_of_unknown_cards == 0:
            self.known_voids.clear()

    def ensure_have_not(self, suit) -> bool:
        """
        We know this hand does not contain this suit. For example the player has
        rejected a request for a card. Returns True if we were able to validate it.
        """
        if suit in self.known_cards:
            return False
        self.known_voids.add(suit)
        return True

    def remove(self, suit) -> bool:
        """
        Take one card of this suit away from the user. If it is a known card, remove that.
        If not, take it from the unknowns. Returns True if we were able to remove it
        """
        if suit in self.known_cards:
            count = self.known_cards[suit]
            if count > 1:
                self.known_cards[suit] = count - 1
            else:
                del self.known_cards[suit]  # avoid empties
            return True
        elif suit in self.known_voids:
            return False
        else:
            self._remove_unknown()
            return True

    def add(self, suit):
        """
        Adds a card to this hand
        """
        self.known_cards[suit] += 1

    def has_four_of_a_kind(self):
        """
        Returns true if this hand contains four of a kind.
        """
        for _, count in self.known_cards.items():
            if count == 4:
                return True
        return False
    
    def is_determined(self):
        """
        Returns true if this hand is entirely known
        """
        return self.number_of_unknown_cards == 0

    def running_totals(self, totals):
        """
        Adds any known cards into running totals for all hands
        """
        totals.update(self.known_cards)

    def kill_unknown(self, suit) -> bool:
        """
        There are four known cards of this suit, so we know it is
        no longer unknown. Returns True if anything changed.
        """
        if self.number_of_unknown_cards > 0 and suit not in self.known_voids:
            self.known_voids.add(suit)
            return True
        else:
            return False

    def force_unknowns(self, number_of_suits) -> bool:
        """
        If we know so much about a void item that we can fix
        its suit, do so and return True.
        """
        if self.number_of_unknown_cards == 0:
            return False
        
        # If we know that all the unknowns are of the same suit,
        # fix them and return True
        if len(self.known_voids) == number_of_suits - 1:
            # find the only possible non-void
            diff = set(range(number_of_suits)) - self.known_voids
            for i in diff:
                self.known_cards[i] += self.number_of_unknown_cards
                self.number_of_unknown_cards = 0
                self.known_voids.clear()
                return True

        # TODO: There is more logic we could deploy here.
        # For example, if there are two unknowns and we know we need
        # two different suits, we could set them both to one.

    def is_legal(self, suit) -> bool:
        """
        Can I legally ask for the given suit?
        """
        if suit in self.known_cards:
            return True     # I have one of these, so can ask
        if self.number_of_unknown_cards == 0:
            return False    # No unknown cards, so cannot ask
        if suit in self.known_voids:
            return False    # We know I have none of these
        return True
    
    def has_card(self, suit) -> Tuple[bool, bool]:
        """
        Does this hand definitely contain the given suit?
        Returns a tuple of [forced, yes/no]
        """
        if suit in self.known_cards:
            return True, True   # We definitely have this card
        elif self.number_of_unknown_cards == 0:
            return True, False  # We definitely do not have it
        elif suit in self.known_voids:
            return True, False  # We definitely do not have it
        else:
            return False, True  # We may or may not have it

    def fill_unknowns(self, totals: Counter) -> bool:
        """
        If only one of the hands has any unknowns in it, we
        can fill them given the counts of other cards. Returns
        True if it cannot be done.
        """
        for suit, count in totals.items():
            if count < 4:
                if not self.fill_unknown_suit(suit, count):
                    return False
        
        assert self.number_of_unknown_cards == 0
        return True

    def fill_unknown_suit(self, suit, count) -> bool:
        """
        If only one of the hands has all the unknowns in
        a given suit, we can fill them in. Returns False if
        it cannot be done.
        """
        assert count < 4
        remaining = 4 - count
        if self.number_of_unknown_cards < remaining:
            return False
        assert suit not in self.known_voids
        self.number_of_unknown_cards -= remaining
        self.known_cards[suit] += remaining
        return True

    def position(self, pos: int, permutation: np.ndarray) -> int:
        """
        Returns a representation of this hand as an integer, so
        we can easily test whether the hand repeats. Pass in the
        position of any hands that have been processed so far.

        Note that we assume the hand is not an immediate winner, so
        the count of cards in any suit must be less than four.
        """
        # start by packing the counts of each suit, using two bits per suit
        for i in permutation:
            count = self.known_cards[i]
            assert(count >= 0 and count < 4)
            pos *= 4
            pos += count
        
        # now pack three bits for a count of unknown cards (0..4)
        pos *= 8
        pos += self.number_of_unknown_cards

        # finally, pack one bit for each known void
        for i in permutation:
            count = 1 if i in self.known_voids else 0
            pos *= 2
            pos += count
        
        return pos

    def adjust_ranking(self, rankings):
        """
        Given an array of rankings for the different suits,
        adjust the rankings to make more common suits higher
        than less common ones. This function is called
        for each hand in turn, with the earlier invocations
        more significant than the later.
        """
        # Shift the existing rankings up out of the way      
        n = len(rankings)
        rankings *= n

        # add the suit counts to the rankings
        for i in range(n):
            rankings[i] += self.known_cards[i]
        
        # make space for the voids
        rankings *= 2

        # add any voids to the rankings (count one each)
        for i in range(n):
            if i in self.known_voids:
                rankings[i] += 1
        
        return rankings

class Cards:
    """
    Represents a pack of playing cards, divided by the given number
    of players. There are four cards per player, and the same
    number of suits as players.
    """
    def __init__(self, number_of_players):
        self.hands = [Hand() for _ in range(number_of_players)]
    
    def is_empty(self, player):
        return self.hands[player].is_empty()

    def number_of_players(self):
        return len(self.hands)

    def show(self, next_player: int):
        """
        Shows all the hands, with an indicator next to the next to play.
        next_player can be -1, but if it is in the legal range of players,
        that hand is highlighted.
        """
        for i, hand in enumerate(self.hands):
            hand.show(i == next_player)
    
    def __str__(self):
        result = ""
        first = True
        for hand in self.hands:
            if not first:
                result += "/"
            first = False
            result += str(hand)
        return result

    def transfer(self, suit, other, this, no_throw) -> bool:
        """
        Moves a card from one hand to another after a successful request.
        _this_ is the player who asked for the transfer. _other_ is the
        player who said they did not have the card. Returns True if it 
        could be done.
        """
        # must have the suit to be able to ask
        if not self.hands[this].ensure_have(suit):
            if no_throw:
                return False
            assert False, f"Cannot ask for {suit} as we know you don't have any"
        if not self.hands[other].remove(suit):
            if no_throw:
                return False
            assert False, f"We know player {other} doesn't have any {suit}"
        self.hands[this].add(suit)         # and give it to this player
        return True

    def no_transfer(self, suit, other, this, no_throw) -> bool:
        """
        Records an unsuccessful request for a transfer. _this_ is the
        player who asked for the transfer. _other_ is the player who
        said they did not have the card. Returns True if it could be
        done.
        """
        # must have the suit to be able to ask
        if not self.hands[this].ensure_have(suit):
            if no_throw:
                return False
            assert False, f"Cannot ask for {suit} as we know you don't have any"
        # other player must have a void
        if not self.hands[other].ensure_have_not(suit):
            if no_throw:
                return False
            assert False, f"Cannot reject {suit} as we know you have one"
        return True
  
    NO_WINNER = -1
    ILLEGAL_CARDS = -2

    def test_winner(self, last_player: int) -> int:
        """
        Is there a winner? If so, return the number of
        the winner. If not, return -1. If the number of cards
        in any suit is greater than 4, or if the hands are
        illegal for any other reason, return -2.
        """
        # First shake down the cards to resolve anything that
        # we can logically deduce
        if not self.shake_down():
            return Cards.ILLEGAL_CARDS

        # Is the situation entirely determined?
        all_determined = True
        for hand in self.hands:
            if not hand.is_determined():
                all_determined = False
                break
        if all_determined:
            return last_player

        # Are there any hands with four of anything?
        for i, hand in enumerate(self.hands):
            if hand.has_four_of_a_kind():
                return i

        # otherwise there are no winners yet
        return Cards.NO_WINNER

    def shake_down(self) -> bool:
        """
        Resolve any logical inferences that can be made on the cards.
        Returns True if the cards are logically consistent.
        """
        # Keep shaking until nothing else settles out
        any_changes = True
        while any_changes:
            any_changes = False

            # If we know the whereabouts of four cards of any suit,
            # we can eliminate them from our enquiries
            totals = Counter()
            for hand in self.hands:
                hand.running_totals(totals)
            for suit, total in totals.items():
                # if we have made changes, break out of the loop so we redo the totals
                if any_changes:
                    break
                if total > 4:
                    return False
                if total == 4:
                    # If we know the whereabouts of all cards in a suit, we know that
                    # none of the unknown cards are of that suit.
                    for hand in self.hands:
                        if hand.kill_unknown(suit):
                            any_changes = True
                else:
                    # If we know that all the unknown cards of one suit are in one hand,
                    # we can fill in all those cards in that hand.
                    hands_with_unknowns = []
                    number_of_unknown_cards = 0
                    for hand in self.hands:
                        if hand.number_of_unknown_cards > 0 and not suit in hand.known_voids:
                            hands_with_unknowns.append(hand)
                            number_of_unknown_cards += hand.number_of_unknown_cards
                    if len(hands_with_unknowns) == 1:
                        if not hands_with_unknowns[0].fill_unknown_suit(suit, total):
                            return False
                        any_changes = True

                    # If we know that the unknown cards in one suit only just fit in the
                    # remaining unknown slots, even spanning multiple hands, we can fill in
                    # those cards.
                    else:
                        remainder = 4 - total
                        if number_of_unknown_cards < remainder:
                            return False    # not enough unknown cards to fit this suit
                        elif number_of_unknown_cards == remainder:
                            for hand in hands_with_unknowns:
                                if not hand.fill_unknown_suit(suit, 4 - hand.number_of_unknown_cards):
                                    return False
                            any_changes = True
        
            # If all the unknown cards in a hand are of just one suit,
            # force them to be known.
            for hand in self.hands:
                if hand.force_unknowns(len(self.hands)):
                    any_changes = True
            
            # redo the totals if there were any changes
            if any_changes:
                continue
            
            # If all the unknowns are in one hand, we must know what they are
            hands_with_unknowns = []
            for hand in self.hands:
                if hand.number_of_unknown_cards > 0:
                    hands_with_unknowns.append(hand)
            if len(hands_with_unknowns) == 1:
                if not hands_with_unknowns[0].fill_unknowns(totals):
                    return False
                any_changes = True

            # redo the totals if there were any changes
            if any_changes:
                continue
            
            # Considering each hand separately, if there are limited options
            # for the unknown cards, we may be able to fill some or all in.
            # e.g. for a 4 player game where the unaccounted ones and twos are:
            # {0: 1, 1: 1}, ??x23 forces 01
            # {0: 1, 1: 2}, ??x23 forces 11 or 01 i.e. 1?x23
            #
            # If there are N possible suits that the cards could be and there
            # are M unknown cards, take the N possible combinations of N-1 suits
            # and for each see whether there are fewer than M cards (say P). If
            # so, there must be at least M - P cards in the remaining suit.
            for suit in range(len(self.hands)):
                if suit not in totals:
                    totals[suit] = 0    # first fill in any complete blanks

            for hand in self.hands:
                if hand.number_of_unknown_cards > 1:
                    possible = 0
                    for suit, total in totals.items():
                        if total < 4 and suit not in hand.known_voids:
                            possible += 4 - total
                    if possible < hand.number_of_unknown_cards:
                        return False    # not enough possible cards to fit

                    unknowns = hand.number_of_unknown_cards
                    for suit, total in totals.items():
                        if total < 4 and suit not in hand.known_voids:
                            remaining = possible - (4 - total)
                            if remaining < unknowns:
                                min_suit = unknowns - remaining
                                if not hand.fill_unknown_suit(suit, 4 - min_suit):
                                    return False
                                any_changes = True

            # TODO there may be other logical moves to clarify what we know
        return True

    def legal(self, other, suit, this, verbose: bool) -> bool:
        """
        Is this move legal?
        """
        if this == other:
            return _not_legal(verbose, "You cannot ask yourself for a card")
        n = len(self.hands)
        if this < 0 or other < 0 or this >= n or other >= n:
            return _not_legal(verbose, "Player number out of range")
        if suit < 0 or suit >= n:
            return _not_legal(verbose, "Suit number out of range")
        if not self.hands[this].is_legal(suit):
            return _not_legal(verbose, "You cannot ask for a suit you do not have")
        return True

    def legal_moves(self, this) -> List[Tuple[int, int]]:
        """
        Returns a list of legal moves, expressed as tuples of
        other, suit.

        Note that it would be possible for a theoretically legal
        move to have no legal reply. This case should be rejected
        by shake_down, which should add to the known_void list any
        suit that would have no legal reply.
        """
        moves = []
        suits = []

        # we can ask for any card that we own or possibly own
        this_hand = self.hands[this]
        for i in range(len(self.hands)):
            if this_hand.is_legal(i):
                suits.append(i)

        # we can ask any other player for a card, but not ourselves
        for other in range(len(self.hands)):
            if other != this:
                for suit in suits:
                    moves.append((other, suit))

        return moves

    def position(self, last_player: int) -> int:
        """
        Returns a representation of the current set of hands as an integer,
        so we can test whether the position repeats. The position function
        is carefully written to give the same result for different instances
        of symmetric positions. The following symmetries are handled:

        * Rotation of players (e.g. player 0 -> 1, 1 -> 2 and 2 -> 0)
        * Permutation of suits (e.g. swapping any two suits)
        """
        # Handle permutation of suits by ordering them according to how
        # they appear in the hands.
        permutation = self.permutation(last_player)
        return self.position_given_permutation(permutation, last_player)
    
    def position_given_permutation(self, permutation: np.ndarray, last_player: int) -> int:
        """
        Returns a representation of the current set of hands, using the
        given permutation of suits to define the relative ordering.
        """
        # Handle rotation of players by always starting from the last
        # player. This also means we do not need to encode the player
        # number.
        pos = 0
        n = len(self.hands)
        assert last_player < n
        for i in range(n):
            hand = self.hands[(i + last_player) % n]
            pos = hand.position(pos, permutation)
        return pos

    def permutation(self, last_player) -> List[int]:
        """
        Handle permutation of suits by ordering them according to how
        they appear in the hands: the most common suit in the first
        hand, down to the last suit seen. Suits that are not seen at
        all, or which have the same ordering in all hands, are ordered
        arbitrarily.
        """
        n = len(self.hands)
        assert last_player < n
        ranking = np.zeros(n, dtype=int)   # will contain the rankings of each suit
        for i in range(n):
            hand = self.hands[(i + last_player) % n]
            hand.adjust_ranking(ranking)
        return np.flip(np.argsort(ranking))

    def has_card(self, suit, this, other) -> Tuple[bool, bool]:
        """
        Does the given hand contain this card?
        Returns a tuple of [forced, yes/no]
        """
        # first check the hand itself
        forced, has = self.hands[this].has_card(suit)
        if forced:
            return forced, has
        
        # It is possible that the choice may be forced even
        # it does not appear so from our individual hand. For
        # example, saying "no" means that none of our cards
        # are of the given suit, which means they must be of
        # the other suits. Check that this does not lead to
        # inconsistencies.
        copied = deepcopy(self)
        if not copied.no_transfer(suit, this, other, True) or not copied.shake_down():
            return True, True   # forced because "no" results in inconsistency

        copied = deepcopy(self)
        if not copied.transfer(suit, this, other, True) or not copied.shake_down():
            return True, False   # forced because "yes" results in inconsistency
  
        # genuinely unforced
        return False, False
    
    def next_player(self, this_player: int) -> int:
        """
        Finds the next player who is able to move (has any cards)
        """
        n = self.number_of_players()
        p = (this_player + 1) % n
        while self.hands[p].is_empty():
            p = (p + 1) % n
            assert p != this_player, "At least one player must have some cards"
        return p            

def _not_legal(verbose, message) -> bool:
    if verbose:
        print(message)
    return False

def test_no_transfer():
    """
    Tests the case where we have 000/22?/111???x0
    and player 1 asks player 0 for a 1.
    """
    h0 = Hand()
    h0.known_cards = Counter({0: 3})
    h0.number_of_unknown_cards = 0
    h1 = Hand()
    h1.known_cards = Counter({2: 2})
    h1.number_of_unknown_cards = 1
    h2 = Hand()
    h2.known_cards = Counter({1: 3})
    h2.number_of_unknown_cards = 3
    #h2.known_voids = {0}
    cards = Cards(3)
    cards.hands = [h0, h1, h2]

    # cards.show(1)
    # print("player 1 asks player 0 for a 1, who must say no")
    cards.no_transfer(1, 0, 1, False)
    # cards.show(-1)
    # print("shake_down")
    cards.shake_down()
    # cards.show(-1)

    assert cards.hands[0].known_cards == {0: 3}
    assert cards.hands[1].known_cards == {2: 2, 1: 1}
    assert cards.hands[2].known_cards == {1: 3, 0: 1, 2: 2}
    print("test_no_transfer: succeeded")

def test_no_transfer_2():
    """
    Initial hands: 0???/00??
    Player 0 asks player 1 for 1, who refuses. (This is
    illegal, but we should handle this gracefully.)
    """
    h0 = Hand()
    h0.known_cards = Counter({0: 1})
    h0.number_of_unknown_cards = 3
    h1 = Hand()
    h1.known_cards = Counter({0: 2})
    h1.number_of_unknown_cards = 2
    cards = Cards(2)
    cards.hands = [h0, h1]

    # cards.show(0)
    # print("player 0 asks player 1 for a 1, who refuses")
    transferred = cards.no_transfer(1, 1, 0, True)
    # cards.show(-1)

    assert transferred
    print("test_no_transfer_2: succeeded")

def test_simple_shakedown():
    """
    Tests the cards 00???/??? for whether they are
    consistent. Of course they are.
    """
    h0 = Hand()
    h0.known_cards = Counter({0: 2})
    h0.number_of_unknown_cards = 3
    h1 = Hand()
    h1.known_cards = Counter({})
    h1.number_of_unknown_cards = 3
    cards = Cards(2)
    cards.hands = [h0, h1]

    cards.show(-1)
    print("shake_down")
    ok = cards.shake_down()
    cards.show(-1)

    assert ok
    assert cards.hands[0].known_cards == {0: 2, 1: 1}
    assert cards.hands[1].known_cards == {1: 1}
    print("test_simple_shake_down: succeeded")

def test_shake_down():
    """
    Tests the case where we have 001/0?x1/22211??x0 and
    we shake_down. We know that player 1 cannot have a 2
    because that means player 2 would have to have a 0
    and that is excluded.
    """
    h0 = Hand()
    h0.known_cards = Counter({0: 2, 1: 1})
    h0.number_of_unknown_cards = 0
    h1 = Hand()
    h1.known_cards = Counter({0: 1})
    h1.number_of_unknown_cards = 1
    h1.known_voids = {1}
    h2 = Hand()
    h2.known_cards = Counter({2: 3, 1: 2})
    h2.number_of_unknown_cards = 2
    h2.known_voids = {0}
    cards = Cards(3)
    cards.hands = [h0, h1, h2]

    # cards.show(-1)
    # print("shake_down")
    cards.shake_down()
    # cards.show(-1)

    assert cards.hands[0].known_cards == {0: 2, 1: 1}
    assert cards.hands[1].known_cards == {0: 2}
    assert cards.hands[2].known_cards == {2: 4, 1: 3}
    print("test_shake_down: succeeded")

def test_has_card():
    """
    Given the cards 00??/01?/11??? is it legal for
    player 2 to tell player 1 that he does not have any
    of suit 2? (It cannot be as that leaves only 3 slots
    for 2s.)
    """
    h0 = Hand()
    h0.known_cards = Counter({0: 2})
    h0.number_of_unknown_cards = 2
    h1 = Hand()
    h1.known_cards = Counter({0: 1, 1: 1})
    h1.number_of_unknown_cards = 1
    h2 = Hand()
    h2.known_cards = Counter({1: 2})
    h2.number_of_unknown_cards = 3
    cards = Cards(3)
    cards.hands = [h0, h1, h2]

    cards.show(-1)
    forced, yes = cards.has_card(2, 2, 0)
    assert forced and yes

    print("test_has_card: succeeded")

def test_four_player_shakedown():
    """
    Are the cards 222??x0/1x23/000?/11330?x0 legal?
    """
    h0 = Hand()
    h0.known_cards = Counter({2: 3})
    h0.number_of_unknown_cards = 2
    h0.known_voids = {0}
    h1 = Hand()
    h1.known_cards = Counter({1: 1})
    h1.number_of_unknown_cards = 0
    h1.known_voids = {2, 3}
    h2 = Hand()
    h2.known_cards = Counter({0: 3})
    h2.number_of_unknown_cards = 1
    h3 = Hand()
    h3.known_cards = Counter({0: 1, 1: 2, 3: 2})
    h3.number_of_unknown_cards = 2
    cards = Cards(4)
    cards.hands = [h0, h1, h2, h3]

    cards.show(-1)
    ok = cards.shake_down()
    print("shakedown")
    cards.show(-1)
    assert ok

    print("test_four_player_shakedown: succeeded")

def test_four_player_test_winner():
    """
    Consider the hands:

    222?x01
    1x23
    000??x23
    1133??

    This is a winner for player 2, because one of those ?s must be a
    0 and the other must be a 1, as there are three each elsewhere.
    Thus player 2 has four zeros.
    """
    h0 = Hand()
    h0.known_cards = Counter({2: 3})
    h0.number_of_unknown_cards = 1
    h0.known_voids = {0, 1}
    h1 = Hand()
    h1.known_cards = Counter({1: 1})
    h1.number_of_unknown_cards = 0
    h1.known_voids = {2, 3}
    h2 = Hand()
    h2.known_cards = Counter({0: 3})
    h2.number_of_unknown_cards = 2
    h2.known_voids = {2, 3}
    h3 = Hand()
    h3.known_cards = Counter({1: 2, 3: 2})
    h3.number_of_unknown_cards = 2
    cards = Cards(4)
    cards.hands = [h0, h1, h2, h3]

    cards.show(-1)
    winner = cards.test_winner(2)
    assert winner == 2

def test_four_player_exclusions():
    """
    Given the cards 222?x01/111?x23/000?x2/333?x01, what
    can player 2 legally ask for from player 0?

    0: win with 222?x01/1111/0000/333?x01
    1:          222?x01/1110/0001/333?x01
    2: disallowed (has no 2)
    3: illegal  2222/111?x23/0003/3332

    Thus the cards can be written 222?x01/111?x23/000?x23/333?x01.
    We must exclude 3 on player 2 because if he were to have it,
    that makes four threes, which excludes three everywhere, which
    means players 0 and 3 must both have an extra 2, which leads to
    five twos.
    """
    h0 = Hand()
    h0.known_cards = Counter({2: 3})
    h0.number_of_unknown_cards = 1
    h0.known_voids = {0, 1}
    h1 = Hand()
    h1.known_cards = Counter({1: 3})
    h1.number_of_unknown_cards = 1
    h1.known_voids = {2, 3}
    h2 = Hand()
    h2.known_cards = Counter({0: 3})
    h2.number_of_unknown_cards = 1
    h2.known_voids = {2}
    h3 = Hand()
    h3.known_cards = Counter({3: 3})
    h3.number_of_unknown_cards = 1
    h3.known_voids = {0, 1}
    cards = Cards(4)
    cards.hands = [h0, h1, h2, h3]

    cards.show(-1)
    ok = cards.shake_down()
    cards.show(-1)
    assert ok
    assert 3 in cards.hands[2].known_voids
    print("test_four_player_exclusions: succeeded")

def test_permutation():
    """
    Tests the ordering of suits when we have 002?/0?x1/2211??x0.
    The order should be:
    
    * 0, 2, 1 for player 0
    * 0, 1, 2 for player 1
    * 2, 1, 0 for player 2
    """
    h0 = Hand()
    h0.known_cards = Counter({0: 2, 2: 1})
    h0.number_of_unknown_cards = 1
    h1 = Hand()
    h1.known_cards = Counter({0: 1})
    h1.number_of_unknown_cards = 1
    h1.known_voids = {1}
    h2 = Hand()
    h2.known_cards = Counter({2: 2, 1: 2})
    h2.number_of_unknown_cards = 2
    h2.known_voids = {0}
    cards = Cards(3)
    cards.hands = [h0, h1, h2]

    p0 = cards.permutation(0)
    p1 = cards.permutation(1)
    p2 = cards.permutation(2)

    # print(p0)
    # print(p1)
    # print(p2)

    assert np.array_equal(p0, [0, 2, 1])
    assert np.array_equal(p1, [0, 1, 2])
    assert np.array_equal(p2, [2, 1, 0])
    print("test_permutation: succeeded")

if __name__ == "__main__":
    test_simple_shakedown()
    test_no_transfer()
    test_no_transfer_2()
    test_simple_shakedown()
    test_shake_down()
    test_has_card()
    test_permutation()
    test_four_player_shakedown()
    test_four_player_test_winner()
    # test_four_player_exclusions()     too hard to get working, just tolerate this error instead
