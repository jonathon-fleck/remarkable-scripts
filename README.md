# remarkable-scripts

## Dependencies

- `rmrl`: especially this [branch](https://github.com/naturale0/rmrl) to handle
the new colors added in remarkable 2
```
pip install git+https://github.com/naturale0/rmrl.git
```
- An entry in your `~/.ssh/config` file for the remarkable listed as `remarkable`
or otherwise adjust the update script
- (For convenience) a `~/.remarkable_params.sh` file containing the following:

```
set -a

RMKBL_REMOTE_DIR=.local/share/remarkable/xochitl/
RMKBL_LOCAL_DIR=/path/for/local/copy/of/raw_remarkable_files
RMKBL_FILE_DIR=/path/for/root/of/remarkable_file_tree

set +a
```

## Files

- `update.sh`: syncs remarkable xochitl directory with local machine (calling
rsync with expected source and destination) and can officially delete files which
have been deleted on the remarkable (they persist for the purposes of syncing
remarkable with cloud service).
- `construct_file_tree.py`: using the local copy of the xochitl directory,
constructs the file tree hierarchy as displayed on the remarkable and
creates the corresponding pdfs using the rmrl utility. 
