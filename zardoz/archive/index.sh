#!/bin/sh

	echo "file : date : title"
for i in 1 2 3; 
do
    for j in 0 1 2 3 4;
    do
        for k in 0 1 2 3 4 5 6 7 8 9;
        do
            _FILE_NAME="${i}${j}${k}.txt"
            if [ -f "$_FILE_NAME" ]
            then
                _DATE=`grep Date "$_FILE_NAME" | head -1 | \
                    perl -ne 'if (/Date.* ([0-9]{1,2}) ([A-Za-z]{3}) ([0-9]{2,4})/) 
                                { $d = $1; $m = $2; $y = $3;
                                    if ($y < 100) { $y = $y + 1900; } 
                                    printf "%02d/%s/%4d\n", $d, $m, $y; 
                                }
                              elsif (/Date.* [A-Za-z]{3} ([A-Za-z]{3}) ([0-9]{1,2}) .*(19[0-9]{2})/)
                                { $d = $2; $m = $1; $y = $3;
                                  printf "%02d/%s/%4d\n", $d, $m, $y;
                                }
                            '`
		_TITLE=`grep Subject "$_FILE_NAME" | head -1 | \
		    sed 's/.*Subject:[ ]*//g' `
               	echo -n "$_FILE_NAME | "
		echo -n "$_DATE | "
		echo -n "$_TITLE"
		echo ""
            fi
        done
    done
done

