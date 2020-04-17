use std::collections::{HashMap, HashSet};
use std::io;
use std::io::BufRead;
use std::io::Write;
use std::cmp::min;
use cards::{Cards, ILLEGAL_CARDS, NO_WINNER};

/** 
    Interface that defines how players interact
*/
pub trait Player {
    /** 
        This player must ask one other player for a card of
        a given suit. Returns other_player, suit.
    */
    fn next_move(&mut self, this: usize, cards: &Cards, history: &HashSet<i128>) -> (usize, i8);
    /** 
        Returns true if the player has this card.
    */
    fn has_card(&mut self, this: usize, other: usize, suit: i8, cards: &Cards, history: &HashSet<i128>) -> bool;

    /**
        Returns information about this object
     */
    fn info(&self) -> String;
}

/** 
    Implementation of Player that wraps around user input.
*/
pub struct HumanPlayer {
}

impl HumanPlayer {
    pub fn new() -> HumanPlayer {
        HumanPlayer {}
    }

    pub fn ask_for(msg: &str, this: usize) -> String {
        println!("{}> {}", this, msg);
        let input = io::stdin();
        return input.lock().lines().next().expect("no input").expect("failed input");
    }
}

impl Player for HumanPlayer {
    fn next_move(&mut self, this: usize, cards: &Cards, _history: &HashSet<i128>) -> (usize, i8) {
        loop {
            let other_input = Self::ask_for("Which player would you like to ask? ", this);
            let suit_input = Self::ask_for("Which suit would you like to ask for? ", this);
            if other_input == "q" || other_input == "Q" || suit_input == "q" || suit_input == "Q" {
                panic!("Quit");
            }
            let other = usize::from_str_radix(&other_input, 10).unwrap_or(usize::max_value());
            let suit = i8::from_str_radix(&suit_input, 10).unwrap_or(-1);
            if cards.legal(other, suit, this, true) {
                return (other, suit);
            }
            println!("Player and suit must both be integers (q to exit)");
        }
    }

    /** 
        If we have definitely have or do not have the card, we
        do not ask the user. Otherwise we must ask
    */
    fn has_card(&mut self, this: usize, other: usize, suit: i8, cards: &Cards, _history: & HashSet<i128>) -> bool {
        let (forced, has) = cards.has_card(suit, this, other);
        if forced {
            return has;
        }

        loop {
            let reply = Self::ask_for(&format!("Do you have a card of suit {}?", suit), this);
            if reply == "Y" || reply == "y" {
                return true;
            } else {
                if reply == "N" || reply == "n" {
                    return false;
                }
            }
            println!("Y or N");
        }
    }
    fn info(&self) -> String {
        "no info".to_string()
    }
}

/** 
    Implementation of Player that looks ahead, playing the best move
    available.
*/
pub struct CleverPlayer {
    max_depth: i64,
    max_has_depth: i64,
    progress: i64,
    current_progress: i64,
    preferences: Vec<Vec<usize>>,
    symmetric: bool,
    _cached_moves: HashMap<i128, (i8, i8, i8)>,
}

impl CleverPlayer {
    /** 
        The max_depth specifies how far ahead the player will look
        before making a move. For example, zero means only consider
        the immediate move, so don't play into an immediate lose.

        The max_has_depth specifies how far ahead the player will look
        before saying whether they have a card. For example, zero means
        only worry about the immediate effect.

        If preferences is specified, it states who the each of the 
        players wants to win. It is a list of lists of player numbers.

        If other_player is supplied, we share its cache.
    */
    pub fn new(
        max_depth: i64, 
        max_has_depth: i64,
        progress: i64, 
        preferences: Vec<Vec<usize>>, 
        symmetric: bool) -> CleverPlayer {

        CleverPlayer {
            max_depth: max_depth,
            max_has_depth: max_has_depth,
            progress: progress,
            current_progress: 0,
            preferences: preferences,
            symmetric: symmetric,
            _cached_moves: HashMap::new(),
        }
    }

