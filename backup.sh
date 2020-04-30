NOW=$(date +"%Y-%m-%d")
FILE="backup/backup-$NOW.tar.gz"

tar -cvzf $FILE data

