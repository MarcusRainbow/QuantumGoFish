from collections import Counter
from typing import Tuple

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

    def show(self, is_next_player: bool):
        """
        Write to stdout a representation of the hand
        """
        for suit in self.known_cards.elements():
            # TODO: need fancier output if there are more than 10 suits
            print(suit, end='')
        
        for _ in range(self.number_of_unknown_cards):
            print("?", end='')

        if self.known_voids:
            print(" excluding ", end='')
            for kv in self.known_voids:
                print(kv, end='')
        
        if is_next_player:
            print("   <<<< next player")
        else:
            print()

    def ensure_have(self, suit):
        """
        Make sure we have one of these cards. (The player has just
        requested a card from this suit.)
        """

        # easy if we already have one
        if suit in self.known_cards:
            assert(self.known_cards[suit] > 0)
            return
        
        # convert one of the unknowns into one of these
        assert suit not in self.known_voids, f"Cannot ask for {suit} as we know you don't have any"
        self._remove_unknown()
        self.known_cards[suit] = 1

    def _remove_unknown(self):
        assert(self.number_of_unknown_cards > 0)
        self.number_of_unknown_cards -= 1
        if self.number_of_unknown_cards == 0:
            self.known_voids.clear()

    def ensure_have_not(self, suit):
        """
        We know this hand does not contain this suit. For example the player has
        rejected a request for a card.
        """
        assert suit not in self.known_cards, f"Cannot reject {suit} as we know you have one"
        self.known_voids.add(suit)

    def remove(self, suit):
        """
        Take one card of this suit away from the user. If it is a known card, remove that.
        If not, take it from the unknowns.
        """
        if suit in self.known_cards:
            count = self.known_cards[suit]
            if count > 1:
                self.known_cards[suit] = count - 1
            else:
                del self.known_cards[suit]  # avoid empties
        else:
            assert suit not in self.known_voids, f"We know you don't have any {suit}"     
            self._remove_unknown()

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

    def position(self, pos: int, number_of_players: int) -> int:
        """
        Returns a representation of this hand as an integer, so
        we can easily test whether the hand repeats. Pass in the
        position of any hands that have been processed so far.

        Note that we assume the hand is not an immediate winner, so
        the count of cards in any suit must be less than four.
        """
        # start by packing the counts of each suit, using two bits per suit
        for i in range(number_of_players):
            count = self.known_cards[range]
            assert(count >= 0 and count < 4)
            pos *= 4
            pos += count
        
        # now pack three bits for a count of unknown cards (0..4)
        pos *= 8
        pos += self.number_of_unknown_cards

        # finally, pack one bit for each known void
        for i in range(number_of_players):
            count = 1 if i in self.known_voids else 0
            pos *= 2
            pos += count
        
        return count

class Cards:
    """
    Represents a pack of playing cards, divided by the given number
    of players. There are four cards per player, and the same
    number of suits as players.
    """

    def __init__(self, number_of_players):
        self.hands = [Hand() for _ in range(number_of_players)]
    
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
        print()

    def transfer(self, suit, other, this):
        """
        Moves a card from one hand to another after a successful request
        """
        self.hands[this].ensure_have(suit) # must have the suit to be able to ask
        self.hands[other].remove(suit)     # take away one card
        self.hands[this].add(suit)         # and give it to this player

    def no_transfer(self, suit, other, this):
        """
        Records an unsuccessful request for a transfer
        """
        self.hands[this].ensure_have(suit) # must have the suit to be able to ask
        self.hands[other].ensure_have_not(suit)  # other player must have a void

    def test_winner(self, last_player: int):
        """
        Is there a winner? If so, return the number of
        the winner. If not, return -1
        """

        # Keep shaking until nothing settles out
        any_changes = True
        while any_changes:
            any_changes = False

            # If we know the whereabouts of four cards of any suit,
            # we can eliminate them from our enquiries
            totals = Counter()
            for hand in self.hands:
                hand.running_totals(totals)
            for suit, total in totals.items():
                assert total <= 4, f"We have {total} cards in suit {suit}!"
                if total == 4:
                    for hand in self.hands:
                        if hand.kill_unknown(suit):
                            any_changes = True
        
            # If all the unknown cards in a hand are of just one suit,
            # force them to be known.
            for hand in self.hands:
                if hand.force_unknowns(len(self.hands)):
                    any_changes = True

            # TODO there may be other logical moves to clarify what we know

        # Are there any hands with four of anything?
        for i, hand in enumerate(self.hands):
            if hand.has_four_of_a_kind():
                return i

        # Is the situation entirely determined?
        for hand in self.hands:
            if hand.is_determined():
                return last_player

        # otherwise there are no winners yet
        return -1

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
    
    def position(self) -> int:
        """
        Returns a representation of the current set of hands as an integer,
        so we can test whether the position repeats.
        """
        pos = 0
        number_of_players = len(self.hands)
        for hand in self.hands:
            pos = hand.position(pos, number_of_players)
        return pos

    def has_card(self, suit, this) -> Tuple[bool, bool]:
        """
        Does the given hand contain this card?
        Returns a tuple of [forced, yes/no]
        """
        return self.hands[this].has_card(suit)

def _not_legal(verbose, message) -> bool:
    if verbose:
        print(message)
    return False
