## Motivation

This is a tool to track rotation in a game.

The information includes total playing time, continuous playing time and resting time.

## Example output

```
============================================================
Game is RUNNING
------------------------------------------------------------
On the court:

Player: 2 B              total: 129      playing for: 129
Player: 3 C              total: 129      playing for: 129
Player: 4 D              total: 129      playing for: 129
Player: 5 E              total: 129      playing for: 129
Player: 6 F              total: 46       playing for: 46
------------------------------------------------------------
On the bench:

Player: 1 A              total: 83       resting for: 46
============================================================

```

## Usage

First, setup the path to Python lib and binary.

```
source bin/env.sh
```

Create a new game with starting lineup 1,2,3,4,5.

```
gt new 1 2 3 4 5
```

Loads a CSV file for roster.

```
gt load_team roster.csv
```

The CSV file format is like this:

```
number,name
1,A
2,B
3,C
4,D
5,E
6,F
```

Start the timer to start or resume the game.

```
gt start
```

Stop the timer to stop or pause the game.

```
gt stop
```

Substitution. E.g. Replace player 1 with player 6.

```
gt replace 1 6
```

Show the status.

```
gt show
```

Reset the game.

```
gt reset
```

## Explanation

Basically, there are four types of events:

- **START**: Game is started or resumed.
- **STOP**: Game is stopped or paused.
- **CHECK-IN**: A player goes on the court.
- **CHECK-OUT**: A player goes off the court.

Based on these event and current time, game tracker calculates these values:

- **Game time** is the segments between each start and stop.
- **On court time** is the segments between each check-in time and check-out time.

- **Total** time is calculated based on all overlapping time between game time and on-court time.

- **Playing for** value is for player on the court. It is calculated based on current time and max(check-in time, start time)
Note that we need a max because sometimes we may replace a player during break while game is paused.
However, a side effect is that whenever the game is paused and resumed, **playing for** value is reset to zero.
Here we assume that player has taken enough rest during the break, which may not be true.

- **Resting for** value is for player on the bench. It is calculated based on current time and check-out time.
Note that this represents the time that player has been taking rest on the bench, which may be longer than game time.
