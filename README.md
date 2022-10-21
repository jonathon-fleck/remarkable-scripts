# remarkable-scripts

## Dependencies

- `rmrl`: especially this [branch](https://github.com/naturale0/rmrl) to handle
the new colors added in remarkable 2
- An entry in your ~/.ssh/config file for the remarkable listed as `remarkable`
or otherwise adjust the update script

## Files

- `update.sh`: syncs remarkable xochitl directory with local machine (just calls
rsync with expected source and destination)
- `construct_file_tree.py`: using the local copy of the xochitl directory,
constructs the file tree hierarchy as displayed on the remarkable and
creates the corresponding pdfs using the rmrl utility. 
