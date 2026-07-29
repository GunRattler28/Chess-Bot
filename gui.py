import pygame
import pygame.freetype
import math
import moveGeneration
import moveExecution
import updateBoard

pygame.init()
pygame.mixer.init()
pygame.key.set_repeat(300, 25)

redraw = True
windowSize = 800
positionSize = windowSize / 8
screen = pygame.display.set_mode((windowSize, windowSize))
pygame.display.set_caption("Gun's Chess Bot")
icon = pygame.image.load('images/icon.png')
pygame.display.set_icon(icon)
clock = pygame.time.Clock()
pygame.font.init()
gameFont = pygame.freetype.SysFont("dynapuffregular", 64, bold=True) 

promotionActive = False
activeOutline = None
activeSquare = None
moveIndicator = []
possibleMoves = []
lines = []
rightClickStart = None
temporaryLine = None
strategyCircles = []

pieces = {
    "bQ": pygame.transform.scale(pygame.image.load("images/pieces/bqueen.png").convert_alpha(), (positionSize, positionSize)),
    "bK": pygame.transform.scale(pygame.image.load("images/pieces/bking.png").convert_alpha(), (positionSize, positionSize)),
    "bB": pygame.transform.scale(pygame.image.load("images/pieces/bbishop.png").convert_alpha(), (positionSize, positionSize)),
    "bH": pygame.transform.scale(pygame.image.load("images/pieces/bhorse.png").convert_alpha(), (positionSize, positionSize)),
    "bR": pygame.transform.scale(pygame.image.load("images/pieces/brook.png").convert_alpha(), (positionSize, positionSize)),
    "bP": pygame.transform.scale(pygame.image.load("images/pieces/bpawn.png").convert_alpha(), (positionSize, positionSize)),
    "wQ": pygame.transform.scale(pygame.image.load("images/pieces/wqueen.png").convert_alpha(), (positionSize, positionSize)), 
    "wK": pygame.transform.scale(pygame.image.load("images/pieces/wking.png").convert_alpha(), (positionSize, positionSize)),
    "wB": pygame.transform.scale(pygame.image.load("images/pieces/wbishop.png").convert_alpha(), (positionSize, positionSize)),
    "wH": pygame.transform.scale(pygame.image.load("images/pieces/whorse.png").convert_alpha(), (positionSize, positionSize)),
    "wR": pygame.transform.scale(pygame.image.load("images/pieces/wrook.png").convert_alpha(), (positionSize, positionSize)),
    "wP": pygame.transform.scale(pygame.image.load("images/pieces/wpawn.png").convert_alpha(), (positionSize, positionSize))
}

overlays = {
    "red": pygame.transform.scale(pygame.image.load("images/redOverlay.png").convert_alpha(), (positionSize, positionSize)),
    "green": pygame.transform.scale(pygame.image.load("images/greenOverlay.png").convert_alpha(), (positionSize, positionSize))
}

sounds = {
    "move": pygame.mixer.Sound("sounds/Move.mp3"),
    "capture": pygame.mixer.Sound("sounds/Capture.mp3"),
    "check": pygame.mixer.Sound("sounds/Check.mp3"),
    "checkmate": pygame.mixer.Sound("sounds/Checkmate.mp3"),
}

def drawBoard():
    for column in range(0, 8):
        for row in range(0, 8):
            if ((row + column) % 2 == 0):
                pygame.draw.rect(screen, "#ffffff", (column * positionSize, row * positionSize, positionSize, positionSize))
            else:
                pygame.draw.rect(screen, "#0088ff", (column * positionSize, row * positionSize, positionSize, positionSize))

            piece = updateBoard.getPiece(row, column)
            if (piece != ""):
                screen.blit(pieces[piece], (column * positionSize, row * positionSize))

def onClick(x, y):
    global activeOutline, activeSquare, possibleMoves, promotionActive, lines, strategyCircles, redraw

    if promotionActive:
        return

    if len(lines) > 0 or len(strategyCircles):
        clearArrows()

    row = int(y // positionSize)
    column = int(x // positionSize)

    if activeSquare == None:
        handleSelection(row, column)
        return

    startRow = activeSquare[0]
    startColumn = activeSquare[1]

    if (row, column) in possibleMoves:
        moveExecution.makeMove(startRow, startColumn, row, column)
        moveExecution.gameState()
        print(updateBoard.moves)
    else:
        handleSelection(row, column)

def handleSelection(row, column):
    global redraw, activeSquare, activeOutline, possibleMoves

    piece = updateBoard.getPiece(row, column)

    if piece == "" or piece[0] != updateBoard.turnColour:
        activeSquare = None
        activeOutline = None
        possibleMoves.clear()
        redraw = True
        return

    activeSquare = [row, column]
    possibleMoves = moveGeneration.blockCheck(row, column)
    redraw = True

def blur_surface(surface, scale_factor=3):
    if scale_factor <= 1:
        return surface.copy()

    width = max(1, int(surface.get_width() / scale_factor))
    height = max(1, int(surface.get_height() / scale_factor))
    scaled = pygame.transform.smoothscale(surface, (width, height))
    return pygame.transform.smoothscale(scaled, surface.get_size())

def choosePromotion(colour):
    global promotionActive
    promotionActive = True
    piecesToChoose = ["Q", "H", "R", "B"]
    
    menuWidth = positionSize * 4
    menuX = (windowSize - menuWidth) // 2
    menuY = (windowSize - positionSize) // 2

    background = screen.copy()
    blurredBackground = blur_surface(background, 3)
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 90))
    
    chosenPiece = None
    
    while promotionActive:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouseX, mouseY = event.pos
                if menuY <= mouseY <= menuY + positionSize:
                    if menuX <= mouseX <= menuX + menuWidth:
                        index = int((mouseX - menuX) // positionSize)
                        chosenPiece = colour + piecesToChoose[index]
                        promotionActive = False

        screen.blit(blurredBackground, (0, 0))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (255, 255, 255), (menuX, menuY, menuWidth, positionSize))
        pygame.draw.rect(screen, (0, 0, 0), (menuX, menuY, menuWidth, positionSize), 4)
        
        for i, piece in enumerate(piecesToChoose):
            screen.blit(pieces[colour + piece], (menuX + (i * positionSize), menuY))
            
        pygame.display.flip()
        clock.tick(60)
        
    return chosenPiece

