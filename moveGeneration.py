import updateBoard

knightMoves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
kingMoves = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]
rookDirections = [(1,0), (-1,0), (0,1), (0,-1)]
bishopDirections = [(1,1), (1,-1), (-1,1), (-1,-1)]
queenDirections = rookDirections + bishopDirections

def createAttackTables(offset):
    table = [0] * 64
    for square in range(64):
        row = square // 8
        column = square % 8
        mask = 0
        for rowChange, columnChange in offset:
            newRow = row + rowChange
            newColumn = column + columnChange
            if 0 <= newRow < 8 and 0 <= newColumn < 8:
                mask |= 1 << (newRow * 8 + newColumn)
        table[square] = mask
    return table

knightAtk = createAttackTables(knightMoves)
kingAtk = createAttackTables(kingMoves)

def slidingMoves(row, column, movements, friendlyOccupied, occupied, possibleMoves):
    for rowChange, columnChange in movements:
        potRow = row + rowChange
        potColumn = column + columnChange
        while potRow >= 0 and potRow < 8 and potColumn >= 0 and potColumn < 8:
            targetIndex = potRow * 8 + potColumn
            targetBit = 1 << targetIndex

            if targetBit & friendlyOccupied:
                break
            possibleMoves.append((potRow, potColumn))
            if targetBit & occupied:
                break
            potRow += rowChange
            potColumn += columnChange

