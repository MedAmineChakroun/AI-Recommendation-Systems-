@echo off
REM Activate conda environment
CALL C:\Users\hp\anaconda3\Scripts\activate.bat recsys

REM Start first app in new window
start cmd /k "cd /d C:\Users\hp\Recommendations\SVD_recommender && python app.py"

REM Start second app in new window
start cmd /k "cd /d C:\Users\hp\Recommendations\Apriori_recommender && python app.py"
