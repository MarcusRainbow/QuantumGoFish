# QuantumGoFish
Quantum go fish is a card game generally played without cards. There is a detailed discussion of the game at https://stacky.net/wiki/index.php?title=Quantum_Go_Fish.

## Extra Rules
I had to add some extra rules to make it possible to play the game.

* If a position repeats itself (i.e. the same cards and the same player to move), the game is declared a draw. Otherwise it is possible for a game to go on for ever, with players just swapping the same cards.
* If a player has no cards at all, they skip their go. (Clearly, if all the players but one have no cards, then the game has already ended.)
* If the game ends with multiple players all having 4 cards of a single suit, but not all the cards known (this can only happen in games with four or more players), there is just one winner. The winner is the current player, if he has 4 cards of a single suit, or failing that the player next to play who has 4 cards of a single suit. He wins immediately, rather than having to wait for his turn
* Each player must most want themselves to win, followed by a draw. If however neither of these is possible, the players must declare up front their order of preference of the other players. (If this is unknown, or can change dynamically, it makes the game extremely difficult, maybe impossible, to analyse.)

