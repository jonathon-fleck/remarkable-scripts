#!/bin/bash

help () {
    echo "Usage: $( basename $0 ) [-c | --clean] [-h]"
    echo "    -h)           displays this message"
    echo "    -c | --clean) cleans up deleted files on remarkable"
}

VALID_ARGS=$(getopt -o ch --long clean -- "$@")
if [[ $? -ne 0 ]]; then
    help
    exit 1;
fi

CLEAN=0

eval set -- "$VALID_ARGS"
while [ : ]; do
  case "$1" in
    -c | --clean)
        CLEAN=1
        shift
        ;;
    -h)
        help
        exit 0
        ;;
    --) shift;
        break
        ;;
  esac
done

if [ -f ~/.remarkable_params.sh ]
then
    source ~/.remarkable_params.sh
else
    echo "Please add a file ~/.remarkable_params.sh which specifies REMOTE_DIR, LOCAL_COPY_DIR, DEST_DIR"
    echo "... or change this file"
    echo ""
    echo "WARNING: Did NOT update!"
fi

if [ $CLEAN -eq 1 ]
then
    ssh remarkable 'cd ~/.local/share/remarkable/xochitl; for file in $( ls *.metadata ); do if [ -n "$( grep "deleted.: true" $file )" ]; then
    UUID=$( basename $file .metadata ); rm -r ${UUID}*; fi;  done'
else
    ssh remarkable 'cd ~/.local/share/remarkable/xochitl; for file in $( ls *.metadata ); do if [ -n "$( grep "deleted.: true" $file )" ]; then
    UUID=$( basename $file .metadata ); echo "$UUID to be deleted..."; fi;  done'
fi

rsync -aruvz -e ssh --delete remarkable:$RMKBL_REMOTE_DIR $RMKBL_LOCAL_DIR
