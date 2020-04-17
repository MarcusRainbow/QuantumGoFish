use std::collections::HashSet;
use std::collections::HashMap;
use std::fmt;

/** 
    Represents a single hand of cards. Cards are either of a
    known suit, or are one of a set of possibilities. We
    define the possibilities in terms of what we know they are
    not. For example, if the holder has said they do not have
    a card in a given suit, we record that fact.
*/
#[derive(Clone)]
pub struct Hand {
    pub known_cards: HashMap<i8, i8>,
    pub known_voids: HashSet<i8>,
    pub number_of_unknown_cards: i8,
}

impl fmt::Display for Hand {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {

        for (&suit, &count) in self.known_cards.iter() {
            for _ in 0..count {
                write!(f, "{}", suit)?;
            }
        }
        for _ in 0..self.number_of_unknown_cards {
            write!(f, "?")?;
        }
        if !self.known_voids.is_empty() {
            write!(f, "x")?;
            for suit in &self.known_voids {
                write!(f, "{}", suit)?;
            }
        }
        Ok(())
    }
}

impl Hand {
    /** 
        Creates an empty hand
    */
    pub fn new() -> Hand {
        Hand {
            known_cards : HashMap::new(),
            known_voids : HashSet::new(),
            number_of_unknown_cards: 4,
        }
    }

    /** 
        Returns true if this player has no cards at all.
    */
    pub fn is_empty(&self) -> bool {
        return self.known_cards.is_empty() && self.number_of_unknown_cards == 0;
    }

    /** 
        Write to stdout a representation of the hand, also showing the next player
    */
    pub fn show(&self, is_next_player: bool) {
        print!("{}", self);
        if is_next_player {
            println!("   <<<< next player");
        } else {
            println!();
        }
    }

    /** 
        Make sure we have one of these cards. The player has just
        requested a card from this suit. Returns True if we were
        able to validate this.
    */
    pub fn ensure_have(&mut self, suit: i8) -> bool {
        if self.known_cards.contains_key(&suit) {
            assert!(self.known_cards[&suit] > 0);
            return true;
        }
        if self.known_voids.contains(&suit) {
            return false;
        }
        self._remove_unknown();
        self.known_cards.insert(suit, 1);
        return true;
    }

    pub fn _remove_unknown(&mut self) {
        assert!(self.number_of_unknown_cards > 0);
        self.number_of_unknown_cards -= 1;
        if self.number_of_unknown_cards == 0 {
            self.known_voids.clear();
        }
    }

    /** 
        We know this hand does not contain this suit. For example the player has
        rejected a request for a card. Returns True if we were able to validate it.
    */
    pub fn ensure_have_not(&mut self, suit: i8) -> bool {
        if self.known_cards.contains_key(&suit) {
            return false;
        }
        self.known_voids.insert(suit);
        return true;
    }

    /** 
        Take one card of this suit away from the user. If it is a known card, remove that.
        If not, take it from the unknowns. Returns True if we were able to remove it
    */
    pub fn remove(&mut self, suit: i8) -> bool {
        if self.known_cards.contains_key(&suit) {
            let count = self.known_cards[&suit];
            if count > 1 {
                self.known_cards.insert(suit, count - 1);
            } else {
                self.known_cards.remove(&suit);
            }
            return true;
        } else {
            if self.known_voids.contains(&suit) {
                return false;
            } else {
                self._remove_unknown();
                return true;
            }
        }
    }

    /** 
        Adds a card to this hand
    */
    pub fn add(&mut self, suit: i8) {
        *self.known_cards.entry(suit).or_insert(0) += 1;
    }

    /** 
        Returns true if this hand contains four of a kind.
    */
    pub fn has_four_of_a_kind(&mut self) -> bool {
        for (_, &count) in self.known_cards.iter() {
            if count == 4 {
                return true;
            }
        }
        return false;
    }

    /** 
        Returns true if this hand is entirely known
    */
    pub fn is_determined(&self) -> bool {
        return self.number_of_unknown_cards == 0;
    }

    /** 
        Adds any known cards into running totals for all hands
    */
    pub fn running_totals(&self, totals: &mut HashMap<i8, i8>) {
        for (&key, &value) in self.known_cards.iter() {
            *totals.entry(key).or_insert(0) += value;
        }
    }

    /** 
        There are four known cards of this suit, so we know it is
        no longer unknown. Returns True if anything changed.
    */
    pub fn kill_unknown(&mut self, suit: i8) -> bool {
        if self.number_of_unknown_cards > 0 {
            return self.known_voids.insert(suit)
        } else {
            return false;
        }
    }

    /** 
        If we know so much about a void item that we can fix
        its suit, do so and return True.
    */
    pub fn force_unknowns(&mut self, number_of_suits: i8) -> bool {
        if self.number_of_unknown_cards == 0 {
            return false
        }
        if self.known_voids.len() as i8 == number_of_suits - 1 {
            for i in 0..number_of_suits {
                if !self.known_voids.contains(&i) {
                    *self.known_cards.entry(i).or_insert(0) += self.number_of_unknown_cards;
                    self.number_of_unknown_cards = 0;
                    self.known_voids.clear();
                    return true
                }
            }
        }

        return false
    }