    /** 
        Like next_move, but it also returns a result, which says what 
        the final best-case result is as a result of this move.

        Returns a tuple of (other_player, suit, result, draw_position)
    */
    pub fn _evaluate_move(&mut self, this: usize, cards: &Cards, history: & HashSet<i128>, depth: i64)
            -> (usize, i8, i64, i128) {
        let permutation = cards.permutation(this);
        let pos = cards.position_given_permutation(&permutation, this, self.symmetric);
        let n = permutation.len();
        match self._cached_moves.get(&pos) {
            Some(&(other_c, suit_c, result_c)) => {
                let other = (other_c as usize + this) % n;
                let result = if result_c < 0 { result_c as i64 } else { ((result_c as usize + this) % n) as i64 };
                let suit = permutation[suit_c as usize];
                return (other, suit, result, -1)
            }
            None => {
                let (other, suit, result, draw_position) 
                    = self._evaluate_move_uncached(this, cards, history, depth, &permutation);

                if self.progress > 0 {
                    self.current_progress += 1;
                    if self.current_progress == self.progress {
                        self.current_progress = 0;
                        print!(".");
                        io::stdout().flush().unwrap();
                    }
                }
                let other_c = (n + other - this) % n;
                let result_c = if result < 0 { result } else { ((n + result as usize - this) % n) as i64 };
                let found = permutation.iter().position(|&x| x == suit);
                let suit_c = found.unwrap();
                if result_c >= 0 || !history.contains(&draw_position) {
                    self._cached_moves.insert(pos, (other_c as i8, suit_c as i8, result_c as i8));
                }
                return (other, suit, result, draw_position);
    
            }
        }
    }

    /** 
        Like _evaluate_move, but not using the cache.
    */
    pub fn _evaluate_move_uncached(&mut self, this: usize, cards: &Cards, history: & HashSet<i128>, depth: i64, permutation: &[i8]) 
            -> (usize, i8, i64, i128) {
        let mut other_winners = vec![];
        let legal_moves = cards.legal_moves_given_permutation(this, permutation);
        assert!(legal_moves.len() > 0);
        let mut draw = None;
        let mut out_of_depth = None;
        let mut lose = None;
        let mut immediate_lose = None;
        if !self.preferences.is_empty() {
            let p = &self.preferences[this];
            other_winners = vec![None; p.len()];
        }
        for &(other, suit) in &legal_moves {
            let mut copy_cards = cards.clone();
            let has = self._evaluate_has_card(other, this, suit, &copy_cards, history, depth - 1);
            if has {
                copy_cards.transfer(suit, other, this, false);
            } else {
                copy_cards.no_transfer(suit, other, this, false);
            }
            let winner = copy_cards.test_winner(this);
            if winner == ILLEGAL_CARDS {
                println!("WARNING: illegal cards after move has={} suit={} other={} this={} moves={:?}", has, suit, other, this, legal_moves);
                cards.show(this);
                println!("-------------");
                continue;
            }
            if winner == this as i64 {
                return (other, suit, winner, -1);
            }
            if winner != NO_WINNER {
                if !self.preferences.is_empty() {
                    let p = &self.preferences[this];
                    if let Some(f) = p.iter().position(|&x| x == winner as usize) {
                        other_winners[f] =  Some((other, suit, winner, -1));
                    } else {
                        immediate_lose = Some((other, suit, winner, -1));
                    } 
                } else {
                    immediate_lose = Some((other, suit, winner, -1));
                }
                continue;
            }
            if depth == 0 {
                out_of_depth = Some((other, suit, -1, -1));
                continue;
            }
            let next_player = copy_cards.next_player(this);
            let position = copy_cards.position(next_player);
            if history.contains(&position) {
                draw = Some((other, suit, -1, position));
                continue;
            }
            let mut copy_history = history.clone();
            copy_history.insert(position);
            let (_, _, next_winner, draw_position)
                = self._evaluate_move(next_player, &copy_cards, &mut copy_history, depth - 1);
            if next_winner == this as i64 {
                return (other, suit, next_winner, -1);
            }
            if next_winner < 0 {
                draw = Some((other, suit, -1, draw_position));
            } else if !self.preferences.is_empty() {
                let p = &self.preferences[this];
                if let Some(f) = p.iter().position(|&x| x == next_winner as usize) {
                    other_winners[f] = Some((other, suit, next_winner, 0));
                } else {
                    lose = Some((other, suit, next_winner, -1));
                }
            } else {
                lose = Some((other, suit, next_winner, -1));
            }
        }
        if let Some(result) = draw {
            return result;
        }
        if let Some(result) = out_of_depth {
            return result;
        }
        for other_winner in other_winners {
            if let Some(result) = other_winner {
                return result;
            }
        }
        if let Some(result) = lose {
            return result;
        }
        if let Some(result) = immediate_lose {
            return result;
        }
        panic!("should never get here")
    }