def clearArrows():
    global redraw, lines, strategyCircles
    strategyCircles.clear()
    lines.clear()
    redraw = True

def onRightClick(x, y):
    global rightClickStart
    if promotionActive: 
        return
    rightClickStart = (int(y // positionSize), int(x // positionSize))

def onRightDrag(x, y):
    global redraw, temporaryLine
    if rightClickStart:
        temporaryLine = (x, y)
    redraw = True

def onRightRelease(x, y):
    global redraw, rightClickStart, temporaryLine
    if not rightClickStart: 
        return

    endRow, endColumn = int(y // positionSize), int(x // positionSize)
    startRow, startColumn = rightClickStart
    
    if 0 <= endRow < 8 and 0 <= endColumn < 8:
        if (startRow, startColumn) == (endRow, endColumn):
            if (startRow, startColumn) in strategyCircles:
                strategyCircles.remove((endRow, endColumn))
            else:
                strategyCircles.append((endRow, endColumn))
        else:
            lines.append(((startRow, startColumn), (endRow, endColumn)))

    rightClickStart = None
    temporaryLine = None
    redraw = True

def drawHighlights():
    if activeSquare:
        r, c = activeSquare
        pygame.draw.rect(screen, (0, 255, 0), (c * positionSize, r * positionSize, positionSize, positionSize), 4)

    for moveRow, moveColumn in possibleMoves:
        x, y = moveColumn * positionSize, moveRow * positionSize
        if updateBoard.getPiece(moveRow, moveColumn) != "":
            screen.blit(overlays["red"], (x, y))
        else:
            screen.blit(overlays["green"], (x, y))

    if moveGeneration.kingCheck(updateBoard.turnColour):
        king = moveGeneration.findKing(updateBoard.turnColour)
        if king:
            screen.blit(overlays["red"], (king[1] * positionSize, king[0] * positionSize))

def squareCenter(square):
    row, column = square
    offset = positionSize / 2
    return (column * positionSize + offset, row * positionSize + offset)

def drawArrow(surface, color, start, end, thickness=25, arrowSize=50):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return

    direction = (dx / length, dy / length)
    perpendicular = (-direction[1], direction[0])
    shaft_end = (
        end[0] - direction[0] * (arrowSize * 0.6),
        end[1] - direction[1] * (arrowSize * 0.6),
    )
    radius = thickness / 2

    positionStartA = (start[0] + perpendicular[0] * radius, start[1] + perpendicular[1] * radius)
    positionStartB = (start[0] - perpendicular[0] * radius, start[1] - perpendicular[1] * radius)
    positionEndA = (shaft_end[0] + perpendicular[0] * radius, shaft_end[1] + perpendicular[1] * radius)
    positionEndB = (shaft_end[0] - perpendicular[0] * radius, shaft_end[1] - perpendicular[1] * radius)

    pygame.draw.circle(surface, color, start, radius)
    pygame.draw.polygon(surface, color, [positionStartA, positionEndA, positionEndB, positionStartB])

    rotation = math.atan2(dy, dx)
    p1 = (end[0] - arrowSize * math.cos(rotation + math.pi / 4), end[1] - arrowSize * math.sin(rotation + math.pi / 4))
    p2 = (end[0] - arrowSize * math.cos(rotation - math.pi / 4), end[1] - arrowSize * math.sin(rotation - math.pi / 4))
    pygame.draw.polygon(surface, color, [end, p1, p2])

def drawArrows():
    for row, column in strategyCircles:
        screen.blit(overlays["green"], (column * positionSize, row * positionSize))

    arrowSurf = pygame.Surface((windowSize, windowSize), pygame.SRCALPHA)
    arrowColor = (0, 255, 0, 150)

    for startSquare, endSquare in lines:
        drawArrow(arrowSurf, arrowColor, squareCenter(startSquare), squareCenter(endSquare))

    if rightClickStart and temporaryLine:
        drawArrow(arrowSurf, (0, 187, 0, 150), squareCenter(rightClickStart), temporaryLine)

    screen.blit(arrowSurf, (0, 0))