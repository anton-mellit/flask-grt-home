NOW=$(date +"%Y-%m-%d-%H")
LOGFILE="logs/www/log-reindex-$NOW.log"

python3 search.py > $LOGFILE 2>&1
