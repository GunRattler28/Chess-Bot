from engine.constants import knightMoves, kingMoves, rookDirections, bishopDirections, queenDirections, knightAtk, kingAtk, sounds, botColour

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

        self.knightAtk = self.createAttackTables(knightMoves)
        self.kingAtk = self.createAttackTables(kingMoves)

    def clone(self):
        new_state = logic()
        new_state.moves = self.moves
        new_state.halfmoveClock = self.halfmoveClock
        new_state.turnColour = self.turnColour
        new_state.enPassantTarget = self.enPassantTarget
        new_state.gameOverMessage = self.gameOverMessage
        new_state.piecePositions = self.piecePositions.copy()
        new_state.castleRights = self.castleRights.copy()
        new_state.squarePiece = self.squarePiece.copy()
        new_state.moveHistory = self.moveHistory.copy()
        new_state.redoHistory = self.redoHistory.copy()
        new_state.positionHistory = self.positionHistory.copy()
        
        return new_state

    def getPiece(self, row, column):
        if not (0 <= row < 8 and 0 <= column < 8): return ""
        return self.squarePiece[row * 8 + column]

    def setPiece(self, row, column, piece):
        if not (0 <= row < 8 and 0 <= column < 8): return
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
            if name[0] == "w": whiteOccupied |= bitboard
            else: blackOccupied |= bitboard
        return (whiteOccupied, blackOccupied, whiteOccupied | blackOccupied)

    def hashBoard(self):
        return hash((tuple(self.piecePositions.values()), self.turnColour, tuple(self.castleRights.values()), self.enPassantTarget))

    def createAttackTables(self, offset):
        table = [0] * 64
        for square in range(64):
            row, column = square // 8, square % 8
            mask = 0
            for rowChange, columnChange in offset:
                newRow, newColumn = row + rowChange, column + columnChange
                if 0 <= newRow < 8 and 0 <= newColumn < 8:
                    mask |= 1 << (newRow * 8 + newColumn)
            table[square] = mask
        return table

    def slidingMoves(self, row, column, movements, friendlyOccupied, occupied, possibleMoves):
        for rowChange, columnChange in movements:
            potRow, potColumn = row + rowChange, column + columnChange
            while 0 <= potRow < 8 and 0 <= potColumn < 8:
                targetBit = 1 << (potRow * 8 + potColumn)
                if targetBit & friendlyOccupied: break
                possibleMoves.append((potRow, potColumn))
                if targetBit & occupied: break
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
        
        if self.knightAtk[targetIndex] & self.piecePositions[atkColour + "H"]:
            return True
            
        if self.kingAtk[targetIndex] & self.piecePositions[atkColour + "K"]:
            return True
        
        pawnMask = 0
        if atkColour == "w":
            if row < 7 and column > 0: pawnMask |= 1 << ((row + 1) * 8 + (column - 1))
            if row < 7 and column < 7: pawnMask |= 1 << ((row + 1) * 8 + (column + 1))
        else:
            if row > 0 and column > 0: pawnMask |= 1 << ((row - 1) * 8 + (column - 1))
            if row > 0 and column < 7: pawnMask |= 1 << ((row - 1) * 8 + (column + 1))
            
        if pawnMask & self.piecePositions[atkColour + "P"]:
            return True

        whiteOccupied, blackOccupied, occupied = self.getOccupied()

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
        if kingBoard == 0: return None
        index = kingBoard.bit_length() - 1
        return (index // 8, index % 8)

    def kingCheck(self, colour):
        king = self.findKing(colour)
        if king is None: return False
        return self.isSquareAttacked(king[0], king[1], "w" if colour == "b" else "b")

    def addCastleMoves(self, pieceColour, possibleMoves):
        row = 7 if pieceColour == "w" else 0
        enemy = "b" if pieceColour == "w" else "w"

        if (self.castleRights[pieceColour + "Kr"] and self.getPiece(row, 5) == "" and self.getPiece(row, 6) == "" and not self.kingCheck(pieceColour) and not self.isSquareAttacked(row, 5, enemy) and not self.isSquareAttacked(row, 6, enemy) and self.getPiece(row, 7) == pieceColour + "R"):
            possibleMoves.append((row, 6))

        if (self.castleRights[pieceColour + "Kl"] and self.getPiece(row, 1) == "" and self.getPiece(row, 2) == "" and self.getPiece(row, 3) == "" and not self.kingCheck(pieceColour) and not self.isSquareAttacked(row, 3, enemy) and not self.isSquareAttacked(row, 2, enemy) and self.getPiece(row, 0) == pieceColour + "R"):
            possibleMoves.append((row, 2))

    def calculateLegalMoves(self, row, column, includeCastling):
        possibleMoves = []
        piece = self.getPiece(row, column)
        if piece == "": return []

        pieceType, pieceColour = piece[-1], piece[0]
        whiteOccupied, blackOccupied, occupied = self.getOccupied()
        friendlyOccupied = whiteOccupied if pieceColour == "w" else blackOccupied

        if pieceType == "H": self.instaMoves(self.knightAtk[row * 8 + column], friendlyOccupied, possibleMoves)
        elif pieceType == "K":
            self.instaMoves(self.kingAtk[row * 8 + column], friendlyOccupied, possibleMoves)
            if includeCastling: self.addCastleMoves(pieceColour, possibleMoves)
        elif pieceType == "R": self.slidingMoves(row, column, rookDirections, friendlyOccupied, occupied, possibleMoves)
        elif pieceType == "B": self.slidingMoves(row, column, bishopDirections, friendlyOccupied, occupied, possibleMoves)
        elif pieceType == "Q": self.slidingMoves(row, column, queenDirections, friendlyOccupied, occupied, possibleMoves)
        elif pieceType == "P":
            direction = -1 if pieceColour == "w" else 1
            potRow = row + direction
            if 0 <= potRow < 8:
                if self.getPiece(potRow, column) == "":
                    possibleMoves.append((potRow, column))
                    if pieceColour == "w" and row == 6 and self.getPiece(potRow - 1, column) == "": possibleMoves.append((potRow - 1, column))
                    elif pieceColour == "b" and row == 1 and self.getPiece(potRow + 1, column) == "": possibleMoves.append((potRow + 1, column))

            for columnChange in [-1, 1]:
                potRow, potColumn = row + direction, column + columnChange
                if 0 <= potRow < 8 and 0 <= potColumn < 8:
                    target = self.getPiece(potRow, potColumn)
                    if target != "" and target[0] != pieceColour: possibleMoves.append((potRow, potColumn))
                    elif self.enPassantTarget == (potRow, potColumn): possibleMoves.append((potRow, potColumn))

        return possibleMoves

    def blockCheck(self, row, column):
        piece = self.getPiece(row, column)
        if piece == "": return []
        validMoves = []
        
        for endRow, endColumn in self.calculateLegalMoves(row, column, True):
            targetPiece = self.getPiece(endRow, endColumn)
            capturedSquare = None
            capturedPiece = targetPiece

            if piece[-1] == "P" and targetPiece == "" and column != endColumn:
                if self.enPassantTarget == (endRow, endColumn):
                    capturedSquare = (endRow - (-1 if piece[0] == "w" else 1), endColumn)
                    capturedPiece = self.getPiece(capturedSquare[0], capturedSquare[1])

            self.simulateMove(piece, (row, column), (endRow, endColumn), capturedPiece, capturedSquare)
            if not self.kingCheck(piece[0]): validMoves.append((endRow, endColumn))
            self.undoMove(piece, (row, column), (endRow, endColumn), capturedPiece, capturedSquare)

        return validMoves

    def legalMoves(self, colour):
        for piece, bitboard in self.piecePositions.items():
            if piece[0] == colour:
                b = int(bitboard)
                while b:
                    lsb = b & -b
                    index = lsb.bit_length() - 1
                    if self.blockCheck(index // 8, index % 8): return True
                    b &= b - 1
        return False

    def isPromotable(self, piece, row):
        return (piece == "wP" and row == 0) or (piece == "bP" and row == 7)

    def insufficientMat(self):
        if (self.piecePositions["bP"] or self.piecePositions["bR"] or self.piecePositions["bQ"] or self.piecePositions["wP"] or self.piecePositions["wR"] or self.piecePositions["wQ"]): return False
        totKnights = self.piecePositions["bH"] | self.piecePositions["wH"]
        totBishops = self.piecePositions["bB"] | self.piecePositions["wB"]
        return (totBishops + totKnights) < 2

    def moveCastleRook(self, piece, start, end, undo=False):
        if piece not in ("wK", "bK"): return
        row = 7 if piece == "wK" else 0

        if start == (row, 4) and end == (row, 6): rookStart, rookEnd = ((row, 5), (row, 7)) if undo else ((row, 7), (row, 5))
        elif start == (row, 4) and end == (row, 2): rookStart, rookEnd = ((row, 3), (row, 0)) if undo else ((row, 0), (row, 3))
        else: return

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
        
        movingPiece = self.getPiece(startRow, startColumn)
        target = self.getPiece(endRow, endColumn)
        targetPos = 1 << (endRow * 8 + endColumn)
        start, end = (startRow, startColumn), (endRow, endColumn)

        self.moveHistory.append({
            "piece": movingPiece,
            "start": start, 
            "end": end, 
            "capturedPiece": target, 
            "capturedSquare": None, 
            "enPassantBefore": self.enPassantTarget, 
            "turnColour": self.turnColour, 
            "moves": self.moves, 
            "halfmoveClockBefore": self.halfmoveClock, 
            "halfmoveClockAfter": None, 
            "castleRightsBefore": self.castleRights.copy(), 
            "promotion": None
        })

        self.moveCastleRook(movingPiece, start, end)
        
        if movingPiece == "wK": self.castleRights["wK"] = self.castleRights["wKl"] = self.castleRights["wKr"] = False
        elif movingPiece == "bK": self.castleRights["bK"] = self.castleRights["bKl"] = self.castleRights["bKr"] = False
        elif movingPiece == "wR":
            if start == (7, 0): self.castleRights["wKl"] = False
            elif start == (7, 7): self.castleRights["wKr"] = False
        elif movingPiece == "bR":
            if start == (0, 0): self.castleRights["bKl"] = False
            elif start == (0, 7): self.castleRights["bKr"] = False

        if target == "wR":
            if end == (7, 0): self.castleRights["wKl"] = False
            elif end == (7, 7): self.castleRights["wKr"] = False
        elif target == "bR":
            if end == (0, 0): self.castleRights["bKl"] = False
            elif end == (0, 7): self.castleRights["bKr"] = False
        if not simulation:
            visuals.possibleMoves.clear()
            self.redoHistory.clear()

        enPassantCapture = False
        if movingPiece[-1] == "P" and target == "" and startColumn != endColumn and self.enPassantTarget == (endRow, endColumn):
            capturedRow = endRow - (-1 if movingPiece[0] == "w" else 1)
            capturedPiece = self.getPiece(capturedRow, endColumn)
            if capturedPiece != "":
                self.piecePositions[capturedPiece] &= ~(1 << (capturedRow * 8 + endColumn))
                self.setPiece(capturedRow, endColumn, "")
                self.moveHistory[-1]["capturedPiece"] = capturedPiece
                self.moveHistory[-1]["capturedSquare"] = (capturedRow, endColumn)
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
            self.moveHistory[-1]["promotion"] = promotedPiece
        
        self.moveHistory[-1]["castleRightsAfter"] = self.castleRights.copy()
        self.enPassantTarget = ((startRow + endRow) // 2, startColumn) if movingPiece[-1] == "P" and abs(endRow - startRow) == 2 else None
        self.moveHistory[-1]["enPassantAfter"] = self.enPassantTarget
        self.turnColour = "b" if self.turnColour == "w" else "w"    
        
        self.updateSquareTable()
        self.moves += 1
        self.halfmoveClock = 0 if movingPiece[-1] == "P" or target != "" or enPassantCapture else self.halfmoveClock + 1
        self.moveHistory[-1]["halfmoveClockAfter"] = self.halfmoveClock
        self.positionHistory.append(self.hashBoard())

        if not simulation:
            visuals.activeSquare = None
            visuals.activeOutline = None
            visuals.moveIndicator.clear()
            visuals.possibleMoves.clear()
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
                if sound: sounds["checkmate"].play()
            else:
                self.gameOverMessage = "Stalemate!\nNobody  wins!"
                if sound: sounds["checkmate"].play()
        elif inCheck and sound: sounds["check"].play()
        elif self.halfmoveClock >= 100:
            self.gameOverMessage = "50-move rule\nDraw!"
            if sound: sounds["checkmate"].play()
        elif self.insufficientMat():
            self.gameOverMessage = "Insufficient  Material! \n Nobody  wins"
            if sound: sounds["checkmate"].play()
        else: self.gameOverMessage = None

    def previousMove(self, sound=True, simulation=False):
        from engine import visuals
        if not self.moveHistory: return

        p = self.moveHistory.pop()
        if not simulation: self.redoHistory.append(p)
        if self.positionHistory: self.positionHistory.pop()

        self.turnColour, self.moves, self.halfmoveClock = p["turnColour"], p["moves"], p.get("halfmoveClockBefore", 0)
        self.castleRights.clear()
        self.castleRights.update(p["castleRightsBefore"])
        self.enPassantTarget = p.get("enPassantBefore", None)

        startPos, endPos = 1 << (p["start"][0] * 8 + p["start"][1]), 1 << (p["end"][0] * 8 + p["end"][1])
        self.setPiece(p["end"][0], p["end"][1], "")
        self.setPiece(p["start"][0], p["start"][1], p["piece"])

        if p["promotion"] is not None:
            self.piecePositions[p["promotion"]] &= ~endPos
            self.piecePositions[p["piece"]] |= startPos
        else:
            self.piecePositions[p["piece"]] &= ~endPos
            self.piecePositions[p["piece"]] |= startPos
            
        if p["capturedPiece"] != "":
            if p.get("capturedSquare"):
                self.piecePositions[p["capturedPiece"]] |= 1 << (p["capturedSquare"][0] * 8 + p["capturedSquare"][1])
                self.setPiece(p["capturedSquare"][0], p["capturedSquare"][1], p["capturedPiece"])
            else:
                self.piecePositions[p["capturedPiece"]] |= endPos
                self.setPiece(p["end"][0], p["end"][1], p["capturedPiece"])
            if sound: sounds["capture"].play()
        else:
            if sound: sounds["move"].play()

        self.moveCastleRook(p["piece"], p["start"], p["end"], undo=True)
        self.updateSquareTable()
        if not simulation:
            visuals.activeSquare = visuals.activeOutline = None
            visuals.possibleMoves.clear()
            visuals.moveIndicator.clear()
            visuals.lines.clear()
            visuals.strategyCircles.clear()

        if not simulation:
            self.gameState(sound)
            visuals.redraw = True

    def redoMove(self):
        from engine import visuals
        if not self.redoHistory: return

        m = self.redoHistory.pop()
        self.turnColour = "b" if m["turnColour"] == "w" else "w"
        self.moves = m["moves"] + 1
        self.halfmoveClock = m.get("halfmoveClockAfter", 0)
        self.castleRights.clear()
        self.castleRights.update(m["castleRightsAfter"])
        self.enPassantTarget = m.get("enPassantAfter", None)

        startPos, endPos = 1 << (m["start"][0] * 8 + m["start"][1]), 1 << (m["end"][0] * 8 + m["end"][1])

        if m["capturedPiece"] != "":
            if m.get("capturedSquare"):
                self.piecePositions[m["capturedPiece"]] &= ~(1 << (m["capturedSquare"][0] * 8 + m["capturedSquare"][1]))
                self.setPiece(m["capturedSquare"][0], m["capturedSquare"][1], "")
            else:
                self.piecePositions[m["capturedPiece"]] &= ~endPos
                self.setPiece(m["end"][0], m["end"][1], "")
            sounds["capture"].play()
        else: sounds["move"].play()

        self.moveCastleRook(m["piece"], m["start"], m["end"])

        if m["promotion"] is not None:
            self.piecePositions[m["piece"]] &= ~startPos
            self.piecePositions[m["promotion"]] |= endPos
            self.setPiece(m["start"][0], m["start"][1], "")
            self.setPiece(m["end"][0], m["end"][1], m["promotion"])
        else:    
            self.piecePositions[m["piece"]] &= ~startPos
            self.piecePositions[m["piece"]] |= endPos
            self.setPiece(m["start"][0], m["start"][1], "")
            self.setPiece(m["end"][0], m["end"][1], m["piece"])

        self.moveHistory.append(m)
        self.updateSquareTable()
        self.positionHistory.append(self.hashBoard())

        visuals.activeSquare = visuals.activeOutline = None
        visuals.possibleMoves.clear()
        visuals.moveIndicator.clear()
        visuals.lines.clear()
        visuals.strategyCircles.clear()
        
        self.gameState()
        visuals.redraw = True