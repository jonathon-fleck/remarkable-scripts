#!/bin/bash

help () {
    echo "Usage: $( basename $0 ) [-w | --warn] [-c | --clean] [-h]"
    echo "    -h)           displays this message"
    echo "    -w | --warn)  warns of files to be deleted if --clean is used"
    echo "    -c | --clean) cleans up deleted files on remarkable (--warn overrides --clean)"
}

VALID_ARGS=$(getopt -o wch --long warn,clean -- "$@")
if [[ $? -ne 0 ]]; then
    help
    exit 1;
fi

CLEAN=0
WARN=0

eval set -- "$VALID_ARGS"
while [ : ]; do
  case "$1" in
    -w | --warn)
        WARN=1
        shift
        ;;
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

if [ $WARN -eq 1 ]
then
    ssh remarkable 'cd ~/.local/share/remarkable/xochitl; for file in $( ls *.metadata ); do if [ -n "$( grep "deleted.: true" $file )" ]; then
    UUID=$( basename $file .metadata ); echo "$UUID to be deleted..."; fi;  done'
else
    if [ $CLEAN -eq 1 ]
    then
        ssh remarkable 'cd ~/.local/share/remarkable/xochitl; for file in $( ls *.metadata ); do if [ -n "$( grep "deleted.: true" $file )" ]; then
        UUID=$( basename $file .metadata ); rm -r ${UUID}*; fi;  done'
    fi
fi

rsync -aruvz -e ssh --delete remarkable:$RMKBL_REMOTE_DIR $RMKBL_LOCAL_DIR
