import sys
import os
import pygame

pygame.init()
pygame.mixer.init()
pygame.display.set_mode((800, 800)) 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
from engine import visuals, inputHandler, logic, constants
from bot import bot
from bot.modules import material

class mainLoop:
    def __init__(self):
        self.bestMove = None
        self.searching = False
        self.searchThread = None
        self.board = logic.logic()
        self.board.updateSquareTable()
        self.board.positionHistory.append(self.board.zobristHash())
        self.botCooldownUntil = 0
        self.running = True

    def searchMove(self, currentMoveCount):
        boardCopy = self.board.clone()
        calculatedMove = bot.findBestMove(boardCopy, 5, constants.botColour)
        if self.searching and self.board.moves == currentMoveCount:
            self.bestMove = calculatedMove
        self.searching = False

    def runBotTurn(self, board): 
        if self.bestMove is None and not self.searching:
            self.searching = True
            self.botCooldownUntil = pygame.time.get_ticks() + 3000
            self.searchThread = threading.Thread(target=self.searchMove, args=(board.moves,), daemon=True)
            self.searchThread.start()

        if self.bestMove is not None and pygame.time.get_ticks() > self.botCooldownUntil:
            startRow, startCol, endRow, endCol = self.bestMove
            piece = board.squarePiece[startRow * 8 + startCol]
            if piece != constants.empty and (piece & 24) == constants.botColour:
                board.makeMove(startRow, startCol, endRow, endCol)
                board.gameState()
                time = pygame.time.get_ticks() - self.botCooldownUntil + 3000
                constants.playerTimeStart = pygame.time.get_ticks()
                print(f"Move: {board.moves} Material Difference: {material.materialDif(board.piecePositions)} Time: {time / 1000 : .2f} seconds")
                constants.botTotalTime += time

            self.bestMove = None
            return True
            
        return False

    def draw(self):
        visuals.drawBoard(self.board)
        visuals.drawHighlights(self.board)
        visuals.drawArrows()
        
        if self.board.gameOverMessage:
            gamelines = self.board.gameOverMessage.split("\n")
            renderedLines = []
            totalHeight = 0
            
            for line in gamelines:
                surface, rectangle = visuals.gameFont.render(line, fgcolor=(255, 0, 0), style=pygame.freetype.STYLE_STRONG)
                renderedLines.append((surface, rectangle))
                totalHeight += rectangle.height + 8

            bgSurface = pygame.Surface((constants.windowSize, constants.windowSize), pygame.SRCALPHA)
            bgSurface.fill((0, 0, 0, 150))
            visuals.screen.blit(bgSurface, (0, 0))

            currentY = (constants.windowSize - totalHeight) / 2
            for surface, rectangle in renderedLines:
                rectangle.centerx = constants.windowSize / 2

                rectangle.y = currentY
                visuals.screen.blit(surface, rectangle)
                currentY += rectangle.height + 8

        pygame.display.flip()
        visuals.redraw = False

    def run(self):
        while self.running:
            inputHandler.handleInputs(self, self.board)
            if visuals.redraw:
                self.draw()
            if self.board.turnColour == constants.botColour and not self.board.gameOverMessage:
                self.runBotTurn(self.board)

            visuals.clock.tick(60)    

if __name__ == "__main__":
    main = mainLoop()
    main.run()

pygame.quit()