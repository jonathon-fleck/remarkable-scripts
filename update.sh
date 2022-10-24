#!/bin/bash

if [ -f ~/.remarkable_params.sh ]
then
    source ~/.remarkable_params.sh
else
    echo "Please add a file ~/.remarkable_params.sh which specifies REMOTE_DIR, LOCAL_COPY_DIR, DEST_DIR"
    echo "... or change this file"
    echo ""
    echo "WARNING: Did NOT update!"
fi

rsync -aruvz -e ssh --delete remarkable:$REMOTE_DIR $LOCAL_COPY_DIR