def instaMoves(atkMask, friendOccupied, possibleMoves):
    legalMask = atkMask & ~friendOccupied
    while legalMask:
        lsb = legalMask & -legalMask
        index = lsb.bit_length() - 1
        possibleMoves.append((index // 8, index % 8))
        legalMask &= legalMask - 1

def isSquareAttacked(row, column, atkColour):
    whiteOccupied, blackOccupied, occupied = updateBoard.getOccupied()
    friendlyOccupied = whiteOccupied if atkColour == "w" else blackOccupied
    for piece, bitboard in updateBoard.piecePositions.items():
        if piece[0] == atkColour:
            b = int(bitboard)
            pieceType = piece[1]
            while b > 0:
                lsb = b & -b
                index = lsb.bit_length() - 1
                pieceRow = index // 8
                pieceColumn = index % 8
                pieceMoves = []
                if pieceType == "H":
                    instaMoves(knightAtk[index], friendlyOccupied, pieceMoves)
                elif pieceType == "K":
                    instaMoves(kingAtk[index], friendlyOccupied, pieceMoves)
                elif pieceType == "R":
                    slidingMoves(pieceRow, pieceColumn, rookDirections, friendlyOccupied, occupied, pieceMoves)
                elif pieceType == "B":
                    slidingMoves(pieceRow, pieceColumn, bishopDirections, friendlyOccupied, occupied, pieceMoves)
                elif pieceType == "Q":
                    slidingMoves(pieceRow, pieceColumn, queenDirections, friendlyOccupied, occupied, pieceMoves)
                elif pieceType == "P":
                    pDir = -1 if atkColour == "w" else 1
                    for dc in [-1, 1]:
                        r, c = pieceRow + pDir, pieceColumn + dc
                        if 0 <= r < 8 and 0 <= c < 8:
                            pieceMoves.append((r, c))

                if (row, column) in pieceMoves:
                    return True
                b &= ~(1 << index)
    return False

def findKing(colour):
    kingBoard = int(updateBoard.piecePositions[colour + "K"])
    if kingBoard == 0:
        return None
    index = kingBoard.bit_length() - 1
    return (index // 8, index % 8)

def kingCheck(colour):
    atkColour = "w" if colour == "b" else "b"
    king = findKing(colour)
    if king is None:
        return False
    return isSquareAttacked(king[0], king[1], atkColour)

def addCastleMoves(pieceColour, possibleMoves):
    row = 7 if pieceColour == "w" else 0
    enemy = "b" if pieceColour == "w" else "w"

    if (updateBoard.castleRights[pieceColour + "Kr"] and 
        updateBoard.getPiece(row, 5) == "" and updateBoard.getPiece(row, 6) == "" and 
        not kingCheck(pieceColour) and 
        not isSquareAttacked(row, 5, enemy) and not isSquareAttacked(row, 6, enemy) and 
        updateBoard.getPiece(row, 7) == pieceColour + "R"):
        possibleMoves.append((row, 6))

    if (updateBoard.castleRights[pieceColour + "Kl"] and 
        updateBoard.getPiece(row, 1) == "" and updateBoard.getPiece(row, 2) == "" and updateBoard.getPiece(row, 3) == "" and 
        not kingCheck(pieceColour) and 
        not isSquareAttacked(row, 3, enemy) and not isSquareAttacked(row, 2, enemy) and 
        updateBoard.getPiece(row, 0) == pieceColour + "R"):
        possibleMoves.append((row, 2))

def calculateLegalMoves(row, column, includeCastling):
    possibleMoves = []
    piece = updateBoard.getPiece(row, column)
    if piece == "":
        return []

    pieceType = piece[-1]
    pieceColour = piece[0]
    whiteOccupied, blackOccupied, occupied = updateBoard.getOccupied()
    friendlyOccupied = whiteOccupied if pieceColour == "w" else blackOccupied

    if pieceType == "H":
        instaMoves(knightAtk[row * 8 + column], friendlyOccupied, possibleMoves)
    elif pieceType == "K":
        instaMoves(kingAtk[row * 8 + column], friendlyOccupied, possibleMoves)
        if includeCastling:
            addCastleMoves(pieceColour, possibleMoves)
    elif pieceType == "R":
        slidingMoves(row, column, rookDirections, friendlyOccupied, occupied, possibleMoves)
    elif pieceType == "B":
        slidingMoves(row, column, bishopDirections, friendlyOccupied, occupied, possibleMoves)
    elif pieceType == "Q":
        slidingMoves(row, column, queenDirections, friendlyOccupied, occupied, possibleMoves)
    elif pieceType == "P":
        direction = -1 if pieceColour == "w" else 1
        potRow = row + direction

        if 0 <= potRow < 8:
            if updateBoard.getPiece(potRow, column) == "":
                possibleMoves.append((potRow, column))
                if pieceColour == "w" and row == 6 and updateBoard.getPiece(potRow - 1, column) == "":
                    possibleMoves.append((potRow - 1, column))
                elif pieceColour == "b" and row == 1 and updateBoard.getPiece(potRow + 1, column) == "":
                    possibleMoves.append((potRow + 1, column))

        for columnChange in [-1, 1]:
            potRow = row + direction
            potColumn = column + columnChange
            if 0 <= potRow < 8 and 0 <= potColumn < 8:
                target = updateBoard.getPiece(potRow, potColumn)
                if target != "" and target[0] != pieceColour:
                    possibleMoves.append((potRow, potColumn))
                elif updateBoard.enPassantTarget == (potRow, potColumn):
                    possibleMoves.append((potRow, potColumn))

    return possibleMoves

def blockCheck(row, column):
    piece = updateBoard.getPiece(row, column)
    if piece == "":
        return []

    colour = piece[0]
    anyMoves = calculateLegalMoves(row, column, True)
    validMoves = []

    import moveExecution

    for endRow, endColumn in anyMoves:
        targetPiece = updateBoard.getPiece(endRow, endColumn)
        start = (row, column)
        end = (endRow, endColumn)
        capturedSquare = None
        capturedPiece = targetPiece

        if piece[-1] == "P" and targetPiece == "" and start[1] != end[1]:
            if updateBoard.enPassantTarget == (endRow, endColumn):
                direction = -1 if piece[0] == "w" else 1
                capturedSquare = (endRow - direction, endColumn)
                capturedPiece = updateBoard.getPiece(capturedSquare[0], capturedSquare[1])

        moveExecution.simulateMove(piece, start, end, capturedPiece, capturedSquare)
        if not kingCheck(colour):
            validMoves.append(end)
        moveExecution.undoMove(piece, start, end, capturedPiece, capturedSquare)

    return validMoves

def legalMoves(colour):
    for piece, bitboard in updateBoard.piecePositions.items():
        if piece[0] == colour:
            b = int(bitboard)
            while b:
                lsb = b & -b
                index = lsb.bit_length() - 1
                row, column = index // 8, index % 8
                if blockCheck(row, column):
                    return True
                b &= b - 1
    return False