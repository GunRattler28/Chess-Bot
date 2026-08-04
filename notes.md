# Bitboards for Chess

## Binary and Decimal

0001 => 1
0011 => 3
1111 => 15

- With only 4 bits the largest number that can be stored is 15
- Positive or negative is stored in a bit. Allows negative numbers as well.
- A bitboard is an integer number.

## Why use bitboards

There is a bitboard for each piece (different for black pawn and white pawn)

White pawns bitboard would look like (below) at start of the game:

1 00000000
2 00000000
3 00000000
4 00000000
5 00000000
6 00000000
7 11111111
8 00000000
  abcdefgh

Same for all other pieces (different bitboards for same pieces of different colours)
6 bitboards for all pieces for 1 colour -> since each bitboard is just an integer, 6 integers to represent each colour
12 for both colours -> 12 integers to represent ALL pieces
Each of these integers is 64 digits long. (1 digit per position on board)

With array each postion has a value. 8 by 8 -> 64 integers to represent all pieces

12 < 64

**Bitboards are ~5 times as efficient**

## Moving Pieces

Below is the starting bitboard for white rooks

1 00000000
2 00000000
3 00000000
4 00000000
5 00000000
6 00000000
7 00000000
8 10000001
  abcdefgh

Change 1 to 0 and change end position to 1?

### Captures

The bitboard is for each piece so when you move a piece the bitboard doesn't show something has been captured. Would likely need to do a for loop for each bitboard. If there is a 1 at where the piece moved turn it to 0.

#### Preventing offboard pawn captures

This is difficult because the computer doesn't see lots of rows. All it sees is 1 long line.

## Extra Info

There are also 2 extra bitboards
1 bitboard for ALL white pieces and another for ALL black pieces
These bitboards ensure that we don't capture our own pieces

## Pros of bitboards

- Bitboards are faster and more efficient than array based chess engines
- Bitboards is useful for evaluating positions (helpful for bot implementation)
- Potential elo of chess bot is higher than if using array (but that is quite insignificant. Only high level Can still get to 2000+ elo with array)

## Cons of bitboards

- Difficult to have just 14 bitboards
- Finding specfic sqaures and whats there is a bit difficult
- Extra logic of mapping is needed

# Efficiency

## Alpha beta pruning

Alpha beta pruning works by storing the best guaranteed outcome for you (alpha) and the best guaranteed outcome for the opponent (beta). Whenever it finds a path where the opponent can force a move that is worse than the alpha, it immediately stops going down that path. The same happens for beta. By ordering the moves from best to worst it maximises the effect of alpha beta pruning as more paths are pruned.

## Aspiration windows

Aspiration windows work on the basis that moves don't usually swing the score by a lot. This means that when going down paths we can immediately remove anything that isn't within a certain amount of our expected score. If we find that the score is actually higher than we expect we search again but without the aspiration window. This helps remove the obviously bad paths