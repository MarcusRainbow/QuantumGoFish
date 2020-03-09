from player import Player, HumanPlayer, RandomPlayer, CleverPlayer
from game import play

if __name__ == "__main__":
    players = [HumanPlayer(), CleverPlayer()]
    result = play(players)
    if result >= 0:
        print(f"Winner was player {result}")
    else:
        print(f"Draw")
