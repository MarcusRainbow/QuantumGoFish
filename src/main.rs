mod cards;
mod game;
mod player;

use game::play;
use player::{HumanPlayer, CleverPlayer, Player};
use std::{env, process};

fn main() {
    let args: Vec<String> = env::args().collect();
    println!("{:?}", args);

    let mut player_types : Vec<Box<Player>> = Vec::new();
    let mut players = Vec::new();

    let mut human = None;
    let mut clever = None;
    let mut max_depth = 1000;
    let mut max_has_depth = 1000;
    let mut progress = 0;
    let mut prefs = Vec::new();
    let mut symmetric = true;

    let mut skip_first = true;
    for arg in &args {
        if skip_first {
            skip_first = false;
            continue;
        }

        if arg == "human" {
            if let Some(h) = human {
                // Already got a human player. Reuse it
                players.push(h);
            } else {
                let h = player_types.len();
                human = Some(h);
                players.push(h);
                player_types.push(Box::new(HumanPlayer::new()));
            }
        } else if arg == "clever" {
            if let Some(c) = clever {
                // Already got a clever player. Reuse it
                players.push(c);
            } else {
                let c = player_types.len();
                clever = Some(c);
                players.push(c);
                player_types.push(Box::new(CleverPlayer::new(max_depth, max_has_depth, progress, prefs.clone(), symmetric)));
            }
        } else if arg.starts_with("prefs:") {
            prefs.clear();
            let (_, p) = arg.split_at(6);
            let pv: Vec<&str> = p.split(',').collect();
            // sensible preference lengths are 3 (three players), 8 (four players), etc
            let len = pv.len();
            let mut prefs_len = 0;
            for i in 3..10 {
                if len == i * (i - 2) {
                    prefs_len = i;
                    break;
                }
            }
            if prefs_len == 0 {
                eprintln!("error -- prefs are not a suitable length (3, 8, 15 etc.)");
                process::exit(-1);
            }
            let part_len = prefs_len - 2;
            assert!(part_len * prefs_len == pv.len());
            let mut src = 0;
            for _ in 0..prefs_len {
                let mut part = Vec::new();
                for _ in 0..part_len {
                    // println!("parse pv[{}] = {}", src, pv[src]);
                    part.push(pv[src].parse::<usize>().unwrap());
                    src += 1;
                }
                prefs.push(part);
            }
            println!("prefs: {:?}", prefs);

            // are the prefs symmetric?
            let pref0 = prefs[0].clone();
            for (i, pref) in prefs.iter().enumerate() {
                for (p0, &p) in pref0.iter().zip(pref.iter()) {
                    if symmetric && p != (p0 + i) % prefs_len {
                        println!("not symmetric");
                        symmetric = false;
                        break;
                    }
                }
            }

        } else if arg.starts_with("max_depth=") {
            let (_, d) = arg.split_at(10);
            max_depth = d.parse::<i64>().unwrap();
            println!("max_depth: {}", max_depth);
        } else if arg.starts_with("max_has_depth=") {
            let (_, d) = arg.split_at(14);
            max_has_depth = d.parse::<i64>().unwrap();
            println!("max_has_depth: {}", max_has_depth);
        } else if arg.starts_with("progress=") {
            let (_, d) = arg.split_at(9);
            progress = d.parse::<i64>().unwrap();
            println!("progress: {}", progress);
        } else if arg == "help" {
            println!("{} [options] [human|clever]*", args[0]);
            println!("e.g. {} max_depth=3 prefs=1,2,0 human human clever", args[0]);
            println!("Options:");
            println!("    max_depth=<int>       how deep to search (1000)");
            println!("    max_has_depth=<int>   how deep to search for 'has_card' (1000)");
            println!("    progress=<int>        show progress every N cache writes (0)");
            println!("    prefs:<int>,<int>,... 2nd, 3rd preferences for each player (none)");
        } else {
            eprintln!("unrecognised arg {}: try {} help", arg, args[0]);
            process::exit(-1);
        }
    }

    if players.len() < 2 {
        eprintln!("need at least two players: try {} help", args[0]);
        process::exit(-1);
    }

    // run the game if we can
    let result = play(&players, player_types.as_mut_slice());
    if result == -1 {
        println!("Result is a draw");
    } else {
        println!("Win for player {}", result);
    }
}
