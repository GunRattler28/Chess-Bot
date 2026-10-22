# Overview

A small chess bot made in Python that you can hone your skills against.

# Controls

<div align="center">

| Action              | Input                        | Description                                          |
| :------------------ | :--------------------------- | :--------------------------------------------------- |
| **Select / Move**   | Left Click (Player's Turn)   | Select and move a piece                              |
| **Premove**         | Left Click (Bot's Turn)      | Queue a premove ahead of time                        |
| **Strategy Circle** | Right Click (Tap)            | Create or remove a green circle on a square          |
| **Temporary Arrow** | Right Click (Drag)           | Display a temporary drag arrow                       |
| **Draw Arrow**      | Right Click (Release)        | Draw a permanent arrow between different squares     |
| **Delete Drawing**  | Right Click (On existing)    | Remove a specific arrow or circle                    |
| **Remove Premove**  | Middle Click (On premove)    | Delete a specific queued premove                     |
| **Clear Drawings**  | Middle Click (Empty)         | Clear all arrows, strategy circles, and premoves     |
| **Undo Move**       | Left Arrow Key (Scroll down) | Revert the game state back one move                  |
| **Redo Move**       | Right Arrow Key (Scroll up)  | Re-apply an undone move (within the 3-second window) |

</div>

https://github.com/user-attachments/assets/9413976c-3d58-44f3-9805-79664743cf4e

The video above shows the game reaching an end condition (checkmate in this example) and the game ending.

# Gameplay

1. The player can make premoves by trying to make moves during the bot's turn. To show this a translucent texture of the piece will move to where you moved it. The square where the piece is moved will also turn orange. Multiple premoves can be made and queued. As soon as the bot moves, the first premove in the queue will be played if it is a fully legal move. Premoves can also be removed by middle clicking where the piece moved from then middle clicking where the piece moved to.

2. If the player goes to promote their pawn, a small gui will pop up showing the different pieces they can promote to.
   
3. When the game ends, text will come up on the screen and say which colour won, or what type of end condition was met (e.g: checkmate, stalemate, three fold repetition, etc). Once this text comes up, the player can still undo moves to quickly get back to where they made a bad decision and play something else instead.
   
4. When undoing moves, the player can also redo moves if they realise they would make the same move again, however if paused on the bot's turn, if the move isn't redone before the bot moves, redos can no longer be made.

# Setup

### Prerequisites

- Pygame
  - Can be installed by running `pip install pygame` in cmd.
- Windows ( `.exes` only run on windows )

### Setting up the game

1. Unzip the `chess` folder. 
   
2. Open `settings.json` to change some settings from default
   - `playerColour` is the colour the player plays as. Replace `""` with `white` or `black`. If left as `""` or an invalid input is inputted, a random colour will be chosen.
   - `timeLimit` is the amount of time the bot has to make its move. Input a float / integer for the number of seconds the bot has to move. If left as `""` or an invalid input is inputted, the bot's time to move will default to 3 seconds.
   - `FEN` is where a Forsyth-Edwards Notation (FEN) string can be inputted. If left as `""` or an invalid input is inputted, starting position will default to standard starting position.
3. Launch `ChessBot.exe` to open the game.

<br>

https://github.com/user-attachments/assets/3a4dcf14-77b4-4545-9ca2-905f02fc2c69

The video above shows me changing values in `settings.json` so that I can play the bot from a different position.

# Technical details

The bot includes:

- Bitboards
- Alpha beta pruning
- Iterative deepening
- Move ordering
    1. Previous best move
    2. Promotions
    3. Captures
    4. Killer moves (moves which pruned most branches in search so far)
    5. Quiet moves (ordered based off decaying history table. History assigns value to all moves based off amount of prunes they have caused ever)
- Principal variation search
- Late move reductions
- Transposition tables
- Aspiration windows
- Null move pruning
- Move evaluation (based off material difference + positional bonuses)

# Demo

https://github.com/user-attachments/assets/f02f9ad8-55f1-44e9-9e1a-dadd9f4fec8f

The video above shows me changing the start settings of the bot by changing some of the values in the `settings.json` file then playing the bot from a non standard starting position

https://github.com/user-attachments/assets/184d618d-a614-4815-8fad-4219a093bf67

The video above shows me playing a full game with the bot. Some of the input variables were left empty to show that the program can deal with this and defaults to standard settings.
