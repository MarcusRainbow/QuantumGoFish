from cards import Cards
from random import seed

def play(players) -> int:
    """
    Plays the game with the given list of players until one
    player wins or there is a draw. If a player wins, the
    function returns the number of the player (0 to one less
    than the number of players). If there is a draw, the function
    returns -1.
    """
    number_of_players = len(players)
    cards = Cards(number_of_players)
    history = set()
    while True:
        for i, p in enumerate(players):
            cards.show(i)
            if cards.is_empty(i):
                print(f"Player {i} must skip as they have no cards")
                continue

            other, suit = p.next_move(i, cards, history)
            print(f"Player {i} requests suit {suit} from player {other}")
            if players[other].has_card(other, i, suit, cards, history):
                print(f"Player {other} hands card {suit} to player {i}")
                cards.transfer(suit, other, i, False)
            else:
                print(f"Player {other} has no cards of suit {suit}")
                cards.no_transfer(suit, other, i, False)
            winner = cards.test_winner(i)
            if winner >= 0:
                cards.show(-1)
                return winner

            # if a position repeats, it forces a draw
            position = cards.position(i)
            if position in history:
                return -1
            history.add(position)