    fn _evaluate_has_card(&mut self, this: usize, other: usize, suit: i8, cards: &Cards, history: & HashSet<i128>, given_depth: i64) -> bool {
        let (forced, has) = cards.has_card(suit, this, other);
        if forced {
            return has;
        }
        let mut copy_cards = cards.clone();
        copy_cards.transfer(suit, this, other, false);
        let mut yes_winner = copy_cards.test_winner(other);
        if yes_winner == this as i64 {
            return true;
        }

        let depth = min(given_depth, self.max_has_depth);
        if depth == 0 {
            return yes_winner != NO_WINNER;
        }

        let next_player = copy_cards.next_player(other);
        if yes_winner != NO_WINNER {
            if !self.preferences.is_empty() {
                let p = &self.preferences[this];
                if p.iter().position(|&x| x == yes_winner as usize) != None {
                    return false;
                }
            }
        } else {
            let mut copy_history = history.clone();
            let tmp0 = self._evaluate_move(next_player, &copy_cards, &mut copy_history, depth - 1);
            yes_winner = tmp0.2;
            if yes_winner == this as i64 {
                return true;
            }
        }
        copy_cards = cards.clone();
        copy_cards.no_transfer(suit, this, other, false);
        let mut no_winner = copy_cards.test_winner(other);
        if no_winner == this as i64 {
            return false;
        }
        if no_winner != NO_WINNER {
            if !self.preferences.is_empty() {
                let p = &self.preferences[this];
                if p.iter().position(|&x| x == no_winner as usize) != None {
                    return true;
                }
            }
        } else {
            let mut copy_history = history.clone();
            let tmp2 = self._evaluate_move(next_player, &copy_cards, &mut copy_history, depth - 1);
            no_winner = tmp2.2;
            if no_winner == this as i64 {
                return false;
            }
        }
        if yes_winner < 0 {
            return true;
        }
        if no_winner < 0 {
            return false;
        }
        if !self.preferences.is_empty() {
            let p = &self.preferences[this];
            let yes_preference: i64;
            let no_preference: i64;
            if let Some(f) = p.iter().position(|&x| x == yes_winner as usize) {
                yes_preference = p[f] as i64;
            } else {
                yes_preference = p.len() as i64;
            }
            if let Some(f) = p.iter().position(|&x| x == no_winner as usize) {
                no_preference = p[f] as i64;
            } else {
                no_preference = p.len() as i64;
            }
            if yes_preference < no_preference {
                return true;
            } else if no_preference < yes_preference {
                return false;
            }
        }
        return false;
    }
}

impl Player for CleverPlayer {
    fn next_move(&mut self, this: usize, cards: &Cards, history: & HashSet<i128>) -> (usize, i8) {
        let max_depth = self.max_depth;
        let (other, suit, result, _) = self._evaluate_move(this, cards, history, max_depth);
        println!("Result={}", result);
        return (other, suit);
    }

    fn has_card(&mut self, this: usize, other: usize, suit: i8, cards: &Cards, history: & HashSet<i128>) -> bool {
        let max_has_depth = self.max_has_depth;
        return self._evaluate_has_card(this, other, suit, cards, history, max_has_depth);
    }

    fn info(&self) -> String {
        let len = self._cached_moves.len();
        return format!("cache size: {}", len);
    }
}

#[cfg(test)]
mod tests {
    use super::{CleverPlayer, HumanPlayer, Player};
    use game::play;
    use std::time::Instant;
    
    #[test]
    #[ignore]
    pub fn test_two_human_players() {
        let human: Box<Player> = Box::new(HumanPlayer::new());
        let mut players = vec![human];
        let result = play(&[0, 0], &mut players);
        if result == -1 {
            println!("Result is a draw");
        } else {
            println!("Win for player {}", result);
        }
        assert!(result == -1, "test_two_human_players: expecting a draw");
        println!("----------------");
        println!();
    }

    #[test]
    pub fn test_two_clever_players() {
        let clever: Box<Player> = Box::new(CleverPlayer::new(1000, 1000, 0, vec![], true));
        let mut players = vec![clever];
        let result = play(&[0, 0], &mut players);
        if result == -1 {
            println!("Result is a draw");
        } else {
            println!("Win for player {}", result);
        }
        assert!(result == -1, "test_two_clever_players: expecting a draw");
        println!("{}", players[0].info());
        println!("----------------");
        println!();
    }
    
    #[test]
    pub fn test_three_clever_players() {
        let clever: Box<Player> = Box::new(CleverPlayer::new(1000, 1000, 0, vec![], true));
        let mut players = vec![clever];
        let result = play(&[0, 0, 0], &mut players);
        if result == -1 {
            println!("Result is a draw");
        } else {
            println!("Win for player {}", result);
        }
        println!("{}", players[0].info());
        println!("----------------");
        println!();
    }
    
