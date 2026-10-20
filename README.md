# Summary

A small chess bot made in Python that you can hone your skills against. Can consistenly beat 2000 elo bot on chess.com.

# Controls

- Left click (player's turn): select and move piece
- Left click (bot's turn): make premove
- Right click (tap): creates a small green circle
- Right click (drag): creates temporary arrow
- Right click (release on different square): draw arrow
- Right click (redraw arrow): delete specific arrow
- Middle click (remake premove): remove specific premove
- Middle click (other): clear all arrows and premoves
- Left arrow: undo last move
- Right arrow (within 3 seconds of undo): redo last undone move

# Game flow 

- When the game ends, text will come up on the screen and say which colour won, or what type of end condition was met (e.g: checkmate, stalemate, three fold repetition, etc). Once this text comes up, the player can still undo moves to quickly get back to where they made a bad decision and play something else instead.
- To restart the player can undo moves until they reach the starting position

# Technical details

The bot includes:

- alpha beta pruning
- iterative deepening
- move ordering
    1. Previous best move
    2. Promotions
    3. Captures
    4. Killer moves (moves which pruned most branches in search so far)
    5. Quiet moves (ordered based off decaying history table. History assigns value to all moves based off amount of prunes they have caused ever)
- principal variation search
- late move reductions
- aspiration windows
- null move pruning
- move evaluation (based off material difference + positional bonuses)

# Support

Currently only works on windows since it is a .exe file.