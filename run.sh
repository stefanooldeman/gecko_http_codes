#!/usr/bin/env bash

# if the first argument is not present.. then use yesterday
# usefull for reprocessing old logs
YESTERDAY_DATE=${1:-`date -s yesterday +"%Y%m%d" 2> /dev/null`}
LOGS_DIR=/usr/local/share/s2mdata/track_logs
DB_DIR=/home/ubuntu/graph_http_codes

mkdir -p $DB_DIR
echo "this file is maintained by a script called gecko_http_codes scripts" > $DB_DIR/README

SUMMARY_FILE=`mktemp --suffix _http_codes_${YESTERDAY_DATE}`
for LFILE in ${LOGS_DIR}/track-*_${YESTERDAY_DATE}*; do
  echo "`date` - INFO - processing $LFILE"
  gunzip -c $LFILE | grep -E "(GET \/toi)|(GET \/v3\/update_order)" \
    | grep -v "Google" \
    | egrep "HTTP/.*\" [2|3|4|5|][0-9]{2}" -o | awk -F" " "{print \$2}" \
    >> $SUMMARY_FILE;
done

# Update the login welcom's message, see ansible for configuration of this
echo "`date` - INFO - sorting summary"
STATS_FILE=`mktemp --suffix _http_codes_uniq_${YESTERDAY_DATE}`
sort $SUMMARY_FILE | uniq -c > $STATS_FILE
  cat << EOF > /home/ubuntu/graph_http_codes/motd_tracker_health.txt
Yesterdays summary of HTTP Status (${YESTERDAY_DATE}).

  Total hits (filtered): `wc -l $SUMMARY_FILE | awk -F' ' '{print $1}'`

  Hits split by status code (count, code):
  `cat $STATS_FILE`

EOF


echo "`date` - storing and updating graphs"
python update_graph_data.py --history $DB_DIR/graph_history.pickle \
  --date ${YESTERDAY_DATE} \
  --api-key <your-api-key> $STATS_FILE \
  | xargs curl http://push.geckoboard.com/v1/send/<your-url-part> -d

# newline to cover any stdoutput from api response
echo 

if [ $? = 0 ]; then
  echo "`date` - INFO - cleanup files"
  rm $SUMMARY_FILE
  rm $STATS_FILE
else
  echo "`date` - ERROR - processing $STATS_FILE or API call failed"
  cat << EOF > /home/ubuntu/graph_http_codes/motd_tracker_health.txt
to retry, run:
  python update_graph_data.py --history $DB_DIR/graph_history.pickle \
    --date ${YESTERDAY_DATE} \
    --api-key <api-key-here> $STATS_FILE \
    \| xargs curl http://push.geckoboard.com/v1/send/<your-own-unique-url-id> -d

tmp files not removed:
  - $SUMMARY_FILE
  - $STATS_FILE

EOF
fi

echo "`date` - DONE"