    /** 
        Can I legally ask for the given suit?
    */
    pub fn is_legal(&self, suit: i8) -> bool {
        if self.known_cards.contains_key(&suit) {
            return true;
        }
        if self.number_of_unknown_cards == 0 {
            return false;
        }
        if self.known_voids.contains(&suit) {
            return false;
        }
        return true;
    }

    /** 
        Does this hand definitely contain the given suit?
        Returns a tuple of [forced, yes/no]
    */
    pub fn has_card(&self, suit: i8) -> (bool, bool) {
        if self.known_cards.contains_key(&suit) {
            return (true, true)
        } else {
            if self.number_of_unknown_cards == 0 {
                return (true, false)
            } else {
                if self.known_voids.contains(&suit) {
                    return (true, false)
                } else {
                    return (false, true)
                }
            }
        }
    }

    /** 
        If only one of the hands has any unknowns in it, we
        can fill them given the counts of other cards. Returns
        True if it cannot be done.
    */
    pub fn fill_unknowns(&mut self, totals: &mut HashMap<i8, i8>) -> bool {
        for (&suit, &count) in totals.iter() {
            if count < 4 {
                if !self.fill_some_unknowns(suit, 4 - count) {
                    return false
                }
            }
        }
        assert!(self.number_of_unknown_cards == 0);
        return true
    }

    /** 
        Fill in some of the unknowns in a given hand with the
        given suit. Returns False if
        it cannot be done.
    */
    pub fn fill_some_unknowns(&mut self, suit: i8, count: i8) -> bool {
        assert!(count <= 4);
        if self.number_of_unknown_cards < count {
            return false;
        }
        assert!(!self.known_voids.contains(&suit));
        self.number_of_unknown_cards -= count;
        *self.known_cards.entry(suit).or_insert(0) += count;
        return true;
    }

    /** 
        Returns a representation of this hand as an integer, so
        we can easily test whether the hand repeats. Pass in the
        position of any hands that have been processed so far.

        Note that we assume the hand is not an immediate winner, so
        the count of cards in any suit must be less than four.
    */
    pub fn position(&self, mut pos: i128, permutation: &[i8]) -> i128 {
        for i in permutation {
            let count = self.known_cards.get(&i).cloned().unwrap_or(0);
            assert!(count >= 0 && count < 4);
            pos *= 4;
            pos += count as i128;
        }
        pos *= 8;
        pos += self.number_of_unknown_cards as i128;
        for i in permutation {
            let count = if self.known_voids.contains(i) { 1 } else { 0 };
            pos *= 2;
            pos += count;
        }
        return pos;
    }

    /** 
        Given an array of rankings for the different suits,
        adjust the rankings to make more common suits higher
        than less common ones. This function is called
        for each hand in turn, with the earlier invocations
        more significant than the later.
    */
    pub fn adjust_ranking(&self, rankings: &mut[i64]) {
        let n = rankings.len();
        for i in rankings.iter_mut() {
            *i *= n as i64;
        }
        for i in 0..n {
            let suit = i as i8;
            let count = self.known_cards.get(&suit).cloned().unwrap_or(0) as i64;
            rankings[i] += count;
        }
        for i in rankings.iter_mut() {
            *i *= 2;
        }
        for i in 0..n {
            let suit = i as i8;
            if self.known_voids.contains(&suit) {
                rankings[i] += 1;
            }
        }
    }
}

pub const NO_WINNER: i64 = -1;
pub const ILLEGAL_CARDS: i64 = -2;

/** 
    Represents a pack of playing cards, divided by the given number
    of players. There are four cards per player, and the same
    number of suits as players.
*/
#[derive(Clone)]
pub struct Cards {
    pub hands: Vec<Hand>,
}

impl fmt::Display for Cards {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {

        let mut first = true;
        for hand in &self.hands {
            if !first {
                write!(f, "/")?;
            }
            first = false;
            write!(f, "{}", hand)?;
        }
        return Ok(())
    }
}

impl Cards {
    pub fn new(number_of_players: usize) -> Cards {
        let tmp_hands = (0..number_of_players).map(|_| Hand::new()).collect::<Vec<_>>();
        Cards {
            hands: tmp_hands,
        }
    }

    pub fn is_empty(&mut self, player: usize) -> bool {
        return self.hands[player].is_empty();
    }

    pub fn number_of_players(&self) -> usize {
        return self.hands.len();
    }

    /** 
        Shows all the hands, with an indicator next to the next to play.
        next_player can be -1, but if it is in the legal range of players,
        that hand is highlighted.
    */
    pub fn show(&self, next_player: usize) {
        for (i, hand) in self.hands.iter().enumerate() {
            hand.show(i == next_player);
        }
    }

