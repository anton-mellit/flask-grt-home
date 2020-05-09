NOW=$(date +"%Y-%m-%d")
LOGFILE="logs/log-digest-$NOW.log"

python3.8.2 send_digest.py > $LOGFILE 2>&1
