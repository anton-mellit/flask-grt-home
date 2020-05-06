NOW=$(date +"%Y-%m-%d")
LOGFILE="logs/www/log-digest-$NOW.log"

python3.8.2 search.py > $LOGFILE