    /** 
        Moves a card from one hand to another after a successful request.
        _this_ is the player who asked for the transfer. _other_ is the
        player who said they did not have the card. Returns True if it 
        could be done.
    */
    pub fn transfer(&mut self, suit: i8, other: usize, this: usize, no_throw: bool) -> bool {
        if !self.hands[this].ensure_have(suit) {
            if no_throw {
                return false;
            }
            panic!("Cannot ask for {} as we know you don't have any", suit);
        }
        if !self.hands[other].remove(suit) {
            if no_throw {
                return false;
            }
            assert!(false, "We know player {} doesn't have any {}", other, suit);
        }
        self.hands[this].add(suit);
        return true;
    }

    /** 
        Records an unsuccessful request for a transfer. _this_ is the
        player who asked for the transfer. _other_ is the player who
        said they did not have the card. Returns True if it could be
        done.
    */
    pub fn no_transfer(&mut self, suit: i8, other: usize, this: usize, no_throw: bool) -> bool {
        if !self.hands[this].ensure_have(suit) {
            if no_throw {
                return false;
            }
            panic!("Cannot ask for {} as we know you don't have any", suit);
        }
        if !self.hands[other].ensure_have_not(suit) {
            if no_throw {
                return false;
            }
            panic!("Cannot reject {} as we know you have one", suit);
        }
        return true;
    }

    /** 
        Is there a winner? If so, return the number of
        the winner. If not, return -1. If the number of cards
        in any suit is greater than 4, or if the hands are
        illegal for any other reason, return -2.
    */
    pub fn test_winner(&mut self, last_player: usize) -> i64 {
        if !self.shake_down() {
            return ILLEGAL_CARDS;
        }
        let mut all_determined = true;
        for hand in &self.hands {
            if !hand.is_determined() {
                all_determined = false;
                break;
            }
        }
        if all_determined {
            return last_player as i64;
        }
        let n = self.hands.len();
        for i in 0..n {
            let player = (i + last_player) % n;
            if self.hands[player].has_four_of_a_kind() {
                return player as i64;
            }
        }
        return NO_WINNER;
    }

