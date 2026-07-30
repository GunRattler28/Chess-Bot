import pygame
import moveExecution
import updateBoard
import gui
import bot
import threading

global bestMove
bestMove = None
global searching
searching = False
global searchThread
searchThread = None

updateBoard.updateSquareTable()
startHash = updateBoard.hashBoard()
updateBoard.positionHistory.append(startHash)

botColour = "b"
botCooldownUntil = 0

def searchMove():
    global bestMove
    global searching

    bestMove = bot.findBestMove(4, botColour)
    searching = False

def runBotTurn():
    global bestMove
    global searching
    global searchThread

    if bestMove is None and not searching:
        searching = True
        searchThread = threading.Thread(target=searchMove, daemon=True)
        searchThread.start()

    if pygame.time.get_ticks() > botCooldownUntil:
        if bestMove is None:
            return False
        startRow, startCol, endRow, endCol = bestMove
        moveExecution.makeMove(startRow, startCol, endRow, endCol)
        moveExecution.gameState()
        print(f"Move: {updateBoard.moves} Material Difference: {bot.materialDif()}")
        bestMove = None
        return True
    else:
        return False

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and not searching:
                gui.onClick(event.pos[0], event.pos[1]) 
            elif event.button == 3:
                gui.onRightClick(event.pos[0], event.pos[1])
                 
        elif event.type == pygame.MOUSEMOTION:
            if gui.rightClickStart:
                gui.onRightDrag(event.pos[0], event.pos[1])
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                gui.onRightRelease(event.pos[0], event.pos[1])
                
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT and not searching:
                moveExecution.previousMove()
                botCooldownUntil = pygame.time.get_ticks() + 3000
                bestMove = None
            elif event.key == pygame.K_RIGHT and not searching:
                moveExecution.redoMove()
                botCooldownUntil = pygame.time.get_ticks() + 3000
                bestMove = None

    if gui.redraw:
        gui.drawBoard()
        gui.drawHighlights()
        gui.drawArrows()
        
        if updateBoard.gameOverMessage:
            gamelines = updateBoard.gameOverMessage.split("\n")
            renderedLines = []
            totalHeight = 0
            
            for line in gamelines:
                surf, rect = gui.gameFont.render(line, fgcolor=(255, 0, 0), style=pygame.freetype.STYLE_STRONG)
                renderedLines.append((surf, rect))
                totalHeight += rect.height + 8

            bgSurface = pygame.Surface((gui.windowSize, gui.windowSize), pygame.SRCALPHA)
            bgSurface.fill((0, 0, 0, 150))
            gui.screen.blit(bgSurface, (0, 0))

            current_y = (gui.windowSize - totalHeight) / 2
            for surf, rect in renderedLines:
                rect.centerx = gui.windowSize / 2
                rect.y = current_y
                gui.screen.blit(surf, rect)
                current_y += rect.height + 8

        pygame.display.flip()
        gui.redraw = False

    if updateBoard.turnColour == botColour and not updateBoard.gameOverMessage:
        runBotTurn()

    gui.clock.tick(60)    

pygame.quit()