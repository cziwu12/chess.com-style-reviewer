# Chess.com Style Reviewer

![alt text](image-1.png)

## Features
- Load PGN 
- Analysis from Stockfish Engine 
- Shows Engine Best Move
- Move Evaluation and Classification
- WDL Probability (Win/Draw/Loss)
- Game Accuracy  
- SVG Board
- Move and Check Highlights

## Requirements

Windows 10/11

## Installation

- Download and extract application
- Run the application (Windows might show a "Windows protected your PC" window but until I purchase a Code Signing Certificate, just click "Run Anyway"). Make sure you DON'T move the .exe to a different location as it needs to be in the same location with _internal else the app won't run.

## Usage 

### What you need:
- A PGN file

#### How to get PGN file

- Go to your games in Chess.com/Lichess/preferred chess platform 
- Click Share
- Select PGN and download the file

![alt text](image-3.png)

Now you have a PGN file of your game:

- Open the application and click on the "Load PGN" button
- Select your PGN file 
- Wait for it to analyse

## Interface Guide

![alt text](image-2.png)

### Left Side

- Load PGN: Load the PGN
- Event Label: Shows the header of the game
- White Game Accuracy: Shows white's game accuracy 
- Black Game Accuracy: Shows black's game accuracy 
- Move list (Bottom Left): List all moves in the game. Click on a move to show analysis result info

### Right Side

- Analysis Result (Top Right): Shows the output of from the engine. Shows Player and engine move, Evaluation, Classification (ranging from "Best" to "Blunder"), Move Accuracy and Win/Draw/Loss Percent
- SVG Board (Bottom Right): Shows an SVG board of the move. Highlights move in green and check in red.

## How it works

- User submits a PGN file which is processed by Stockfish to extract centipawn scores (Cp), Win/Draw/Loss probabilities (WDL) and the best engine moves.
- Move accuracy is evaluated using an exponential curve that overlays expected score loss against the actual move, resulting in an accuracy score per move.
- Moves are categorized independently based on their Cp score and matescore.
- The analysis function returns a dictionary containing all calculated data to the frontend for formatting and display.
- Game-wide accuracy is calculated using a sigmoid (S-shaped) curve to assign "weights" to the move scores. The final score is the sum of these weighted accuracies divided by the number of moves.

## Tech Stack

- Python
- PySide6
- python-chess
- Stockfish

## For Devs:

This project requires Stockfish.

Download the latest Windows x64 binary from:
https://github.com/official-stockfish/Stockfish/releases

Extract the executable into this folder before running the project.

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3).

It bundles the Stockfish chess engine, which is also licensed under GPLv3.
