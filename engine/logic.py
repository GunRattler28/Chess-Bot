from engine.constants import rookDirections, bishopDirections, queenDirections, knightAtk, kingAtk, sounds, botColour, empty, queen, king, knight, rook, bishop, pawn, black, white, zobristKeys, zobristTurn, zobristCastling, zobristEnPassant
from engine import visuals, constants
from bot import evaluation

class logic:

    # Creates all the tmpty variables that will later be used

    def __init__(self):
        self.gameOverMessage = None
        self.moves = 0
        self.halfmoveClock = 0
        self.turnColour = white
        self.moveHistory = []
        self.redoHistory = []
        self.positionHistory = []
        self.positionCounts = {}
        self.squarePiece = [empty] * 64
        self.enPassantTarget = None
        self.hash = 0
        self.whiteOccupied = 0
        self.blackOccupied=  0
        self.occupied = 0
        self.evaluationScore = 0
        self.totalPieces = 0
        self.endgame = 0
        self.castleRights = 0b1111

        # Each bit represents a rook. 1 means can castle. From smallest to largest bit: white queenside castle, white kingside castle, black queenside castle, black kingside castle

        # Initialises empty bitboards so that they can be populated by fen string

        self.piecePositions = {
            (black | queen): 0x0000000000000000, 
            (black | king): 0x0000000000000000, 
            (black | bishop): 0x0000000000000000,
            (black | knight): 0x0000000000000000, 
            (black | rook): 0x0000000000000000, 
            (black | pawn): 0x0000000000000000,
            (white | queen): 0x0000000000000000, 
            (white | king): 0x0000000000000000, 
            (white | bishop): 0x0000000000000000,
            (white | knight): 0x0000000000000000, 
            (white | rook): 0x0000000000000000, 
            (white | pawn): 0x0000000000000000
        }

        self.updateOccupied() # Updates bitboards which handle occupancy

    # So that other scripts can use the logic without actually changing anything (such as what we see). main.py passes a copy of logic.py to bot.py so that the we don't see the moves the bot is testing while we wait

    def clone(self):
        newState = logic() # For all the functions

        # For all the current values

        newState.moves = self.moves
        newState.halfmoveClock = self.halfmoveClock
        newState.turnColour = self.turnColour
        newState.enPassantTarget = self.enPassantTarget
        newState.gameOverMessage = self.gameOverMessage
        newState.piecePositions = self.piecePositions.copy()
        newState.castleRights = self.castleRights
        newState.squarePiece = self.squarePiece.copy()
        newState.moveHistory = self.moveHistory.copy()
        newState.redoHistory = self.redoHistory.copy()
        newState.positionHistory = self.positionHistory.copy()
        newState.positionCounts = self.positionCounts.copy()
        newState.hash = self.hash
        newState.whiteOccupied = self.whiteOccupied
        newState.blackOccupied = self.blackOccupied
        newState.occupied = self.occupied
        newState.evaluationScore = self.evaluationScore
        newState.totalPieces = self.totalPieces
        newState.endgame = self.endgame
        return newState

    def createSquareTable(self):
        self.squarePiece = [empty] * 64 # 64 element long array. Defaults to all empty squares so we don't need to loop through all squares just those with pieces
        self.hash = 0
        self.totalPieces = 0
        for piece, bitboard in self.piecePositions.items():
            board = bitboard
            while board:
                lsb = board & -board # <-- '-board' flips all bits then adds 1. This means that where the least significant 1 bit is in original number it would be 0 in flipped. but adding 1 means that there is a carry chain that ends at least significant bit and makes it 1. And therefore only has that bit
                index = lsb.bit_length() - 1 # 'bit_length' returns bits needed to write number. -1 gives index from 0 to 63.
                self.squarePiece[index] = piece # Changes specific square in array to correct piece
                self.hash = self.hash ^ zobristKeys[piece][index] # Updates hash to have the piece
                self.totalPieces += 1 # Tracks total pieces
                board &= board - 1 # Clears least significant bit

        self.endgame = evaluation.isEndgame(self) # Finds if endgame so that bot makes appropiate moves if end game fen string loaded

        if self.turnColour == black: # So that hash is different for black and white
            self.hash = self.hash ^ zobristTurn # xor toggles bits on and off

        self.hash = self.hash ^ zobristCastling[self.castleRights] # castlerights being stored in binary mean each combination / computation has a unique value. xor by same value means it is a toggle

        if self.enPassantTarget != None:
            self.hash = self.hash ^ zobristEnPassant[self.enPassantTarget[1]] # Toggles hash by same value en passant value
        
        self.evaluationScore = 0 # Evaluation is tracked throughout the game

        for index in range(64):
            piece = self.squarePiece[index] # Gets piece from 64 element array
            if piece != empty:
                self.evaluationScore += evaluation.getPieceScore(piece, index, self.endgame) # Starts off evaluation score. Ready to be tracked rest of game.

    def loadFEN(self, fen):
        try:

            # Splits the FEN string into the 6 components

            fenParts = fen.split(" ")
            placements = fenParts[0]
            colour = fenParts[1]
            castlingRights = fenParts[2]
            enPassant = fenParts[3]
            halfMove = fenParts[4]
            fullMoves = fenParts[5]

            # Map between FEN string piece names and my program's piece names (e.g: p: black pawn)

            pieceCode = {
                "p": black | pawn,
                "n": black | knight,
                "b": black | bishop,
                "r": black | rook,
                "q": black | queen,
                "k": black | king,
                "P": white | pawn,
                "N": white | knight,
                "B": white | bishop,
                "R": white | rook,
                "Q": white | queen,
                "K": white | king
            }

            # Clears bitboards

            for bitboard in self.piecePositions.keys():
                self.piecePositions[bitboard] = 0

            # Sets array to have all 64 squares empty

            self.squarePiece = [empty] * 64

            row = 0
            column = 0

            for character in placements:
                if character == "/": # '/' is the separator for rows
                    row += 1
                    column = 0
                elif character.isdigit(): # number of empty spaces in a row
                    column += int(character)
                else:
                    piece = pieceCode[character] # translate between FEN string piece names and my piece names
                    index = row * 8 + column
                    self.piecePositions[piece] |= (1 << index) # left shifts a 1 bit to the index of the piece then adds that 1 in that position to the bitboard. 
                    column += 1 # pieces take 1 square so move to the next square

            self.turnColour = white if colour == "w" else black # sets the turn colour to what FEN string says

            self.castleRights = 0 # resets castle rights

            # sets castle rights to what FEN string says

            if "Q" in castlingRights:
                self.castleRights |= 1 # bit 1 is white queen side castle
            if "K" in castlingRights:
                self.castleRights |= 2 # bit 2 is white king side castle
            if "q" in castlingRights:
                self.castleRights |= 4 # bit 3 is black queen side castle
            if "k" in castlingRights:
                self.castleRights |= 8 # bit 4 is black king wside castle

            if enPassant == "-": # No en passant
                self.enPassantTarget = None
            else:
                enRow = 8 - int(enPassant[1]) # Because for me it is reversed
                enColumm = ord(enPassant[0]) - 97 # ord gets ASCII code of the letter. ASCII code - 97 (ASCII code for a) shows how many columns past a it is
                self.enPassantTarget = (enRow, enColumm) # sets en passant target

            self.halfmoveClock = int(halfMove) # moves since last irreversible move (pawn push, capture)
            self.moves = (int(fullMoves) - 1) * 2 + (1 if self.turnColour == black else 0) # FEN string counts 1 move as every time both sides play. I count as different so this converts.

            # Clears variables which werent set

            self.moveHistory.clear()
            self.redoHistory.clear()
            self.positionHistory.clear()
            self.positionCounts.clear()
            self.updateOccupied() # set's up bitboard of where there is a piece
            self.createSquareTable() # creates array containing piece on every square
            self.positionHistory.append(self.hash) # set's current state as the first move in move history
            self.positionCounts[self.hash] = 1 # resets hash
            return True # if no errors has occured it was successful
        except:
            return False # there was an error so tell whatever called function and it can handle error smoothly

    def updateSquare(self, row, column, newPiece):
        index = row * 8 + column
        oldPiece = self.squarePiece[index]
        if oldPiece != empty:
            self.totalPieces -= 1 # Remove old piece from total pieces count
            self.evaluationScore -= evaluation.getPieceScore(oldPiece, index, self.endgame) # Remove evaluation score that piece contributed
            self.piecePositions[oldPiece] = self.piecePositions[oldPiece] & ~(1 << index) # Removes bit representing piece from piece type specific bitboard. Left shifts bit to correct position then inverts so all 1s and 1, 0 bit where piece is then AND gate to remove piece 
            self.hash = self.hash ^ zobristKeys[oldPiece][index] # Removes piece from hash

            # Removes old piece from coloured bitboards showing what squares are occupied

            if oldPiece & white:
                self.whiteOccupied &= ~(1 << index) # Left shifts 1 to correct index then flips all bits. Puts 0 bit in colour occupied bitboard at correct index 
            else:
                self.blackOccupied &= ~(1 << index)

        if newPiece != empty:
            self.totalPieces += 1 # Add piece to total pieces count
            self.evaluationScore += evaluation.getPieceScore(newPiece, index, self.endgame) # Add piece to evaluation score
            self.piecePositions[newPiece] = self.piecePositions[newPiece] | (1 << index) # Left shifts bit to correct place then OR with piece type bitboard
            self.hash = self.hash ^ zobristKeys[newPiece][index] # Adds piece to hash

            # Adds piece to coloured bitboards showing what squares are occupied

            if newPiece & white:
                self.whiteOccupied |= (1 << index) # Left shifts 1 to correct index. Puts 1 bit in colour occupied bitboard at correct index
            else:
                self.blackOccupied |= (1 << index)

        self.occupied = (self.whiteOccupied | self.blackOccupied) # Updates occupied bitboard
        self.squarePiece[index] = newPiece # Updates 64 square array

    def updateOccupied(self):
        self.whiteOccupied = 0
        self.blackOccupied = 0
        for piece, bitboard in self.piecePositions.items():
            if piece & white: # Binary for white is 01000. Binary for any piece type only affects last 3 bits. This means and will only give a 01000 if piece is white or give 00000 for anything else
                self.whiteOccupied |= bitboard # Adds the bits where those white pieces are to white bitboard
            else:
                self.blackOccupied |= bitboard # Adds bits where other pieces are to bitboards
        self.occupied = (self.whiteOccupied | self.blackOccupied) # Combines bitboards for map of which squares are occupied

    def switchTurn(self):
        self.turnColour = black if self.turnColour == white else white # Changes turn colour
        self.hash = self.hash ^ zobristTurn # Toggles hash by turn colour

    def setEnPassantTarget(self, target):
        if self.enPassantTarget != target: # Checks whether target has changed to ensure that the whole thing isn't done for no reason (this would be when the target is none both moves)
            if self.enPassantTarget != None:
                self.hash = self.hash ^ zobristEnPassant[self.enPassantTarget[1]] # Untoggles current target from hash
            self.enPassantTarget = target # Sets target
            if self.enPassantTarget != None:
                self.hash = self.hash ^ zobristEnPassant[self.enPassantTarget[1]] # Hashes current target

    def slidingMoves(self, row, column, movements, friendlyOccupied, occupied, possibleMoves):
        for rowChange, columnChange in movements: # Splits movement tuple into row offset, column offset. Checks how far piece can move in each direction
            potRow, potColumn = row + rowChange, column + columnChange # Changes potential row and column to test if it is legal or not
            while 0 <= potRow < 8 and 0 <= potColumn < 8: # While still in board bounds
                targetBit = 1 << (potRow * 8 + potColumn) # Creates mask by left shifting bit that has a value of 1 to where the potential row and column put it
                if targetBit & friendlyOccupied: 
                    break # If piece is occupied by friendly piece don't include that square in where piece can move in this direction
                possibleMoves.append((potRow, potColumn)) # Add this new square to possible moves that can be played
                if targetBit & occupied:
                    break # If piece is occupied by enemy piece include that square in where piece can move in this direction
                potRow += rowChange # Move to next row
                potColumn += columnChange # Move to next column

    def instaMoves(self, atkMask, friendOccupied, possibleMoves):
        legalMask = atkMask & ~friendOccupied # '~' flips bits. This means that legal mask is where atkMask is and there isn't a friendly piece. Attack mask is made in constants.py
        while legalMask:
            lsb = legalMask & -legalMask # '-' flips all bits then adds 1. This means that where the least significant 1 bit is in original number it would be 0 in flipped. but adding 1 means that there is a carry chain that ends at least significant bit and makes it 1. And therefore only has that bit
            index = lsb.bit_length() - 1 # 'bit_length' returns bits needed to write number. -1 gives index from 0 to 63.
            possibleMoves.append((index // 8, index % 8)) # adds tuple of row and column into possible places that piece can move
            legalMask &= legalMask - 1 # Clears least significant bit and continues

    def isSquareAttacked(self, row, column, atkColour):
        targetIndex = row * 8 + column
        # knightAtk[targetIndex] is mask of where knight can move from specific square. Since targetIndex is square we want to see is attacked it shows where a knight would have to be to move to target square
        if knightAtk[targetIndex] & self.piecePositions[atkColour | knight]: # If where the knight would have to be to attack target square has a knight in that square it means a knight is attacking target square
            return True
        # Same thing as knight but for king
        if kingAtk[targetIndex] & self.piecePositions[atkColour | king]:
            return True
        
        pawnMask = 0

        # Creates mask of where pawns can move from, that being up 1 and across on either side. Does this for both colours and both directions the pawn could move horizontally
        
        if atkColour == white:
            if row < 7 and column > 0: 
                pawnMask |= 1 << ((row + 1) * 8 + (column - 1))
            if row < 7 and column < 7: 
                pawnMask |= 1 << ((row + 1) * 8 + (column + 1))
        else:
            if row > 0 and column > 0: 
                pawnMask |= 1 << ((row - 1) * 8 + (column - 1))
            if row > 0 and column < 7: 
                pawnMask |= 1 << ((row - 1) * 8 + (column + 1))
            
        if pawnMask & self.piecePositions[atkColour | pawn]: # If possible places pawns could be to attack square has a pawn in one of those places return true
            return True

        # Lots of duplicated code but still technically O(1) time complexity since fixed number of iterations. Can't think of another way to do it in O(1) time complexity
        
        for rowChange, columnChange in rookDirections: # Row offset and column offset of rook movements
            potRow, potColumn = row + rowChange, column + columnChange # Potential row and column that piece could be in
            while 0 <= potRow < 8 and 0 <= potColumn < 8: # While potential row and column is in board bounds
                testMask = 1 << (potRow * 8 + potColumn) # Creates mask by left shifting bit that has a value of 1 to where the potential row and column put it
                if testMask & self.occupied: # If there is any piece on this new potential square test if it is a 
                    if testMask & (self.piecePositions[atkColour | rook] | self.piecePositions[atkColour | queen]): # If there is a rook or queen on any of these squares return true
                        return True
                    break # If it hits any other piece stop searching in this direction
                potRow += rowChange # Moves to next row
                potColumn += columnChange # Moves to next column

        for rowChange, columnChange in bishopDirections: # Row offset and column offset of bishop movements
            potRow, potColumn = row + rowChange, column + columnChange # Potential row and column that piece could be in
            while 0 <= potRow < 8 and 0 <= potColumn < 8: # While potential row and column is in board bounds
                testMask = 1 << (potRow * 8 + potColumn) # Creates mask by left shifting bit that has a value of 1 to where the potential row and column put it
                if testMask & self.occupied: # If there is any piece on this new potential square test if it is a 
                    if testMask & (self.piecePositions[atkColour | bishop] | self.piecePositions[atkColour | queen]): # If there is a bishop or queen on any of these squares return true
                        return True
                    break # If it hits any other piece stop searching in this direction
                potRow += rowChange # Moves to next row
                potColumn += columnChange # Moves to next column
        
        return False # If it can't be attacked by knights, kings, pawns, bishops, rooks or queens it can't be attacked

    def findKing(self, colour):
        kingBoard = self.piecePositions[colour | king] # Correct bitboad for specific colour of king
        if kingBoard == empty: 
            return None # Handles no king
        index = kingBoard.bit_length() - 1 # 'bit_length' returns bits needed to write number. -1 gives index from 0 to 63.
        return (index // 8, index % 8) # Return row and column from index through integer division and modulo respectively

    def kingCheck(self, colour):
        king = self.findKing(colour) # (row, column) of king
        if king is None: 
            return False # Handles no king
        return self.isSquareAttacked(king[0], king[1], white if colour == black else black) # king[0] is row, king[1] is column, colour that would be attacking

    def addCastleMoves(self, pieceColour, possibleMoves):
        row = 7 if pieceColour == white else 0 # Always back rank. Changes based on colour
        enemy = black if pieceColour == white else white
        # Assigns value of bit that represents castle direction to varaible for readable and gates 
        if pieceColour == white:
            kl = 1
            kr = 2
        else:
            kl = 4
            kr = 8

        # If king can castle on specific side, squares in between are empty, and king isn't in check. This means can castle on that side. Add this as a move that can be played

        if (self.castleRights & kr and self.squarePiece[row * 8 + 5] == empty and self.squarePiece[row * 8 + 6] == empty and not self.kingCheck(pieceColour) and not self.isSquareAttacked(row, 5, enemy) and not self.isSquareAttacked(row, 6, enemy) and self.squarePiece[row * 8 + 7] == (pieceColour | rook)):
            possibleMoves.append((row, 6))

        if (self.castleRights & kl and self.squarePiece[row * 8 + 1] == empty and self.squarePiece[row * 8 + 2] == empty and self.squarePiece[row * 8 + 3] == empty and not self.kingCheck(pieceColour) and not self.isSquareAttacked(row, 3, enemy) and not self.isSquareAttacked(row, 2, enemy) and self.squarePiece[row * 8 + 0] == (pieceColour | rook)):
            possibleMoves.append((row, 2))

    def calculateLegalMoves(self, row, column):
        possibleMoves = [] # Empty list of what moves can be made
        piece = self.squarePiece[row * 8 + column] # Piece that on specific square
        if piece == empty:
            return []
                                            #           Colour  +   Piece Type
        pieceType = piece & 7 # Piece is represented by   01          001           (example). & 7 gets the last 3 bits (001 in this case)
        pieceColour = white if (piece & white) else black # variable & white gives 0 if variable is not also white
        friendlyOccupied = self.whiteOccupied if pieceColour == white else self.blackOccupied

        if pieceType == knight: 
            self.instaMoves(knightAtk[row * 8 + column], friendlyOccupied, possibleMoves) # knightAtk is everywhere knight can move from any square. Since knights don't have ray attacks it can be easily precomputed
        elif pieceType == king:
            self.instaMoves(kingAtk[row * 8 + column], friendlyOccupied, possibleMoves) # kingAtk is everywhere king can move from any square
            self.addCastleMoves(pieceColour, possibleMoves) # Add castling as a possible move
        elif pieceType == rook: 
            self.slidingMoves(row, column, rookDirections, friendlyOccupied, self.occupied, possibleMoves) # Everywhere rook can move
        elif pieceType == bishop: 
            self.slidingMoves(row, column, bishopDirections, friendlyOccupied, self.occupied, possibleMoves) # Everywhere bishop can move
        elif pieceType == queen: 
            self.slidingMoves(row, column, queenDirections, friendlyOccupied, self.occupied, possibleMoves) # Everywhere queen can move
        elif pieceType == pawn:
            direction = -1 if pieceColour == white else 1 # Direction pawn moves in based off of colour
            potRow = row + direction
            if 0 <= potRow < 8: # If inside board boundaries
                if self.squarePiece[potRow * 8 + column] == empty: # If square in front of pawn is empty
                    possibleMoves.append((potRow, column))
                    if pieceColour == white and row == 6 and self.squarePiece[(potRow - 1) * 8 + column] == empty: # If square 2 in front is also empty
                        possibleMoves.append((potRow - 1, column))
                    elif pieceColour == black and row == 1 and self.squarePiece[(potRow + 1) * 8 + column] == empty: # If square 2 in front is also empty
                        possibleMoves.append((potRow + 1, column))

            for columnChange in [-1, 1]: # For both directions pawn can capture (left and right)
                potRow, potColumn = row + direction, column + columnChange # New row and column
                if 0 <= potRow < 8 and 0 <= potColumn < 8: # If inside board boundaries
                    target = self.squarePiece[potRow * 8 + potColumn] # Piece on target square
                    if target != empty and (target & 24) != pieceColour: # If there is an ENEMY piece
                        possibleMoves.append((potRow, potColumn))
                    elif self.enPassantTarget == (potRow, potColumn): # Allows en passant
                        possibleMoves.append((potRow, potColumn))

        return possibleMoves

    def fullyLegalMove(self, row, column):
        piece = self.squarePiece[row * 8 + column] # Piece at specified coordinates
        if piece == empty: 
            return [] # No possible moves if no piece
        validMoves = [] # List of all completely legal moves
        
        for endRow, endColumn in self.calculateLegalMoves(row, column): # For all moves that are possible movement
            targetPiece = self.squarePiece[endRow * 8 + endColumn] # Target square
            capturedSquare = None # Square captured from en passant

            if (piece & 7) == pawn and targetPiece == empty and column != endColumn: # If piece is a pawn and moving to empty square and it moves left or right (just if a pawn is capturing)
                if self.enPassantTarget == (endRow, endColumn): # If it is an en passant
                    capturedSquare = (endRow - (-1 if (piece & 24) == white else 1), endColumn) # -1 or 1 depending on direction pawn is moving. Subtracting this means that square that is being captured is 1 below where the pawn moves. En passant rules...
                    targetPiece = self.squarePiece[capturedSquare[0] * 8 + capturedSquare[1]] # Index of target piece

            self.simulateMove(piece, (row, column), (endRow, endColumn), targetPiece, capturedSquare) # Simulate making move. Just moves piece no other stuff (such as turn colour chaging, moves going up...) 
            if not self.kingCheck(piece & 24): # If player making move isn't put in check becuase of move it is a move that is fully legal and can be made
                validMoves.append((endRow, endColumn))
            self.undoMove(piece, (row, column), (endRow, endColumn), targetPiece, capturedSquare) # Undo the move simulation

        return validMoves # Return list of all fully legal moves

    def legalMoves(self, colour):
        for piece, bitboard in self.piecePositions.items():
            if (piece & 24) == colour: # For all the player's bitboards
                board = bitboard # To ensure actual bitboard isn't messed with
                while board: # While there is still at least 1, 1 bit continue
                    lsb = board & -board # '-' flips all bits then adds 1. This means that where the least significant 1 bit is in original number it would be 0 in flipped. but adding 1 means that there is a carry chain that ends at least significant bit and makes it 1. And therefore only has that bit
                    index = lsb.bit_length() - 1 # 'bit_length' returns bits needed to write number. -1 gives index from 0 to 63.
                    if self.fullyLegalMove(index // 8, index % 8): # Finds what moves that specific piece can make that are fully legal. Uses integer division and modulo to ge row and column
                        return True # If a move can be made, there are still legal moves that can be played
                    board &= board - 1 # Clears least significant bit and continues
        return False # If after going through all the pieces that could move and not finding any legal moves, there are no legal moves

    def isPromotable(self, piece, row):
        return (piece == (white | pawn) and row == 0) or (piece == (black | pawn) and row == 7) # If pawn is on the last row it can move to

    def insufficientMat(self):
        if (self.piecePositions[black | pawn] or self.piecePositions[black | rook] or self.piecePositions[black | queen] or self.piecePositions[white | pawn] or self.piecePositions[white | rook] or self.piecePositions[white | queen]): 
            return False # If there are pawns, rooks or queens then there is sufficient material
        totKnights = self.piecePositions[black | knight].bit_count() + self.piecePositions[white | knight].bit_count()
        totBishops = self.piecePositions[black | bishop].bit_count() + self.piecePositions[white | bishop].bit_count()
        return (totBishops + totKnights) < 2 # If amount of knights and bishops is less than 2 then there is insufficient material, Technically not FIDE accurate but I would have to hard code specific scenarios which is too long and annoying 

    def moveCastleRook(self, piece, start, end, undo=False):
        if piece not in (white | king, black | king): 
            return
        row = 7 if piece == (white | king) else 0

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

        self.updateSquare(rookStart[0], rookStart[1], empty)
        self.updateSquare(rookEnd[0], rookEnd[1], (piece & 24) | rook)

    def simulateMove(self, piece, start, end, captured, capturedSquare=None):
        if captured:
            if capturedSquare:
                self.updateSquare(capturedSquare[0], capturedSquare[1], empty)
            else:
                self.updateSquare(end[0], end[1], empty)

        self.updateSquare(start[0], start[1], empty)
        self.updateSquare(end[0], end[1], piece)

        if piece in (white | king, black | king): 
            self.moveCastleRook(piece, start, end)

    def undoMove(self, piece, start, end, captured, capturedSquare=None):
        self.updateSquare(end[0], end[1], empty)
        self.updateSquare(start[0], start[1], piece)

        if captured:
            if capturedSquare:
                self.updateSquare(capturedSquare[0], capturedSquare[1], captured)
            else:
                self.updateSquare(end[0], end[1], captured)

        if piece in (white | king, black | king): 
            self.moveCastleRook(piece, start, end, undo=True)

    def makeMove(self, startRow, startColumn, endRow, endColumn, simulation=False):
        movingPiece = self.squarePiece[startRow * 8 + startColumn]
        target = self.squarePiece[endRow * 8 + endColumn]
        start, end = (startRow, startColumn), (endRow, endColumn)

        enPassantBefore = self.enPassantTarget
        castleRightsBefore = self.castleRights
        self.moveCastleRook(movingPiece, start, end)

        if movingPiece == (white | king): 
            self.castleRights &= ~0b0011
        elif movingPiece == (black | king):
            self.castleRights &= ~0b1100

        if start == (7, 0) or end == (7, 0): 
            self.castleRights &= ~0b0001
        if start == (7, 7) or end == (7, 7): 
            self.castleRights &= ~0b0010
        if start == (0, 0) or end == (0, 0): 
            self.castleRights &= ~0b0100
        if start == (0, 7) or end == (0, 7): 
            self.castleRights &= ~0b1000

        if self.castleRights != castleRightsBefore:
            self.hash ^= zobristCastling[castleRightsBefore]
            self.hash ^= zobristCastling[self.castleRights]

        enPassantCapture = False
        capturedPiece = target
        capturedSquare = None

        if (movingPiece & 7) == pawn and target == empty and startColumn != endColumn and self.enPassantTarget == (endRow, endColumn):
            capturedRow = endRow - (-1 if (movingPiece & 24) == white else 1)
            capturedPiece = self.squarePiece[capturedRow * 8 + endColumn]
            if capturedPiece != empty:
                self.updateSquare(capturedRow, endColumn, empty)
                capturedSquare = (capturedRow, endColumn)
                enPassantCapture = True
                if not simulation: 
                    sounds["capture"].play()

        if not simulation:
            if target != empty:
                sounds["capture"].play()
            else:
                sounds["move"].play()
            visuals.possibleMoves.clear()
            self.redoHistory.clear()

        self.updateSquare(startRow, startColumn, empty)
        promotion = None
        if self.isPromotable(movingPiece, endRow):
            if simulation or self.turnColour == botColour:
                promotion = self.turnColour | queen
            else:
                promotion = visuals.choosePromotion(self.turnColour)

        pieceToPlace = promotion if promotion is not None else movingPiece
        self.updateSquare(endRow, endColumn, pieceToPlace)

        enPassantTarget = None
        if (movingPiece & 7) == pawn and abs(endRow - startRow) == 2:
            enemyPawn = black | pawn if (movingPiece & 24) == white else white | pawn
            if endColumn > 0 and self.squarePiece[endRow * 8 + endColumn - 1] == enemyPawn:
                enPassantTarget = ((startRow + endRow) // 2, startColumn)
            elif endColumn < 7 and self.squarePiece[endRow * 8 + endColumn + 1] == enemyPawn:
                enPassantTarget = ((startRow + endRow) // 2, startColumn)

        self.setEnPassantTarget(enPassantTarget)
        self.switchTurn()
        self.halfmoveClock = 0 if (movingPiece & 7) == pawn or target != empty or enPassantCapture else self.halfmoveClock + 1
        currentHash = self.hash
        self.positionCounts[currentHash] = self.positionCounts.get(currentHash, 0) + 1

        if simulation:
            return (
                movingPiece, 
                start, 
                end, 
                capturedPiece, 
                capturedSquare, 
                enPassantBefore,
                self.halfmoveClock, 
                castleRightsBefore, 
                currentHash
            )
        else:
            self.moveHistory.append((
                movingPiece, 
                start, 
                end, 
                capturedPiece, 
                capturedSquare,
                enPassantBefore,
                castleRightsBefore, 
                promotion, 
                self.castleRights, 
                self.enPassantTarget, 
                self.halfmoveClock
            ))
            self.positionHistory.append(currentHash)
            self.moves += 1                
            if self.endgame != evaluation.isEndgame(self):
                self.createSquareTable()
            visuals.activeSquare = None
            visuals.possibleMoves.clear()
            visuals.lastMove = (startRow, startColumn, endRow, endColumn)
            visuals.redraw = True

    def unmakeMove(self, undoInfo):
        movingPiece, start, end, capturedPiece, capturedSquare, enPassantBefore, halfmoveClock, castleRightsBefore, currentHash = undoInfo
        self.positionCounts[currentHash] -= 1
        if self.positionCounts[currentHash] == 0:
            del self.positionCounts[currentHash]
            
        self.switchTurn()
        self.halfmoveClock = halfmoveClock
        if self.castleRights != castleRightsBefore:
            self.hash ^= zobristCastling[self.castleRights]
            self.hash ^= zobristCastling[castleRightsBefore]
            self.castleRights = castleRightsBefore
        self.setEnPassantTarget(enPassantBefore)

        self.updateSquare(end[0], end[1], empty)
        self.updateSquare(start[0], start[1], movingPiece)
        
        if capturedPiece != empty:
            if capturedSquare:
                self.updateSquare(capturedSquare[0], capturedSquare[1], capturedPiece)
            else:
                self.updateSquare(end[0], end[1], capturedPiece)

        self.moveCastleRook(movingPiece, start, end, undo=True)

    def gameState(self):
        
        if self.positionCounts.get(self.hash, 0) >= 3:
            self.gameOverMessage = "Three-fold \nRepetition!\nNobody  wins!"
            sounds["checkmate"].play()
            return

        inCheck = self.kingCheck(self.turnColour)
        if not self.legalMoves(self.turnColour):
            if inCheck:
                winner = "Black" if self.turnColour == white else "White"
                self.gameOverMessage = f"Checkmate!\n{winner}  wins!"
                sounds["checkmate"].play()
            else:
                self.gameOverMessage = "Stalemate!\nNobody  wins!"
                sounds["checkmate"].play()
        elif inCheck: 
            sounds["check"].play()
        elif self.halfmoveClock >= 100:
            self.gameOverMessage = "50-move rule\nDraw!"
            sounds["checkmate"].play()
        elif self.insufficientMat():
            self.gameOverMessage = "Insufficient  Material! \n Nobody  wins"
            sounds["checkmate"].play()
        else: 
            self.gameOverMessage = None

    def previousMove(self):
        if not self.moveHistory: 
            return

        move = self.moveHistory.pop()

        if self.positionHistory: 
            oldHash = self.positionHistory.pop()
            self.positionCounts[oldHash] -= 1
            if self.positionCounts[oldHash] == 0:
                del self.positionCounts[oldHash]

        self.redoHistory.append(move)

        piece, start, end, capturedPiece, capturedSquare, enPassantBefore, castleRightsBefore, promotion, castleRightsAfter, enPassantAfter, halfmoveClock = move
        self.switchTurn()
        self.moves -= 1
        self.halfmoveClock = halfmoveClock - 1

        if self.castleRights != castleRightsBefore:
            self.hash ^= zobristCastling[self.castleRights]
            self.hash ^= zobristCastling[castleRightsBefore]
            self.castleRights = castleRightsBefore

        self.setEnPassantTarget(enPassantBefore)

        self.updateSquare(end[0], end[1], empty)
        self.updateSquare(start[0], start[1], piece)
            
        if capturedPiece != empty:
            if capturedSquare:
                self.updateSquare(capturedSquare[0], capturedSquare[1], capturedPiece)
            else:
                self.updateSquare(end[0], end[1], capturedPiece)
            sounds["capture"].play()
        else:
            sounds["move"].play()

        self.moveCastleRook(piece, start, end, undo=True)

        if self.endgame != evaluation.isEndgame(self):
            self.createSquareTable()
        from engine import visuals
        visuals.activeSquare = None
        visuals.possibleMoves.clear()
        visuals.lines.clear()
        visuals.strategyCircles.clear()
        constants.premoves.clear()
        self.gameState()
        
        if len(self.moveHistory) > 0:
            secondLastMove = self.moveHistory[-1]
            visuals.lastMove = (secondLastMove[1][0], secondLastMove[1][1], secondLastMove[2][0], secondLastMove[2][1])
        else:
            visuals.lastMove = None
        visuals.redraw = True

    def redoMove(self):
        from engine import visuals
        if not self.redoHistory: 
            return

        move = self.redoHistory.pop()
        piece, start, end, capturedPiece, capturedSquare, enPassantBefore, castleRightsBefore, promotion, castleRightsAfter, enPassantAfter, halfmoveClock = move

        self.switchTurn()
        self.moves += 1
        self.halfmoveClock = halfmoveClock

        if castleRightsBefore != castleRightsAfter:
            self.hash ^= zobristCastling[castleRightsBefore]
            self.hash ^= zobristCastling[castleRightsAfter]
            self.castleRights = castleRightsAfter

        self.setEnPassantTarget(enPassantAfter)

        if capturedPiece != empty:
            sounds["capture"].play()
        else: 
            sounds["move"].play()

        self.moveCastleRook(piece, start, end)
        self.updateSquare(start[0], start[1], empty)

        if capturedPiece != empty and capturedSquare:
            self.updateSquare(capturedSquare[0], capturedSquare[1], empty)
        if promotion is not None:
            self.updateSquare(end[0], end[1], promotion)
        else:
            self.updateSquare(end[0], end[1], piece)

        self.moveHistory.append(move)
        currentHash = self.hash
        self.positionHistory.append(currentHash)
        if currentHash in self.positionCounts:
            self.positionCounts[currentHash] += 1
        else:
            self.positionCounts[currentHash] = 1
                
        if self.endgame != evaluation.isEndgame(self):
            self.createSquareTable()
        visuals.activeSquare = None
        visuals.possibleMoves.clear()
        visuals.lines.clear()
        visuals.strategyCircles.clear()
        constants.premoves.clear()
        visuals.lastMove = (start[0], start[1], end[0], end[1])
        
        self.gameState()
        visuals.redraw = True