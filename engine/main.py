import sys
import os
import pygame

pygame.init()
pygame.mixer.init()
pygame.display.set_mode((800, 800)) 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
from engine import visuals, inputHandler, logic, constants
from engine.constants import botColour
from bot import bot

global bestMove
bestMove = None
global searching
searching = False
global searchThread
searchThread = None

logic.updateSquareTable()
startHash = logic.hashBoard()
logic.positionHistory.append(startHash)

botCooldownUntil = 0

def searchMove():
    global bestMove, searching
    bestMove = bot.findBestMove(4, botColour)
    searching = False

def runBotTurn():
    global bestMove, searching, searchThread

    if bestMove is None and not searching:
        searching = True
        searchThread = threading.Thread(target=searchMove, daemon=True)
        searchThread.start()

    if pygame.time.get_ticks() > botCooldownUntil:
        if bestMove is None: return False
        
        startRow, startCol, endRow, endCol = bestMove
        logic.makeMove(startRow, startCol, endRow, endCol)
        logic.gameState()
        print(f"Move: {logic.moves} Material Difference: {bot.materialDif()}")
        bestMove = None
        return True
    return False

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and not searching: inputHandler.onClick(event.pos[0], event.pos[1]) 
            elif event.button == 3: inputHandler.onRightClick(event.pos[0], event.pos[1])
                 
        elif event.type == pygame.MOUSEMOTION:
            if visuals.rightClickStart: inputHandler.onRightDrag(event.pos[0], event.pos[1])
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3: inputHandler.onRightRelease(event.pos[0], event.pos[1])
                
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT and not searching:
                logic.previousMove()
                botCooldownUntil = pygame.time.get_ticks() + 3000
                bestMove = None
            elif event.key == pygame.K_RIGHT and not searching:
                logic.redoMove()
                botCooldownUntil = pygame.time.get_ticks() + 3000
                bestMove = None

    if visuals.redraw and not searching:
        visuals.drawBoard()
        visuals.drawHighlights()
        visuals.drawArrows()
        
        if logic.gameOverMessage:
            gamelines = logic.gameOverMessage.split("\n")
            renderedLines = []
            totalHeight = 0
            
            for line in gamelines:
                surf, rect = visuals.gameFont.render(line, fgcolor=(255, 0, 0), style=pygame.freetype.STYLE_STRONG)
                renderedLines.append((surf, rect))
                totalHeight += rect.height + 8

            bgSurface = pygame.Surface((constants.windowSize, constants.windowSize), pygame.SRCALPHA)
            bgSurface.fill((0, 0, 0, 150))
            visuals.screen.blit(bgSurface, (0, 0))

            currentY = (constants.windowSize - totalHeight) / 2
            for surf, rect in renderedLines:
                rect.centerx = constants.windowSize / 2
                rect.y = currentY
                visuals.screen.blit(surf, rect)
                currentY += rect.height + 8

        pygame.display.flip()
        visuals.redraw = False

    if logic.turnColour == botColour and not logic.gameOverMessage:
        runBotTurn()

    visuals.clock.tick(60)    

pygame.quit()