    /** 
        Resolve any logical inferences that can be made on the cards.
        Returns True if the cards are logically consistent.
    */
    pub fn shake_down(&mut self) -> bool {
        let len_hands = self.hands.len();
        let all_suits = (0..len_hands as i8).collect::<HashSet<_>>();
        let mut any_changes = true;
        while any_changes {
            any_changes = false;
            let mut totals = HashMap::new();
            for hand in &self.hands {
                hand.running_totals(&mut totals);
            }
            for (&suit, &total) in totals.iter() {
                if any_changes {
                    break;
                }
                if total > 4 {
                    return false;
                }
                if total == 4 {
                    for hand in &mut self.hands {
                        if hand.kill_unknown(suit) {
                            any_changes = true;
                        }
                    }
                } else {
                    let mut hands_with_unknowns = vec![];
                    let mut number_of_unknown_cards = 0;
                    for (i, hand) in self.hands.iter().enumerate() {
                        if hand.number_of_unknown_cards > 0 &&
                                !hand.known_voids.contains(&suit) {
                            hands_with_unknowns.push(i);
                            number_of_unknown_cards += hand.number_of_unknown_cards;
                        }
                    }
                    if hands_with_unknowns.len() == 1 {
                        if !self.hands[hands_with_unknowns[0]].fill_some_unknowns(suit, 4 - total) {
                            return false;
                        }
                        any_changes = true;
                    } else {
                        let remainder = 4 - total;
                        if number_of_unknown_cards < remainder {
                            return false;
                        } else {
                            if number_of_unknown_cards == remainder {
                                for i in &hands_with_unknowns {
                                    let hand = &mut self.hands[*i];
                                    let unknowns = hand.number_of_unknown_cards;
                                    if !hand.fill_some_unknowns(suit, unknowns) {
                                        return false;
                                    }
                                }
                                any_changes = true;
                            }
                        }
                    }
                }
            }
            for hand in &mut self.hands {
                if hand.force_unknowns(len_hands as i8) {
                    any_changes = true;
                }
            }
            if any_changes {
                continue;
            }
            let mut hands_with_unknowns = vec![];
            for (i, hand) in self.hands.iter().enumerate() {
                if hand.number_of_unknown_cards > 0 {
                    hands_with_unknowns.push(i);
                }
            }
            if hands_with_unknowns.len() == 1 {
                if !self.hands[hands_with_unknowns[0]].fill_unknowns(&mut totals) {
                    return false;
                }
                any_changes = true;
            }
            if any_changes {
                continue;
            }

            // fill in any missing totals with zero
            for suit in 0..len_hands as i8 {
                if !totals.contains_key(&suit) {
                    totals.insert(suit, 0);
                }
            }

            for hand in &mut self.hands {
                if hand.number_of_unknown_cards > 1 {
                    let mut possible = 0;
                    for (&suit, &total) in totals.iter() {
                        if total < 4 && !hand.known_voids.contains(&suit) {
                            possible += 4 - total;
                        }
                    }
                    if possible < hand.number_of_unknown_cards {
                        return false;
                    }
                    let unknowns = hand.number_of_unknown_cards;
                    for (&suit, &total) in totals.iter() {
                        if total < 4 && !hand.known_voids.contains(&suit) {
                            let remaining = possible - (4 - total);
                            if remaining < unknowns {
                                let min_suit = unknowns - remaining;
                                if !hand.fill_some_unknowns(suit, min_suit) {
                                    return false;
                                }
                                any_changes = true;
                            }
                        }
                    }
                }
            }
            if any_changes {
                continue;
            }
            for (&suit, &total) in totals.iter() {
                if total > 2 {
                    continue;
                }
                let mut slots = 0;
                for hand in &self.hands {
                    if !hand.known_voids.contains(&suit) {
                        slots += hand.number_of_unknown_cards;
                    }
                }
                for hand in &mut self.hands {
                    if !hand.known_voids.contains(&suit) {
                        let other_slots = slots - hand.number_of_unknown_cards;
                        if other_slots < total {
                            if !hand.fill_some_unknowns(suit, total - other_slots) {
                                return false;
                            }
                        }
                    }
                }
            }
            if any_changes {
                continue;
            }
            let mut groups : HashMap<Vec<i8>, Vec<usize>> = HashMap::new();
            for (player, hand) in self.hands.iter().enumerate() {
                let group_len = hand.known_voids.len();
                if hand.number_of_unknown_cards > 0 && group_len > 1 {
                    let group : Vec<i8> = all_suits.difference(&hand.known_voids).cloned().collect();
                    groups.entry(group).or_insert(vec![]).push(player);
                }
            }
            for (group, players) in groups.iter() {
                if players.len() > 1 {
                    let mut missing = group.len() as i8 * 4;
                    for (&suit, &total) in totals.iter() {
                        if group.iter().find(|&x| *x == suit) != None {
                            missing -= total as i8;
                        }
                    }
                    let mut holes = 0;
                    for &player in players {
                        holes += self.hands[player].number_of_unknown_cards as i8;
                    }
                    if missing < holes {
                        return false;
                    }
                    if missing == holes {
                        for (player, hand) in self.hands.iter_mut().enumerate() {
                            if players.iter().find(|&x| *x == player) == None {
                                for suit in group {
                                    if hand.kill_unknown(*suit) {
                                        any_changes = true;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        return true;
    }

    /** 
        Is this move legal?
    */
    pub fn legal(&self, other: usize, suit: i8, this: usize, verbose: bool) -> bool {
        if this == other {
            return _not_legal(verbose, "You cannot ask yourself for a card");
        }
        let n = self.hands.len();
        if this >= n || other >= n {
            return _not_legal(verbose, "Player number out of range");
        }
        if suit < 0 || suit >= n as i8 {
            return _not_legal(verbose, "Suit number out of range");
        }
        if !self.hands[this].is_legal(suit) {
            return _not_legal(verbose, "You cannot ask for a suit you do not have");
        }
        return true;
    }

    /** 
        Returns a list of legal moves in a fixed order, depending
        on the ordering of suits specified in permutations.

        Note that it would be possible for a theoretically legal
        move to have no legal reply. This case should be rejected
        by shake_down, which should add to the known_void list any
        suit that would have no legal reply.
    */
    pub fn legal_moves_given_permutation(&self, this: usize, permutation: &[i8]) -> Vec<(usize, i8)> {
        let mut moves = vec![];
        let mut suits = vec![];
        let this_hand = &self.hands[this];
        for &i in permutation {
            if this_hand.is_legal(i) {
                suits.push(i);
            }
        }
        let mut totals : HashMap<i8, i8> = HashMap::new();
        for hand in &self.hands {
            hand.running_totals(&mut totals);
        }
        let n = self.hands.len();
        for i in 1..n {
            let other = (i + this) % n;
            for suit in &suits {
                let (forced, has) = self.hands[other].has_card(*suit);
                if forced && !has {
                    continue;
                } else {
                    if !forced {
                        let mut count = *totals.get(&suit).unwrap_or(&0);
                        if !this_hand.known_cards.contains_key(&suit) {
                            count += 1;
                        }
                        if count >= 4 {
                            continue;
                        }
                    }
                }
                moves.push((other, *suit));
            }
        }
        return moves;
    }

    /** 
        Returns a representation of the current set of hands as an integer,
        so we can test whether the position repeats.
    */
    pub fn position(&mut self, last_player: usize) -> i128 {
        let n = self.number_of_players() as i8;
        let permutation : Vec<i8> = (0..n).collect();
        return self.position_given_permutation(&permutation, last_player, false);
    }

    /** 
        Returns a representation of the current set of hands, using the
        given permutation of suits to define the relative ordering.  The position function
        is carefully written to give the same result for different instances
        of symmetric positions. The following symmetries are handled:

        * Rotation of players (e.g. player 0 -> 1, 1 -> 2 and 2 -> 0)
        * Permutation of suits (e.g. swapping any two suits)

        Note that position is always an integer greater or equal to zero.
    */
    pub fn position_given_permutation(&self, permutation: &[i8], last_player: usize, player_symmetric: bool) -> i128 {
        let mut pos = 0;
        let n = self.hands.len();
        assert!(last_player < n);
        for i in 0..n {
            let hand = &self.hands[(i + last_player) % n];
            pos = hand.position(pos, permutation);
        }
        if !player_symmetric {
            pos *= n as i128;
            pos += last_player as i128;
        }
        return pos;
    }

    /** 
        Handle permutation of suits by ordering them according to how
        they appear in the hands: the most common suit in the first
        hand, down to the last suit seen. Suits that are not seen at
        all, or which have the same ordering in all hands, are ordered
        arbitrarily.
    */
    pub fn permutation(&self, last_player: usize) -> Vec<i8> {
        let n = self.hands.len();
        assert!(last_player < n);
        let mut ranking = vec![0; n];
        for i in 0..n {
            let hand = &self.hands[(i + last_player) % n];
            hand.adjust_ranking(&mut ranking);
        }

        // We want to return a vector that is the ordering of these rankings
        // in reverse order.
        let mut result : Vec<i8> = (0..n as i8).collect();
        result.sort_by(|&a, &b| ranking[b as usize].cmp(&ranking[a as usize]));
        return result
    }

    /** 
        Does the given hand contain this card?
        Returns a tuple of [forced, yes/no]
    */
    pub fn has_card(&self, suit: i8, this: usize, other: usize) -> (bool, bool) {
        let (forced, has) = self.hands[this].has_card(suit);
        if forced {
            return (forced, has);
        }
        let mut copied = self.clone();
        if !copied.no_transfer(suit, this, other, true) || !copied.shake_down() {
            return (true, true);
        }
        copied = self.clone();
        if !copied.transfer(suit, this, other, true) || !copied.shake_down() {
            return (true, false);
        }
        return (false, false);
    }

    /** 
        Finds the next player who is able to move (has any cards)
    */
    pub fn next_player(&mut self, this_player: usize) -> usize {
        let n = self.number_of_players();
        let mut p = (this_player + 1) % n;
        while self.hands[p].is_empty() {
            p = (p + 1) % n;
            assert!(p != this_player, "At least one player must have some cards");
        }
        return p;
    }

}

pub fn _not_legal(verbose: bool, message: &str) -> bool {
    if verbose {
        println!("{}", message);
    }
    return false;
}

#[cfg(test)]
mod tests {
    use super::*;

    /** 
        Tests the case where we have 000/22?/111???x0
        and player 1 asks player 0 for a 1.
    */
    #[test]
    pub fn test_no_transfer() {
        let mut h0 = Hand::new();
        h0.known_cards = [(0, 3)].iter().cloned().collect::<HashMap<_, _>>();
        h0.number_of_unknown_cards = 0;
        let mut h1 = Hand::new();
        h1.known_cards = [(2, 2)].iter().cloned().collect::<HashMap<_, _>>();
        h1.number_of_unknown_cards = 1;
        let mut h2 = Hand::new();
        h2.known_cards = [(1, 3)].iter().cloned().collect::<HashMap<_, _>>();
        h2.number_of_unknown_cards = 3;
        let mut cards = Cards::new(3);
        cards.hands = vec![
            h0,
            h1,
            h2,
            ];
        cards.show(1);
        println!("player 1 asks player 0 for a 1, who must say no");
        cards.no_transfer(1, 0, 1, false);
        cards.show(usize::max_value());
        println!("shake_down");
        cards.shake_down();
        cards.show(usize::max_value());
        assert!(cards.hands[0].known_cards == [(0, 3)].iter().cloned().collect::<HashMap<_, _>>());
        assert!(cards.hands[1].known_cards == [(2, 2), (1, 1)].iter().cloned().collect::<HashMap<_, _>>());
        assert!(cards.hands[2].known_cards == [
            (1, 3),
            (0, 1),
            (2, 2),
            ].iter().cloned().collect::<HashMap<_, _>>());
        println!("test_no_transfer: succeeded");
    }

    /** 
        Initial hands: 0???/00??
        Player 0 asks player 1 for 1, who refuses. (This is
        illegal, but we should handle this gracefully.)
    */
    #[test]
    pub fn test_no_transfer_2() {
        let mut h0 = Hand::new();
        h0.known_cards = [(0, 1)].iter().cloned().collect::<HashMap<_, _>>();
        h0.number_of_unknown_cards = 3;
        let mut h1 = Hand::new();
        h1.known_cards = [(0, 2)].iter().cloned().collect::<HashMap<_, _>>();
        h1.number_of_unknown_cards = 2;
        let mut cards = Cards::new(2);
        cards.hands = vec![h0, h1];
        let transferred = cards.no_transfer(1, 1, 0, true);
        assert!(transferred);
        println!("test_no_transfer_2: succeeded");
    }

    /** 
        Tests the cards 00???/??? for whether they are
        consistent. Of course they are.
    */
    #[test]
    pub fn test_simple_shakedown() {
        let mut h0 = Hand::new();
        h0.known_cards = [(0, 2)].iter().cloned().collect::<HashMap<_, _>>();
        h0.number_of_unknown_cards = 3;
        let mut h1 = Hand::new();
        h1.known_cards = [].iter().cloned().collect::<HashMap<_, _>>();
        h1.number_of_unknown_cards = 3;
        let mut cards = Cards::new(2);
        cards.hands = vec![h0, h1];
        cards.show(usize::max_value());
        println!("shake_down");
        let ok = cards.shake_down();
        cards.show(usize::max_value());
        assert!(ok);
        assert!(cards.hands[0].known_cards == [(0, 2), (1, 1)].iter().cloned().collect::<HashMap<_, _>>());
        assert!(cards.hands[1].known_cards == [(1, 1)].iter().cloned().collect::<HashMap<_, _>>());
        println!("test_simple_shake_down: succeeded");
    }

    /** 
        Tests the case where we have 001/0?x1/22211??x0 and
        we shake_down. We know that player 1 cannot have a 2
        because that means player 2 would have to have a 0
        and that is excluded.
    */
    #[test]
    pub fn test_shake_down() {
        let mut h0 = Hand::new();
        h0.known_cards = [(0, 2), (1, 1)].iter().cloned().collect::<HashMap<_, _>>();
        h0.number_of_unknown_cards = 0;
        let mut h1 = Hand::new();
        h1.known_cards = [(0, 1)].iter().cloned().collect::<HashMap<_, _>>();
        h1.number_of_unknown_cards = 1;
        h1.known_voids = [1].iter().cloned().collect::<HashSet<_>>();
        let mut h2 = Hand::new();
        h2.known_cards = [(2, 3), (1, 2)].iter().cloned().collect::<HashMap<_, _>>();
        h2.number_of_unknown_cards = 2;
        h2.known_voids = [0].iter().cloned().collect::<HashSet<_>>();
        let mut cards = Cards::new(3);
        cards.hands = vec![
            h0,
            h1,
            h2,
            ];
        cards.shake_down();
        assert!(cards.hands[0].known_cards == [(0, 2), (1, 1)].iter().cloned().collect::<HashMap<_, _>>());
        assert!(cards.hands[1].known_cards == [(0, 2)].iter().cloned().collect::<HashMap<_, _>>());
        assert!(cards.hands[2].known_cards == [(2, 4), (1, 3)].iter().cloned().collect::<HashMap<_, _>>());
        println!("test_shake_down: succeeded");
    }

    /** 
        Given the cards 00??/01?/11??? is it legal for
        player 2 to tell player 1 that he does not have any
        of suit 2? (It cannot be as that leaves only 3 slots
        for 2s.)
    */
    #[test]
    pub fn test_has_card() {
        let mut h0 = Hand::new();
        h0.known_cards = [(0, 2)].iter().cloned().collect::<HashMap<_, _>>();
        h0.number_of_unknown_cards = 2;
        let mut h1 = Hand::new();
        h1.known_cards = [(0, 1), (1, 1)].iter().cloned().collect::<HashMap<_, _>>();
        h1.number_of_unknown_cards = 1;
        let mut h2 = Hand::new();
        h2.known_cards = [(1, 2)].iter().cloned().collect::<HashMap<_, _>>();
        h2.number_of_unknown_cards = 3;
        let mut cards = Cards::new(3);
        cards.hands = vec![
            h0,
            h1,
            h2,
            ];
        cards.show(usize::max_value());
        let (forced, yes) = cards.has_card(2, 2, 0);
        assert!(forced && yes);
        println!("test_has_card: succeeded");
    }

    /** 
        Do a shakedown of 2211?x0/00??x1/???. Player 2 must be
        holding at least one 1, because player 1 has none, and
        player 0 accounts for no more than 3 of them.
    */
    #[test]
    pub fn test_three_player_shakedown() {
        let mut h0 = Hand::new();
        h0.known_cards = [(2, 2), (1, 2)].iter().cloned().collect::<HashMap<_, _>>();
        h0.number_of_unknown_cards = 1;
        h0.known_voids = [0].iter().cloned().collect::<HashSet<_>>();
        let mut h1 = Hand::new();
        h1.known_cards = [(0, 2)].iter().cloned().collect::<HashMap<_, _>>();
        h1.number_of_unknown_cards = 2;
        h1.known_voids = [1].iter().cloned().collect::<HashSet<_>>();
        let mut h2 = Hand::new();
        h2.number_of_unknown_cards = 3;
        let mut cards = Cards::new(3);
        cards.hands = vec![
            h0,
            h1,
            h2,
            ];
        cards.show(usize::max_value());
        let ok = cards.shake_down();
        println!("shakedown");
        cards.show(usize::max_value());
        assert!(ok);
        assert!(cards.hands[2].known_cards[&1] == 1);
        println!("test_three_player_shakedown: succeeded");
    }

    /** 
        Do a shakedown of 2???/0???x2/????x0.
        Player 2 must be holding a 1, because he can have at most 3
        2's and can't have any 0's.
    */
    #[test]
    pub fn test_three_player_shakedown_2() {
        let mut h0 = Hand::new();
        h0.known_cards = [(2, 1)].iter().cloned().collect::<HashMap<_, _>>();
        h0.number_of_unknown_cards = 3;
        let mut h1 = Hand::new();
        h1.known_cards = [(0, 1)].iter().cloned().collect::<HashMap<_, _>>();
        h1.number_of_unknown_cards = 3;
        h1.known_voids = [2].iter().cloned().collect::<HashSet<_>>();
        let mut h2 = Hand::new();
        h2.number_of_unknown_cards = 4;
        h2.known_voids = [0].iter().cloned().collect::<HashSet<_>>();
        let mut cards = Cards::new(3);
        cards.hands = vec![
            h0,
            h1,
            h2,
            ];
        cards.show(usize::max_value());
        let ok = cards.shake_down();
        println!("shakedown");
        cards.show(usize::max_value());
        assert!(ok);
        assert!(cards.hands[2].known_cards[&1] == 1);
        println!("test_three_player_shakedown_2: succeeded");
    }

    /** 
        Are the cards 222??x0/1x23/000?/11330?x0 legal?
    */
    #[test]
    pub fn test_four_player_shakedown() {
        let mut h0 = Hand::new();
        h0.known_cards = [(2, 3)].iter().cloned().collect::<HashMap<_, _>>();
        h0.number_of_unknown_cards = 2;
        h0.known_voids = [0].iter().cloned().collect::<HashSet<_>>();
        let mut h1 = Hand::new();
        h1.known_cards = [(1, 1)].iter().cloned().collect::<HashMap<_, _>>();
        h1.number_of_unknown_cards = 0;
        h1.known_voids = [2, 3].iter().cloned().collect::<HashSet<_>>();
        let mut h2 = Hand::new();
        h2.known_cards = [(0, 3)].iter().cloned().collect::<HashMap<_, _>>();
        h2.number_of_unknown_cards = 1;
        let mut h3 = Hand::new();
        h3.known_cards = [
            (0, 1),
            (1, 2),
            (3, 2),
            ].iter().cloned().collect::<HashMap<_, _>>();
        h3.number_of_unknown_cards = 2;
        let mut cards = Cards::new(4);
        cards.hands = vec![
            h0,
            h1,
            h2,
            h3,
            ];
        cards.show(usize::max_value());
        let ok = cards.shake_down();
        println!("shakedown");
        cards.show(usize::max_value());
        assert!(ok);
        println!("test_four_player_shakedown: succeeded");
    }

    /** 
        Consider the hands:

        222?x01
        1x23
        000??x23
        1133??

        This is a winner for player 2, because one of those ?s must be a
        0 and the other must be a 1, as there are three each elsewhere.
        Thus player 2 has four zeros.
    */
    #[test]
    pub fn test_four_player_test_winner() {
        let mut h0 = Hand::new();
        h0.known_cards = [(2, 3)].iter().cloned().collect::<HashMap<_, _>>();
        h0.number_of_unknown_cards = 1;
        h0.known_voids = [0, 1].iter().cloned().collect::<HashSet<_>>();
        let mut h1 = Hand::new();
        h1.known_cards = [(1, 1)].iter().cloned().collect::<HashMap<_, _>>();
        h1.number_of_unknown_cards = 0;
        h1.known_voids = [2, 3].iter().cloned().collect::<HashSet<_>>();
        let mut h2 = Hand::new();
        h2.known_cards = [(0, 3)].iter().cloned().collect::<HashMap<_, _>>();
        h2.number_of_unknown_cards = 2;
        h2.known_voids = [2, 3].iter().cloned().collect::<HashSet<_>>();
        let mut h3 = Hand::new();
        h3.known_cards = [(1, 2), (3, 2)].iter().cloned().collect::<HashMap<_, _>>();
        h3.number_of_unknown_cards = 2;
        let mut cards = Cards::new(4);
        cards.hands = vec![
            h0,
            h1,
            h2,
            h3,
            ];
        cards.show(usize::max_value());
        let winner = cards.test_winner(2);
        assert!(winner == 2);
    }

    /** 
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
    */
    #[test]
    pub fn test_four_player_exclusions() {
        let mut h0 = Hand::new();
        h0.known_cards = [(2, 3)].iter().cloned().collect::<HashMap<_, _>>();
        h0.number_of_unknown_cards = 1;
        h0.known_voids = [0, 1].iter().cloned().collect::<HashSet<_>>();
        let mut h1 = Hand::new();
        h1.known_cards = [(1, 3)].iter().cloned().collect::<HashMap<_, _>>();
        h1.number_of_unknown_cards = 1;
        h1.known_voids = [2, 3].iter().cloned().collect::<HashSet<_>>();
        let mut h2 = Hand::new();
        h2.known_cards = [(0, 3)].iter().cloned().collect::<HashMap<_, _>>();
        h2.number_of_unknown_cards = 1;
        h2.known_voids = [2].iter().cloned().collect::<HashSet<_>>();
        let mut h3 = Hand::new();
        h3.known_cards = [(3, 3)].iter().cloned().collect::<HashMap<_, _>>();
        h3.number_of_unknown_cards = 1;
        h3.known_voids = [0, 1].iter().cloned().collect::<HashSet<_>>();
        let mut cards = Cards::new(4);
        cards.hands = vec![
            h0,
            h1,
            h2,
            h3,
            ];
        println!("test_four_player_exclusions");
        cards.show(usize::max_value());
        let ok = cards.shake_down();
        println!("test_four_player_exclusions: after shake_down");
        cards.show(usize::max_value());
        assert!(ok);
        assert!(cards.hands[2].known_voids.iter().position(|&tmp| tmp == 3) != None);
        println!("test_four_player_exclusions: succeeded");
    }

    /** 
        Tests the ordering of suits when we have 002?/0?x1/2211??x0.
        The order should be:
        
        * 0, 2, 1 for player 0
        * 0, 1, 2 for player 1
        * 2, 1, 0 for player 2
    */
    #[test]
    pub fn test_permutation() {
        let mut h0 = Hand::new();
        h0.known_cards = [(0, 2), (2, 1)].iter().cloned().collect::<HashMap<_, _>>();
        h0.number_of_unknown_cards = 1;
        let mut h1 = Hand::new();
        h1.known_cards = [(0, 1)].iter().cloned().collect::<HashMap<_, _>>();
        h1.number_of_unknown_cards = 1;
        h1.known_voids = [1].iter().cloned().collect::<HashSet<_>>();
        let mut h2 = Hand::new();
        h2.known_cards = [(2, 2), (1, 2)].iter().cloned().collect::<HashMap<_, _>>();
        h2.number_of_unknown_cards = 2;
        h2.known_voids = [0].iter().cloned().collect::<HashSet<_>>();
        let mut cards = Cards::new(3);
        cards.hands = vec![
            h0,
            h1,
            h2,
            ];
        let p0 = cards.permutation(0);
        let p1 = cards.permutation(1);
        let p2 = cards.permutation(2);
        print!("p0={:?}", p0);
        print!("p1={:?}", p1);
        print!("p2={:?}", p2);
        assert!(p0 == vec![
            0,
            2,
            1,
            ]);
        assert!(p1 == vec![
            0,
            1,
            2,
            ]);
        assert!(p2 == vec![
            2,
            1,
            0,
            ]);
        println!("test_permutation: succeeded");
    }

    /** 
        We start with the hands 00111?x1/?x01/02223?/33?x01.
        There are many restrictions implicit in this, and the
        hands are equivalent to 000111/?x01/022231/33?x01
    */
    #[test]
    pub fn test_complex_shakedown() {
        let mut h0 = Hand::new();
        h0.known_cards = [(0, 2), (1, 3)].iter().cloned().collect::<HashMap<_, _>>();
        h0.number_of_unknown_cards = 1;
        h0.known_voids = [1].iter().cloned().collect::<HashSet<_>>();
        let mut h1 = Hand::new();
        h1.known_cards = [].iter().cloned().collect::<HashMap<_, _>>();
        h1.number_of_unknown_cards = 1;
        h1.known_voids = [0, 1].iter().cloned().collect::<HashSet<_>>();
        let mut h2 = Hand::new();
        h2.known_cards = [
            (0, 1),
            (2, 3),
            (3, 1),
            ].iter().cloned().collect::<HashMap<_, _>>();
        h2.number_of_unknown_cards = 1;
        let mut h3 = Hand::new();
        h3.known_cards = [(3, 2)].iter().cloned().collect::<HashMap<_, _>>();
        h3.number_of_unknown_cards = 1;
        h3.known_voids = [0, 1].iter().cloned().collect::<HashSet<_>>();
        let mut cards = Cards::new(4);
        cards.hands = vec![
            h0,
            h1,
            h2,
            h3,
            ];
        println!("test_complex_shakedown");
        cards.show(usize::max_value());
        cards.shake_down();
        println!("test_complex_shakedown: after shakedown");
        cards.show(usize::max_value());
        assert!(cards.hands[0].number_of_unknown_cards == 0);
        assert!(cards.hands[2].number_of_unknown_cards == 0);
    }
}