    pub fn three_biased_players(preferences: Vec<Vec<usize>>, symmetric: bool) -> i64 {
        let result;
        let clever: Box<Player> = Box::new(CleverPlayer::new(1000, 1000, 0, preferences, symmetric));
        let mut players = vec![clever];
        result = play(&[0, 0, 0], &mut players);
        if result == -1 {
            println!("Result is a draw");
        } else {
            println!("Win for player {}", result);
        }
        println!("{}", players[0].info());
        return result;
    }
    
    #[test]
    pub fn test_three_clever_biased_players() {
        let result = three_biased_players(vec![vec![2], vec![0], vec![1]], true);
        assert!(result == -1, "test_three_clever_biased_players: expecting a draw");
        println!("----------------");
        println!();
    }
    
    /** 
        Try all combinations of preferences for the three player game
    */
    #[test]
    pub fn test_three_clever_players_of_all_types() {
        for i0 in vec![1, 2] {
            for i1 in vec![0, 2] {
                for i2 in vec![0, 1] {
                    let preferences = vec![vec![i0], vec![i1], vec![i2]];
                    let symmetric = (i0 == 1 && i1 == 2 && i2 == 0) || (i0 == 2 && i1 == 0 && i2 == 1);
                    let result = three_biased_players(preferences.clone(), symmetric);
                    print!("With second preferences {:?}", preferences);
                    if result == -1 {
                        println!("Result is a draw");
                    } else {
                        println!("Win for player {}", result);
                    }
                }
            }
        }
        println!("----------------");
        println!();
    }
        
    #[test]
    #[ignore]
    pub fn test_four_clever_biased_players() {

        let result;
        let now = Instant::now();
        let clever: Box<Player> = Box::new(CleverPlayer::new(1000, 1000, 2, vec![
            vec![3, 2],
            vec![0, 3],
            vec![1, 0],
            vec![2, 1],
            ], true));
        let mut players = vec![clever];
        result = play(&[0, 0, 0, 0], &mut players);
        if result == -1 {
            println!("Result is a draw");
        } else {
            println!("Win for player {}", result);
        }
        println!("{}", players[0].info());
        println!("time taken {} seconds", now.elapsed().as_secs());
        assert!(result == -1, "test_four_clever_players: expecting a draw");
        println!("----------------");
        println!();
    }
   
    fn test_four_symmetric(prefs: &[usize]) {
        let result;
        let now = Instant::now();

        let n = 4;
        let mut preferences = Vec::new();
        for i in 0..n {
            let mut subprefs = Vec::new();
            for p in prefs {
                let preference = (p + i) % n;
                subprefs.push(preference);
            }
            preferences.push(subprefs);
        }

        let clever: Box<Player> = Box::new(CleverPlayer::new(1000, 1000, 1, preferences, true));
        let mut players = vec![clever];
        result = play(&[0, 0, 0, 0], &mut players);
        if result == -1 {
            println!("Result is a draw");
        } else {
            println!("Win for player {}", result);
        }
        println!("for preferences: {:?}", prefs);
        println!("{}", players[0].info());
        println!("time taken {} seconds", now.elapsed().as_secs());
        // assert!(result == -1, "test_four_symmetric: expecting a draw");
        println!("----------------");
        println!();
    }

    #[test]
    // #[ignore]
    pub fn test_all_four_clever_symmetrically_biased_players() {

        test_four_symmetric(&[1, 2, 3]);
        test_four_symmetric(&[2, 1, 3]);
        test_four_symmetric(&[3, 1, 2]);
        test_four_symmetric(&[1, 3, 2]);
        test_four_symmetric(&[2, 3, 1]);
        test_four_symmetric(&[3, 2, 1]);

        println!("----------------");
        println!();
    }

    #[test]
    #[ignore]
    pub fn test_five_clever_biased_players() {

        let now = Instant::now();
        let clever: Box<Player> = Box::new(CleverPlayer::new(1000, 1000, 2, vec![
            vec![4, 3, 2],
            vec![0, 4, 3],
            vec![1, 0, 4],
            vec![2, 1, 0],
            vec![3, 2, 1],
            ], true));
        let mut players = vec![clever];
        let result = play(&[0, 0, 0, 0, 0], &mut players);
        if result == -1 {
            println!("Result is a draw");
        } else {
            println!("Win for player {}", result);
        }
        // println!("number of entries in cache: {}", clever.cache_size());
        println!("time taken {} seconds", now.elapsed().as_secs());
        assert!(result == -1, "test_five_clever_players: expecting a draw");
        println!("----------------");
        println!();
    }
}