#!/bin/bash
rsync -aruvz -e ssh --delete remarkable:.local/share/remarkable/xochitl/ /home/jonathon/ubox_personal_local/remarkable/raw_copy
