import pygame
import moveGeneration
import moveExecution
import updateBoard
import gui

updateBoard.updateSquareTable()
startHash = updateBoard.hashBoard()
updateBoard.positionHistory.append(startHash)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
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
            if event.key == pygame.K_LEFT:
                moveExecution.previousMove()
            elif event.key == pygame.K_RIGHT:
                moveExecution.redoMove()

    if gui.redraw:
        gui.screen.fill((255, 255, 255))
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

    gui.clock.tick(60)    

pygame.quit()