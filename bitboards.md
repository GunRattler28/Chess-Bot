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

## Bitboards

### WHITE PAWNS

00000000
00000000
00000000
00000000
00000000
00000000
11111111
00000000

### BLACK PAWNS

00000000
11111111
00000000
00000000
00000000
00000000
00000000
00000000

### WHITE ROOKS

00000000
00000000
00000000
00000000
00000000
00000000
00000000
10000001

### BLACK ROOKS

10000001
00000000
00000000
00000000
00000000
00000000
00000000
00000000

### WHITE KNIGHTS

00000000
00000000
00000000
00000000
00000000
00000000
00000000
01000010

### BLACK KNIGHTS

01000010
00000000
00000000
00000000
00000000
00000000
00000000
00000000

### WHITE BISHOPS

00000000
00000000
00000000
00000000
00000000
00000000
00000000
00100100

### BLACK BISHOPS

00100100
00000000
00000000
00000000
00000000
00000000
00000000
00000000

### WHITE KING

00000000
00000000
00000000
00000000
00000000
00000000
00000000
00001000

### BLACK KING

00001000
00000000
00000000
00000000
00000000
00000000
00000000
00000000

### WHITE QUEEN

00000000
00000000
00000000
00000000
00000000
00000000
00000000
00010000

### BLACK QUEEN

00010000
00000000
00000000
00000000
00000000
00000000
00000000
00000000

### WHITE PIECES

00000000
00000000
00000000
00000000
00000000
00000000
11111111
11111111

### BLACK PIECES

11111111
11111111
00000000
00000000
00000000
00000000
00000000
00000000