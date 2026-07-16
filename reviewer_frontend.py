import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget, 
    QMainWindow, 
    QPushButton, 
    QLabel, 
    QListWidget, 
    QTextEdit, 
    QVBoxLayout, 
    QHBoxLayout, 
    QFileDialog,
    QProgressBar,
)
from PySide6.QtSvgWidgets import QSvgWidget
from reviwer_backend import review_game
from analysis import engine
import chess.svg

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chess Reviewer")

        self.load_button = QPushButton("Load PGN")

        self.event_label = QLabel("Event")
        self.white_label = QLabel("White Accuracy")
        self.black_label = QLabel("Black Accuracy")
        self.board = QSvgWidget()
        self.board.setMinimumSize(500,500)

        self.move_list = QListWidget()

        self.move_info = QTextEdit()
        self.move_info.setReadOnly(True)

        left = QVBoxLayout()
        left.addWidget(self.load_button)
        left.addWidget(self.event_label)
        left.addWidget(self.white_label)
        left.addWidget(self.black_label)
        left.addWidget(self.move_list)

        right = QVBoxLayout()
        right.addWidget(self.move_info)
        right.addWidget(self.board)

        layout = QHBoxLayout()
        layout.addLayout(left)
        layout.addLayout(right)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        self.load_button.clicked.connect(self.load_pgn)
        self.move_list.currentRowChanged.connect(self.show_move)

    def load_pgn(self):
        self.move_list.clear()

        self.move_info.clear()

        self.board.load(b"")

        self.moves = []

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open PGN",
            "",
            "PGN Files (*.pgn)"
        )

        if not filename:
            return

        result = review_game(filename)
        self.event_label.setText(
            result["headers"]["Event"]
        )

        self.white_label.setText(
            f"White Accuracy: {result['white_accuracy']:.2f}%"
        )

        self.black_label.setText(
            f"Black Accuracy: {result['black_accuracy']:.2f}%"
        )

        self.moves = result["moves"]

        self.move_list.clear()

        for move in self.moves:
            self.move_list.addItem(
                f"{move['Move']}. {move['Player Move']} ({move['Classification']})"
            )        

    def show_move(self, index):
        if index < 0:
            return
        move = self.moves[index]

        text = f"""
    Player Move:
    {move["Player Move"]}

    Best Move:
    {move["Best Move"]}

    Evaluation:
    {move["Eval Before"]} -> {move["Eval After"]}

    Classification:
    {move["Classification"]}

    Accuracy:
    {move["Accuracy"]}%

    Win:
    {move["WDL Win Prob"]}%

    Draw:
    {move["WDL Draw Prob"]}%

    Loss:
    {move["WDL Loss Prob"]}%
    """

        self.move_info.setPlainText(text)
        board = chess.Board(move["Board FEN"])

        svg = chess.svg.board(
            board,
            size=500
        )

        self.board.load(bytearray(svg, encoding="utf-8"))



app = QApplication(sys.argv)

window = MainWindow()

app.setStyleSheet("""
QMainWindow {
    background-color: #121212;
}

QWidget {
    background-color: #121212;
    color: white;
    font-size: 12pt;
}

QPushButton {
    background-color: #1E88E5;
    color: white;
    border-radius: 8px;
    padding: 8px;
}

QPushButton:hover {
    background-color: #42A5F5;
}

QListWidget {
    background-color: #1E1E1E;
    border: 1px solid #333;
}

QTextEdit {
    background-color: #1E1E1E;
    border: 1px solid #333;
}

QLabel {
    color: white;
}
""")

window.show()

app.exec()
engine.quit()