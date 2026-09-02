import sys
import os
import pygame
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Tells python to search other folders for files

# Initialises pygame

pygame.init()
pygame.mixer.init()
pygame.display.set_mode((800, 800))

# Imports other project files

from engine import visuals, constants, inputHandler, logic
import bot.bot
import bot.evaluation

class mainLoop:

    # Creates these variables on startup

    def __init__(self):
        self.bestMove = None
        self.searching = False
        self.searchThread = None
        self.board = logic.logic() # This the object that everything in logic.py is part of
        self.board.createSquareTable()
        self.board.positionHistory.append(self.board.hash)
        self.botCooldownUntil = 0
        self.running = True
        self.searchedDepth = None
        self.currentGameOverMessage = None
        if self.board.loadFEN(constants.fen):
            print("FEN string loaded!")
        else:
            print("Invalid FEN string. Defaulting to standard starting position")
            self.board.loadFEN("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    def executePremove(self):
        startRow, startColumn, endRow, endColumn = constants.premove.pop(0)
        piece = self.board.squarePiece[startRow * 8 + startColumn]
        playerColour = constants.white if constants.botColour == constants.black else constants.black
        if piece != constants.empty and (piece & 24) == playerColour:
            moves = self.board.fullyLegalMove(startRow, startColumn)
            if (endRow, endColumn) in moves:
                self.board.makeMove(startRow, startColumn, endRow, endColumn)
                self.board.gameState()
                print(f"Move: {self.board.moves:>3} | Evaluation Score: {self.board.evaluationScore:>5} | Time:   0.00 seconds | Depth: N/A | Endgame: {str(bot.evaluation.isEndgame(self.board)):>5} | Total pieces: {self.board.totalPieces:>2}")
            else:
                constants.premove.clear()
        else:
            constants.premove.clear()

    def searchMove(self, hash, boardCopy):
        calculatedMove, searchedDepth = bot.bot.findBestMove(boardCopy, 20, constants.botColour, pygame.time.get_ticks(), constants.timeLimit * 1000) # Gets the best move from bot.py with a max search depth of 10
        if self.searching and self.board.hash == hash: # Makes sure that best move is only assigned if the bot is supposed to be searching and the current board hash is the same hash as when the search started.
            self.bestMove = calculatedMove
            self.searchedDepth = searchedDepth
        self.searching = False

    def runBotTurn(self, board): 
        if self.bestMove is None and not self.searching:
            if self.searchThread and self.searchThread.is_alive():  # Makes sure that only 1 search thread is alive at a time
                return False
            self.searching = True
            self.botCooldownUntil = pygame.time.get_ticks() + (constants.timeLimit * 1000)
            constants.abortSearch = False
            self.searchThread = threading.Thread(target=self.searchMove, args=(board.hash, board.clone()), daemon=True) # Creates a thread to find best move so that it doesn't freeze on the bot's turn
            self.searchThread.start()

        # Makes the bot's move after enough time has passed

        if self.bestMove is not None and pygame.time.get_ticks() > self.botCooldownUntil: # Make sure enough time has passed and the bot is allowed to move
            startRow, startColumn, endRow, endColumn = self.bestMove
            piece = board.squarePiece[startRow * 8 + startColumn]
            if piece != constants.empty and (piece & 24) == constants.botColour:
                board.makeMove(startRow, startColumn, endRow, endColumn)
                board.gameState() # Checks if the game is over
                time = pygame.time.get_ticks() - self.botCooldownUntil + (constants.timeLimit * 1000)
                constants.playerTimeStart = pygame.time.get_ticks()
                print(f"Move: {board.moves:>3} | Evaluation Score: {board.evaluationScore:>5} | Time: {time / 1000:>6.2f} seconds | Depth: {self.searchedDepth:>3} | Endgame: {str(bot.evaluation.isEndgame(board)):>5} | Total pieces: {board.totalPieces:>2}")
                if len(constants.premove) > 0:
                    self.executePremove()
            self.bestMove = None
            return True
            
        return False

    def draw(self):
        visuals.drawBoard(self.board) # Updates board to have pieces in correct positions after move
        visuals.drawHighlights(self.board) # Draws the circles where the piece can move
        visuals.drawArrows() # Draws the arrows the user has made

        if self.board.gameOverMessage: 
            gamelines = self.board.gameOverMessage.split("\n")
            renderedLines = []
            totalHeight = 0
            for line in gamelines:
                surface, rectangle = visuals.gameFont.render(line, fgcolor=(255, 0, 0), style=pygame.freetype.STYLE_STRONG) # Creates an item that has the text
                renderedLines.append((surface, rectangle)) # Appends the item as a tuple to an array
                totalHeight += rectangle.height + 8 # Adjusts height depending on lines in the message

            bgSurface = pygame.Surface((constants.windowSize, constants.windowSize), pygame.SRCALPHA)
            bgSurface.fill((0, 0, 0, 150)) # Makes the background darker so the text is more visible. 150 is the alpha value
            visuals.screen.blit(bgSurface, (0, 0))

            currentY = (constants.windowSize - totalHeight) / 2
            for surface, rectangle in renderedLines:
                rectangle.centerx = constants.windowSize / 2 # Centres the text horizontally
                rectangle.y = currentY # Top left of the text
                visuals.screen.blit(surface, rectangle) # Writes the text
                currentY += rectangle.height + 8 # Updates y value so that next line is written below

        if self.board.gameOverMessage != self.currentGameOverMessage:
            self.currentGameOverMessage = self.board.gameOverMessage
            print(f"Average player time: {(constants.playerTotalTime / max(1, self.board.moves / 2)) / 1000 : .2f} seconds")
            print(f"Average bot time: {constants.timeLimit : .2f} seconds")

        pygame.display.flip() # Updates the screen
        visuals.redraw = False # Changes redraw to false so that the screen is only redrawn when a change happens

    def run(self):
        while self.running:
            inputHandler.handleInputs(self, self.board) # Lets inputHandler deal with inputs
            if visuals.redraw:
                self.draw()
            if self.board.turnColour == constants.botColour and not self.board.gameOverMessage: # Makes sure the bot only plays on its turn and not after the game has ended
                self.runBotTurn(self.board)

            visuals.clock.tick(60) # Runs in 60 frames per second

if __name__ == "__main__": # Only run when it the file is being run not when imported
    main = mainLoop() # Object that everything else was in
    main.run() # Starts the while loop in run()

pygame.quit()