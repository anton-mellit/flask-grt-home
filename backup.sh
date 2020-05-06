NOW=$(date +"%Y-%m-%d")
FILE="backup/backup-$NOW.tar.gz"
LOGFILE="logs/log-backup-$NOW.log"

tar -cvzf $FILE data > $LOGFILE
