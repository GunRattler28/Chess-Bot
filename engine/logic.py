from engine.constants import rookDirections, bishopDirections, queenDirections, knightAtk, kingAtk, sounds, botColour

class logic:
    def __init__(self):
        self.gameOverMessage = None
        self.moves = 0
        self.halfmoveClock = 0
        self.turnColour = "w"
        self.moveHistory = []
        self.redoHistory = []
        self.positionHistory = []
        self.squarePiece = [""] * 64
        self.enPassantTarget = None

        self.piecePositions = {
            "bQ": 0x0000000000000008, 
            "bK": 0x0000000000000010, 
            "bB": 0x0000000000000024,
            "bH": 0x0000000000000042, 
            "bR": 0x0000000000000081, 
            "bP": 0x000000000000FF00,
            "wQ": 0x0800000000000000, 
            "wK": 0x1000000000000000, 
            "wB": 0x2400000000000000,
            "wH": 0x4200000000000000, 
            "wR": 0x8100000000000000, 
            "wP": 0x00FF000000000000
        }

        self.castleRights = {
            "wKl": True, 
            "wK": True, 
            "wKr": True,
            "bKl": True, 
            "bK": True, 
            "bKr": True,
        }

    def clone(self):
        newState = logic()
        newState.moves = self.moves
        newState.halfmoveClock = self.halfmoveClock
        newState.turnColour = self.turnColour
        newState.enPassantTarget = self.enPassantTarget
        newState.gameOverMessage = self.gameOverMessage
        newState.piecePositions = self.piecePositions.copy()
        newState.castleRights = self.castleRights.copy()
        newState.squarePiece = self.squarePiece.copy()
        newState.moveHistory = self.moveHistory.copy()
        newState.redoHistory = self.redoHistory.copy()
        newState.positionHistory = self.positionHistory.copy()
        
        return newState

    def setPiece(self, row, column, piece):
        if not (0 <= row < 8 and 0 <= column < 8): 
            return
        self.squarePiece[row * 8 + column] = piece

    def updateSquareTable(self):
        self.squarePiece = [""] * 64
        for piece, bitboard in self.piecePositions.items():
            board = int(bitboard)
            while board:
                lsb = board & -board
                index = lsb.bit_length() - 1
                self.squarePiece[index] = piece
                board &= board - 1

    def getOccupied(self):
        whiteOccupied, blackOccupied = 0, 0
        for name, bitboard in self.piecePositions.items():
            if name[0] == "w": 
                whiteOccupied |= bitboard
            else: 
                blackOccupied |= bitboard
        return (whiteOccupied, blackOccupied, whiteOccupied | blackOccupied)

    def hashBoard(self):
        return hash((tuple(self.piecePositions.values()), self.turnColour, tuple(self.castleRights.values()), self.enPassantTarget))

    def slidingMoves(self, row, column, movements, friendlyOccupied, occupied, possibleMoves):
        for rowChange, columnChange in movements:
            potRow, potColumn = row + rowChange, column + columnChange
            while 0 <= potRow < 8 and 0 <= potColumn < 8:
                targetBit = 1 << (potRow * 8 + potColumn)
                if targetBit & friendlyOccupied: 
                    break
                possibleMoves.append((potRow, potColumn))
                if targetBit & occupied: 
                    break
                potRow += rowChange
                potColumn += columnChange

    def instaMoves(self, atkMask, friendOccupied, possibleMoves):
        legalMask = atkMask & ~friendOccupied
        while legalMask:
            lsb = legalMask & -legalMask
            index = lsb.bit_length() - 1
            possibleMoves.append((index // 8, index % 8))
            legalMask &= legalMask - 1

    def isSquareAttacked(self, row, column, atkColour):
        targetIndex = row * 8 + column
        
        if knightAtk[targetIndex] & self.piecePositions[atkColour + "H"]:
            return True
            
        if kingAtk[targetIndex] & self.piecePositions[atkColour + "K"]:
            return True
        
        pawnMask = 0
        if atkColour == "w":
            if row < 7 and column > 0: 
                pawnMask |= 1 << ((row + 1) * 8 + (column - 1))
            if row < 7 and column < 7: 
                pawnMask |= 1 << ((row + 1) * 8 + (column + 1))
        else:
            if row > 0 and column > 0: 
                pawnMask |= 1 << ((row - 1) * 8 + (column - 1))
            if row > 0 and column < 7: 
                pawnMask |= 1 << ((row - 1) * 8 + (column + 1))
            
        if pawnMask & self.piecePositions[atkColour + "P"]:
            return True

        occupied = self.getOccupied()[2]

        for rowChange, columnChange in rookDirections:
            potRow, potColumn = row + rowChange, column + columnChange
            while 0 <= potRow < 8 and 0 <= potColumn < 8:
                testMask = 1 << (potRow * 8 + potColumn)
                if testMask & occupied:
                    if testMask & (self.piecePositions[atkColour + "R"] | self.piecePositions[atkColour + "Q"]):
                        return True
                    break
                potRow += rowChange
                potColumn += columnChange

        for rowChange, columnChange in bishopDirections:
            potRow, potColumn = row + rowChange, column + columnChange
            while 0 <= potRow < 8 and 0 <= potColumn < 8:
                testMask = 1 << (potRow * 8 + potColumn)
                if testMask & occupied:
                    if testMask & (self.piecePositions[atkColour + "B"] | self.piecePositions[atkColour + "Q"]):
                        return True
                    break
                potRow += rowChange
                potColumn += columnChange
        return False

    def findKing(self, colour):
        kingBoard = int(self.piecePositions[colour + "K"])
        if kingBoard == 0: 
            return None
        index = kingBoard.bit_length() - 1
        return (index // 8, index % 8)

    def kingCheck(self, colour):
        king = self.findKing(colour)
        if king is None: 
            return False
        return self.isSquareAttacked(king[0], king[1], "w" if colour == "b" else "b")

    def addCastleMoves(self, pieceColour, possibleMoves):
        row = 7 if pieceColour == "w" else 0
        enemy = "b" if pieceColour == "w" else "w"

        if (self.castleRights[pieceColour + "Kr"] and self.squarePiece[row * 8 + 5] == "" and self.squarePiece[row * 8 + 6] == "" and not self.kingCheck(pieceColour) and not self.isSquareAttacked(row, 5, enemy) and not self.isSquareAttacked(row, 6, enemy) and self.squarePiece[row * 8 + 7] == pieceColour + "R"):
            possibleMoves.append((row, 6))

        if (self.castleRights[pieceColour + "Kl"] and self.squarePiece[row * 8 + 1] == "" and self.squarePiece[row * 8 + 2] == "" and self.squarePiece[row * 8 + 3] == "" and not self.kingCheck(pieceColour) and not self.isSquareAttacked(row, 3, enemy) and not self.isSquareAttacked(row, 2, enemy) and self.squarePiece[row * 8 + 0] == pieceColour + "R"):
            possibleMoves.append((row, 2))

    def calculateLegalMoves(self, row, column, includeCastling):
        possibleMoves = []
        piece = self.squarePiece[row * 8 + column]
        if piece == "": return []

        pieceType, pieceColour = piece[-1], piece[0]
        whiteOccupied, blackOccupied, occupied = self.getOccupied()
        friendlyOccupied = whiteOccupied if pieceColour == "w" else blackOccupied

        if pieceType == "H": 
            self.instaMoves(knightAtk[row * 8 + column], friendlyOccupied, possibleMoves)
        elif pieceType == "K":
            self.instaMoves(kingAtk[row * 8 + column], friendlyOccupied, possibleMoves)
            if includeCastling: self.addCastleMoves(pieceColour, possibleMoves)
        elif pieceType == "R": 
            self.slidingMoves(row, column, rookDirections, friendlyOccupied, occupied, possibleMoves)
        elif pieceType == "B": 
            self.slidingMoves(row, column, bishopDirections, friendlyOccupied, occupied, possibleMoves)
        elif pieceType == "Q": 
            self.slidingMoves(row, column, queenDirections, friendlyOccupied, occupied, possibleMoves)
        elif pieceType == "P":
            direction = -1 if pieceColour == "w" else 1
            potRow = row + direction
            if 0 <= potRow < 8:
                if self.squarePiece[potRow * 8 + column] == "":
                    possibleMoves.append((potRow, column))
                    if pieceColour == "w" and row == 6 and self.squarePiece[(potRow - 1) * 8 + column] == "": possibleMoves.append((potRow - 1, column))
                    elif pieceColour == "b" and row == 1 and self.squarePiece[(potRow + 1) * 8 + column] == "": possibleMoves.append((potRow + 1, column))

            for columnChange in [-1, 1]:
                potRow, potColumn = row + direction, column + columnChange
                if 0 <= potRow < 8 and 0 <= potColumn < 8:
                    target = self.squarePiece[potRow * 8 + potColumn]
                    if target != "" and target[0] != pieceColour: possibleMoves.append((potRow, potColumn))
                    elif self.enPassantTarget == (potRow, potColumn): possibleMoves.append((potRow, potColumn))

        return possibleMoves

    def blockCheck(self, row, column):
        piece = self.squarePiece[row * 8 + column]
        if piece == "": return []
        validMoves = []
        
        for endRow, endColumn in self.calculateLegalMoves(row, column, True):
            targetPiece = self.squarePiece[endRow * 8 + endColumn]
            capturedSquare = None
            capturedPiece = targetPiece

            if piece[-1] == "P" and targetPiece == "" and column != endColumn:
                if self.enPassantTarget == (endRow, endColumn):
                    capturedSquare = (endRow - (-1 if piece[0] == "w" else 1), endColumn)
                    capturedPiece = self.squarePiece[capturedSquare[0] * 8 + capturedSquare[1]]

            self.simulateMove(piece, (row, column), (endRow, endColumn), capturedPiece, capturedSquare)
            if not self.kingCheck(piece[0]): validMoves.append((endRow, endColumn))
            self.undoMove(piece, (row, column), (endRow, endColumn), capturedPiece, capturedSquare)

        return validMoves

    def legalMoves(self, colour):
        for piece, bitboard in self.piecePositions.items():
            if piece[0] == colour:
                board = bitboard
                while board:
                    lsb = board & -board
                    index = lsb.bit_length() - 1
                    if self.blockCheck(index // 8, index % 8): 
                        return True
                    board &= board - 1
        return False

    def isPromotable(self, piece, row):
        return (piece == "wP" and row == 0) or (piece == "bP" and row == 7)

    def insufficientMat(self):
        if (self.piecePositions["bP"] or self.piecePositions["bR"] or self.piecePositions["bQ"] or self.piecePositions["wP"] or self.piecePositions["wR"] or self.piecePositions["wQ"]): return False
        totKnights = int(self.piecePositions["bH"]).bit_count() + int(self.piecePositions["wH"]).bit_count()
        totBishops = int(self.piecePositions["bB"]).bit_count() + int(self.piecePositions["wB"]).bit_count()
        return (totBishops + totKnights) < 2

    def moveCastleRook(self, piece, start, end, undo=False):
        if piece not in ("wK", "bK"): 
            return
        row = 7 if piece == "wK" else 0

        if start == (row, 4) and end == (row, 6): 
            if undo:
                rookStart, rookEnd = ((row, 5), (row, 7)) 
            else:
                rookStart, rookEnd = ((row, 7), (row, 5))
        elif start == (row, 4) and end == (row, 2):  
            if undo:
                rookStart, rookEnd = ((row, 3), (row, 0))
            else:
                rookStart, rookEnd = ((row, 0), (row, 3))
        else: 
            return

        self.piecePositions[piece[0] + "R"] &= ~(1 << (rookStart[0] * 8 + rookStart[1]))
        self.piecePositions[piece[0] + "R"] |= 1 << (rookEnd[0] * 8 + rookEnd[1])
        self.setPiece(rookStart[0], rookStart[1], "")
        self.setPiece(rookEnd[0], rookEnd[1], piece[0] + "R")

    def simulateMove(self, piece, start, end, captured, capturedSquare=None):
        if captured:
            if capturedSquare:
                self.piecePositions[captured] &= ~(1 << (capturedSquare[0] * 8 + capturedSquare[1]))
                self.setPiece(capturedSquare[0], capturedSquare[1], "")
            else:
                self.piecePositions[captured] &= ~(1 << (end[0] * 8 + end[1]))
                self.setPiece(end[0], end[1], "")

        self.piecePositions[piece] &= ~(1 << (start[0] * 8 + start[1]))
        self.piecePositions[piece] |= 1 << (end[0] * 8 + end[1])
        self.setPiece(start[0], start[1], "")
        self.setPiece(end[0], end[1], piece)

        if piece in ("wK", "bK"): self.moveCastleRook(piece, start, end)

    def undoMove(self, piece, start, end, captured, capturedSquare=None):
        self.piecePositions[piece] &= ~(1 << (end[0] * 8 + end[1]))
        self.piecePositions[piece] |= (1 << (start[0] * 8 + start[1]))

        if captured:
            if capturedSquare:
                self.piecePositions[captured] |= 1 << (capturedSquare[0] * 8 + capturedSquare[1])
                self.setPiece(capturedSquare[0], capturedSquare[1], captured)
            else:
                self.piecePositions[captured] |= (1 << (end[0] * 8 + end[1]))
                self.setPiece(end[0], end[1], captured)

        self.setPiece(start[0], start[1], piece)
        if not captured or (captured and capturedSquare):
            self.setPiece(end[0], end[1], "" if captured and capturedSquare else (captured or ""))

        if piece in ("wK", "bK"): self.moveCastleRook(piece, start, end, undo=True)

    def makeMove(self, startRow, startColumn, endRow, endColumn, sound=True, simulation=False):
        from engine import visuals
        
        movingPiece = self.squarePiece[startRow * 8 + startColumn]
        target = self.squarePiece[endRow * 8 + endColumn]
        targetPos = 1 << (endRow * 8 + endColumn)
        start, end = (startRow, startColumn), (endRow, endColumn)

        turnColourBefore = self.turnColour
        movesBefore = self.moves
        halfmoveClockBefore = self.halfmoveClock
        enPassantBefore = self.enPassantTarget
        castleRights = self.castleRights
        castleRightsBefore = (castleRights["wKl"], castleRights["wK"], castleRights["wKr"], castleRights["bKl"], castleRights["bK"], castleRights["bKr"])
        capturedPiece = target
        capturedSquare = None
        promotion = None

        self.moveCastleRook(movingPiece, start, end)
        
        if movingPiece == "wK": 
            self.castleRights["wK"] = self.castleRights["wKl"] = self.castleRights["wKr"] = False
        elif movingPiece == "bK": 
            self.castleRights["bK"] = self.castleRights["bKl"] = self.castleRights["bKr"] = False
        elif movingPiece == "wR":
            if start == (7, 0): 
                self.castleRights["wKl"] = False
            elif start == (7, 7): 
                self.castleRights["wKr"] = False
        elif movingPiece == "bR":
            if start == (0, 0): 
                self.castleRights["bKl"] = False
            elif start == (0, 7): 
                self.castleRights["bKr"] = False

        if target == "wR":
            if end == (7, 0): 
                self.castleRights["wKl"] = False
            elif end == (7, 7): 
                self.castleRights["wKr"] = False
        elif target == "bR":
            if end == (0, 0): 
                self.castleRights["bKl"] = False
            elif end == (0, 7): 
                self.castleRights["bKr"] = False

        if not simulation:
            visuals.possibleMoves.clear()
            self.redoHistory.clear()

        enPassantCapture = False

        if movingPiece[-1] == "P" and target == "" and startColumn != endColumn and self.enPassantTarget == (endRow, endColumn):
            capturedRow = endRow - (-1 if movingPiece[0] == "w" else 1)
            capturedPiece = self.squarePiece[capturedRow * 8 + endColumn]
            if capturedPiece != "":
                self.piecePositions[capturedPiece] &= ~(1 << (capturedRow * 8 + endColumn))
                self.setPiece(capturedRow, endColumn, "")
                capturedSquare = (capturedRow, endColumn)
                enPassantCapture = True
                if sound: sounds["capture"].play()

        if not enPassantCapture:
            if target != "":
                self.piecePositions[target] &= ~targetPos
                self.setPiece(endRow, endColumn, "")
                if sound: sounds["capture"].play()
            else:
                if sound: sounds["move"].play()

        self.piecePositions[movingPiece] &= ~(1 << (startRow * 8 + startColumn))
        self.piecePositions[movingPiece] |= targetPos
        self.setPiece(startRow, startColumn, "")
        self.setPiece(endRow, endColumn, movingPiece)

        if self.isPromotable(movingPiece, endRow):
            if simulation or self.turnColour == botColour:
                promotedPiece = self.turnColour + "Q"
            else:
                promotedPiece = visuals.choosePromotion(self.turnColour)
            
            self.piecePositions[movingPiece] &= ~targetPos
            self.piecePositions[promotedPiece] |= targetPos
            self.setPiece(endRow, endColumn, promotedPiece)
            promotion = promotedPiece

        self.enPassantTarget = ((startRow + endRow) // 2, startColumn) if movingPiece[-1] == "P" and abs(endRow - startRow) == 2 else None
        self.turnColour = "b" if self.turnColour == "w" else "w"    
        self.moves += 1
        self.halfmoveClock = 0 if movingPiece[-1] == "P" or target != "" or enPassantCapture else self.halfmoveClock + 1
        castleRightsAfter = (castleRights["wKl"], castleRights["wK"], castleRights["wKr"], castleRights["bKl"], castleRights["bK"], castleRights["bKr"])
        self.moveHistory.append((
            movingPiece, 
            start, 
            end, 
            capturedPiece, 
            capturedSquare,
            enPassantBefore, 
            turnColourBefore, 
            movesBefore, 
            halfmoveClockBefore,
            castleRightsBefore, 
            promotion,
            castleRightsAfter, 
            self.enPassantTarget, 
            self.halfmoveClock
        ))

        if not simulation:
            self.positionHistory.append(self.hashBoard())
            self.updateSquareTable()
            visuals.activeSquare = None
            visuals.activeOutline = None
            visuals.moveIndicator.clear()
            visuals.possibleMoves.clear()
            visuals.lastMove = (startRow, startColumn, endRow, endColumn)
            visuals.redraw = True

    def gameState(self, sound=True):
        
        if self.positionHistory.count(self.hashBoard()) >= 3:
            self.gameOverMessage = "Three-fold \nRepetition!\nNobody  wins!"
            if sound: sounds["checkmate"].play()
            return

        inCheck = self.kingCheck(self.turnColour)
        if not self.legalMoves(self.turnColour):
            if inCheck:
                winner = "Black" if self.turnColour == "w" else "White"
                self.gameOverMessage = f"Checkmate!\n{winner}  wins!"
                if sound: 
                    sounds["checkmate"].play()
            else:
                self.gameOverMessage = "Stalemate!\nNobody  wins!"
                if sound: 
                    sounds["checkmate"].play()
        elif inCheck and sound: 
            sounds["check"].play()
        elif self.halfmoveClock >= 100:
            self.gameOverMessage = "50-move rule\nDraw!"
            if sound: 
                sounds["checkmate"].play()
        elif self.insufficientMat():
            self.gameOverMessage = "Insufficient  Material! \n Nobody  wins"
            if sound: 
                sounds["checkmate"].play()
        else: 
            self.gameOverMessage = None

    def previousMove(self, sound=True, simulation=False):
        from engine import visuals
        if not self.moveHistory: 
            return

        move = self.moveHistory.pop()
        if not simulation: 
            self.redoHistory.append(move)
        if self.positionHistory: 
            self.positionHistory.pop()

        piece, start, end, capturedPiece, capturedSquare, enPassantBefore, turnColour, moves, halfmoveClockBefore, castleRightsBefore, promotion, castleRightsAfter, enPassantAfter, halfmoveClockAfter = move

        self.turnColour = turnColour
        self.moves = moves
        self.halfmoveClock = halfmoveClockBefore
        
        castleRights = self.castleRights
        castleRights["wKl"], castleRights["wK"], castleRights["wKr"], castleRights["bKl"], castleRights["bK"], castleRights["bKr"] = castleRightsBefore
        self.enPassantTarget = enPassantBefore

        startPos = 1 << (start[0] * 8 + start[1])
        endPos = 1 << (end[0] * 8 + end[1])

        if promotion is not None:
            self.piecePositions[promotion] &= ~endPos
            self.piecePositions[piece] |= startPos
        else:
            self.piecePositions[piece] &= ~endPos
            self.piecePositions[piece] |= startPos
            
        if capturedPiece != "":
            if capturedSquare:
                self.piecePositions[capturedPiece] |= 1 << (capturedSquare[0] * 8 + capturedSquare[1])
            else:
                self.piecePositions[capturedPiece] |= endPos
            if sound: sounds["capture"].play()
        else:
            if sound: sounds["move"].play()

        self.moveCastleRook(piece, start, end, undo=True)
        self.updateSquareTable()

        if not simulation:
            visuals.activeSquare = visuals.activeOutline = None
            visuals.possibleMoves.clear()
            visuals.moveIndicator.clear()
            visuals.lines.clear()
            visuals.strategyCircles.clear()
            self.gameState(sound)
            
            if len(self.moveHistory) > 0:
                secondLastMove = self.moveHistory[-1]
                visuals.lastMove = (secondLastMove[1][0], secondLastMove[1][1], secondLastMove[2][0], secondLastMove[2][1])
            else:
                visuals.lastMove = None
            visuals.redraw = True

    def redoMove(self):
        from engine import visuals
        if not self.redoHistory: return

        move = self.redoHistory.pop()
        
        piece, start, end, capturedPiece, capturedSquare, enPassantBefore, turnColour, moves, halfmoveClockBefore, castleRightsBefore, promotion, castleRightsAfter, enPassantAfter, halfmoveClockAfter = move

        self.turnColour = "b" if turnColour == "w" else "w"
        self.moves = moves + 1
        self.halfmoveClock = halfmoveClockAfter
        
        castleRights = self.castleRights
        castleRights["wKl"], castleRights["wK"], castleRights["wKr"], castleRights["bKl"], castleRights["bK"], castleRights["bKr"] = castleRightsAfter
        self.enPassantTarget = enPassantAfter

        startPos = 1 << (start[0] * 8 + start[1])
        endPos = 1 << (end[0] * 8 + end[1])

        if capturedPiece != "":
            if capturedSquare:
                self.piecePositions[capturedPiece] &= ~(1 << (capturedSquare[0] * 8 + capturedSquare[1]))
            else:
                self.piecePositions[capturedPiece] &= ~endPos
            sounds["capture"].play()
        else: 
            sounds["move"].play()

        self.moveCastleRook(piece, start, end)

        if promotion is not None:
            self.piecePositions[piece] &= ~startPos
            self.piecePositions[promotion] |= endPos
        else:    
            self.piecePositions[piece] &= ~startPos
            self.piecePositions[piece] |= endPos

        self.moveHistory.append(move)
        self.updateSquareTable()
        self.positionHistory.append(self.hashBoard())

        visuals.activeSquare = visuals.activeOutline = None
        visuals.possibleMoves.clear()
        visuals.moveIndicator.clear()
        visuals.lines.clear()
        visuals.strategyCircles.clear()
        visuals.lastMove = (start[0], start[1], end[0], end[1])
        
        self.gameState()
        visuals.redraw = True