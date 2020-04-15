use cards::{Cards, NO_WINNER, ILLEGAL_CARDS};
use player::Player;
use std::collections::HashSet;

/** 
    Plays the game with the given list of players until one
    player wins or there is a draw. If a player wins, the
    function returns the number of the player (0 to one less
    than the number of players). If there is a draw, the function
    returns -1.
*/
pub fn play(players: &[usize], player_instances: &mut [Box<Player>]) -> i64 {
    let number_of_players = players.len();
    assert!(player_instances.len() <= number_of_players);

    let mut cards = Cards::new(number_of_players);
    let mut history = HashSet::new();

    loop {
        for i in 0..number_of_players {
            cards.show(i);
            if cards.is_empty(i) {
                println!("Player {} must skip as they have no cards", i);
                continue;
            }
            let (other, suit) = player_instances[players[i]].next_move(i, &cards, &history);
            println!("Player {} requests suit {} from player {}", i, suit, other);
            if player_instances[players[other]].has_card(other, i, suit, &cards, &history) {
                println!("Player {} hands card {} to player {}", suit, other, i);
                cards.transfer(suit, other, i, false);
            } else {
                println!("Player {} has no cards of suit {}", other, suit);
                cards.no_transfer(suit, other, i, false);
            }
            let winner = cards.test_winner(i);
            if winner == ILLEGAL_CARDS {
                cards.show(usize::max_value());
                panic!("The cards are in an illegal state. All players lose");
            }
            if winner != NO_WINNER {
                cards.show(usize::max_value());
                return winner
            }
            let position = cards.position(i);
            if history.contains(&position) {
                cards.show(usize::max_value());
                return -1
            }
            history.insert(position);
        }
    }
}

