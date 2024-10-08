#!/usr/bin/env python3
# TODO : GraphNode changes (plus rename to 'RemarkableTreeNode' or something like this...)
# TODO : add support for remote source (i.e., the remarkable...)
# TODO : add support for saving source and pdf of files no longer on remarkable
#        (and restoring on remarkable thereafter)
"""
    Test newly change process_extra_files (changed from delete_extra_files)
        + add calls/inputs for this
    Test newly changed update.sh to make sure it works as expected (backing up ...)
"""

import json, sys, os, signal, argparse, configparser, time, shutil
import subprocess
import rmrl

class GraphNode:
    """
    A class used to represent a graph node, specifically to represent a remarkable file object.

    Attributes
    ----------
    __id : str
        identifier for this file object (not human readable)
    __name : str
        human readable string to name this file
    __children : list(GraphNode)
        list of GraphNode instances (children of this node)
    __deleted : bool
        records whether *.metadata indicates this file was deleted
    __parent_id : str
        identifier of this file object's parent
    __parent : GraphNode
        parent node
    __last_modified : int
        integer representing the last time when the remarkable document was last modified

    Methods
    -------
    get_parent_id()
        returns string identifier of its parent
    get_name()
        returns string name of this node
    
    add_child(node : GraphNode)
        adds GraphNode instance as a child of this node

    get_str(pref="" : str)
        returns a string representation of this file tree (via traversal)
    create_structure(source_dir : str, dest_dir : str)
        creates the file structure locally and uses rmrl to build pdfs from remarkable files
    """
    __id = None
    __name = None
    __children = None
    __deleted = None
    __parent_id = None
    __parent = None
    __last_modified = None

    def __init__(self, _id, _name, _type_str, _deleted, _parent_id, _last_modified=None):
        """
        Parameters
        ----------
        _id : str
            remarkable identifier of this node
        _name : str
            to be the name of this file/directory
        _type_str : str
            string indicating this node's type ('type' field in <_id>.metadata)
        _deleted : str/bool
            string/bool indicating whether this node has been deleted ('deleted' field in <_id>.metadata)
        _parent_id : str
            id of this node's parent
        _last_modified : int
            time when the remarkable file was last modified
        """
        self.__id = _id
        self.__name = _name

        if _type_str == 'DocumentType':
            self.__children = None
        elif _type_str == 'CollectionType':
            self.__children = []
        else:
            print("Unexpected type \"%s\" for file \"%s\" with id=%s" %\
                    (_type_str, self.__name, self.__id))
    
        self.__deleted = _deleted not in (False, "false", "False")
        self.__parent_id = _parent_id
        self.__last_modified = _last_modified

    def get_parent_id(self):
        return self.__parent_id

    def get_name(self):
        return self.__name

    def is_deleted(self):
        return self.__deleted

    def add_child(self, node):
        """
        Adds a child to this node.  Prints warning message in case you attempted to add a child to a
        non-child type.

        TODO: make return value an exception

        Parameters
        ----------
        node : GraphNode
            GraphNode of child to add

        Returns
        -------
        True/False if addition was successful
        """

        if self.__children is None:
            print("Tried to add a child to a non-collection type!")
            success = False
        else:
            self.__children.append(node)
            success = True

        return success

    def set_parent(self, node):
        self.__parent = node

    def get_str(self, pref=""):
        """
        Returns a string representation of this tree (from this node) with 'pref' prepended to each
        line via a tree traversal.

        Parameters
        ----------
        pref : str
            prefix string for each line
        """
        out_str = "%s%s (%s)" % (pref, self.__name, self.__id)

        if self.is_deleted():
            out_str = "[ %s ]\n" % (out_str)
        else:
            out_str += "\n"

        if self.__children:
            for child in self.__children:
                out_str += child.get_str(pref+"+---")

        return out_str

    def create_structure(self, source_dir, dest_dir, verbose=False, time_ref=None):
        """
        Traverses tree and creates a model of the (displayed) filesystem on the remarkable.

        Parameters
        ----------
        source_dir : str
            path to directory which has the raw xochitl copy from the remarkable
        dest_dir : str
            path to directory where you want this file/dir to sit

        Returns
        -------
        list of files to be created with rmrl (after checking if necessary)
            each entry is a tuple (pdf_name, err_name, id_file)
        """

        fileinfo_to_create = []
        if not self.is_deleted():
            if self.__children is None: # Then this represents a file

                pdf = f"{dest_dir}/{self.__name}.pdf"
                err = f"{dest_dir}/{self.__name}.err"

                src_id = f"{source_dir}/{self.__id}"
                src_md = f"{src_id}.metadata"


                # If no time_ref or id not recorded in time_ref use default (old version)
                if (time_ref is None) or (self.__id not in time_ref.keys()):
                    # Script: check if pdf doesn't exist or metadata file is newer
                    script = f"PROCESS=0; if [ ! -s {pdf} ] || [ {src_md} -nt {pdf} ]; then PROCESS=1; fi; exit $PROCESS"
                    update = os.system(script)
                else:
                    # update if last logged time is older (i.e., less) than last modified time or if no file
                    # exists at last registered location
                    update = (time_ref[self.__id]['time'] < self.__last_modified) or \
                            (not os.path.isfile(time_ref[self.__id]['pdf']))

                    # If above did not flag update, file locations are different, and new location is not
                    # a file, change the name locally
                    if (not update) and time_ref[self.__id]['pdf'] != pdf and (not os.path.isfile(pdf)):
                        os.rename(time_ref[self.__id]['pdf'], pdf)

                if time_ref is not None:
                    if self.__id not in time_ref:
                        time_ref[self.__id] = {'last_time': None, 'last_pdf': None}
                    else:
                        time_ref[self.__id] = {'last_time': time_ref[self.__id]['time'], 'last_pdf': time_ref[self.__id]['pdf']}

                    time_ref[self.__id].update({'time': self.__last_modified, 'pdf': pdf, 'updated': update})

                if update:
                    num_pages = int(subprocess.check_output(f"ls {src_id} | wc -l", shell=True)) // 2
                    fileinfo_to_create.append((pdf, err, src_id, num_pages))

            else:
                # This represents a directory

                if self.__name != "": # not root
                    new_dir = '%s/%s' % (dest_dir, self.__name)
                else:
                    new_dir = dest_dir

                if not os.path.isdir(new_dir):
                    os.mkdir(new_dir)

                for child in self.__children:
                    fileinfo_to_create.extend(child.create_structure(source_dir, new_dir, verbose, time_ref))

        return fileinfo_to_create

    def process_extra_files(self, dirname, verbose=False, warn_only=True, archive_dir=None):
        """
        TESTME!!!

        Traverses directory and deletes (or archives) unexepected files/directories below
        dirname.

        Parameters
        ----------
        dirname : str
            Directory of filesystem where we expect to find the children of this node
        verbose : bool
            If true prints info about each deletion
        warn_only : bool
            If true, only prints which files would be deleted
        archive_dir : str
            Directory of filesystem to move unexepcted files to instead of deleting them
            (if None, then the files will be deleted)
        """
        if self.__children is not None:
            filenames = os.listdir(dirname)
            for f_name in filenames:
                if f_name.endswith(".pdf"):
                    f_basename = f_name[:-4]
                else:
                    f_basename = f_name

                i=0
                while i < len(self.__children) and self.__children[i].__name != f_basename:
                    i+= 1
                found = i < len(self.__children)

                if not found:
                    if verbose:
                        print(f"Removing {f_name} in {dirname}...")

                    if warn_only:
                        print(f"Would remove {f_name} in {dirname}")
                    else:
                        # NEW CODE ----------------------\/
                        if archive_dir is None:
                            if os.path.isdir(f"{dirname}/{f_name}"):
                                #os.rmdir(f"{dirname}/{f_name}")
                                shutil.rmtree(f"{dirname}/{f_name}")
                            elif os.path.isfile(f"{dirname}/{f_name}"):
                                os.remove(f"{dirname}/{f_name}")
                            else:
                                print(f"Unexpected file type for {dirname}/{f_name}!")
                        else:
                            if not os.path.isdir(archive_dir):
                                os.makedirs(archive_dir)
                            shutil.move(f"{dirname}/{f_name}", f"{archive_dir}/{f_name}")
                        # END NEW CODE -------------------/\

            for child in self.__children:
                if archive_dir is not None:
                    new_archive_dir = f"{archive_dir}/{child.__name}"
                else:
                    new_archive_dir = None
                child.process_extra_files(f"{dirname}/{child.__name}", verbose, warn_only,
                        archive_dir=new_archive_dir)

def construct_node(ident, source_dir):
    """
    Constructs a GraphNode by first reading the corresponding metadata file
    and passing the relavent parameters to the GraphNode init.

    Parameters
    ----------
    ident : str
        remarkable identifier
    source_dir : str
        string path to directory containing remarkable xochitl files

    Returns
    -------
    Corresponding GraphNode instance
    """
    with open('%s/%s.metadata' % (source_dir, ident)) as f:
        data = f.read()

    meta_data = json.loads(data)

    return GraphNode(ident, meta_data['visibleName'].replace(' ', '_'), meta_data['type'],
            meta_data['deleted'], meta_data['parent'], int(meta_data['lastModified']))

def get_node_dict(source_dir):
    """
    Reads contents of source_dir to get list of remarkable ids then creates
    dictionary mapping ids to GraphNode instances via construct_node.

    Parameters
    ----------
    source_dir : str
        path to copy of remarkable xochitl folder
    """
    node_dict = {}

    for name in os.listdir(source_dir):
        ident = os.path.basename(name).split('.')[0]
        if len(ident) > 0 and ident not in node_dict:
            node_dict[ident] = construct_node(ident, source_dir)

    return node_dict

def make_graph(node_dict):
    """
    Populates relevant node children to recreate file tree structure.

    Parameters
    ----------
    node_dict : dict(k=str, v=GraphNode)
        dictionary mapping remarkable id strings to GraphNode instances

    Returns
    -------
    Root (GraphNode) of filesystem
    """
    root = GraphNode("", "", "CollectionType", "False", "None")
    node_dict[""] = root
    node_dict["trash"] = GraphNode("trash", "trash", "CollectionType", "False", "")

    for ident, node in node_dict.items():
        parent_id = node.get_parent_id()
        if parent_id in node_dict:
            node_dict[parent_id].add_child(node)
            node.set_parent(node_dict[parent_id])
        elif ident != "":
            print("Could not find parent \"%s\" in node_dict, node=%s!" % (parent_id, node.get_name()))

    return root

def get_time_str(time):
    return f"{time/3600:.0f}h{(time%3600)/60:02.0f}m{time%60:04.1f}s"

def create_pdfs(fileinfo_to_create):
    """
    Creates the pdfs given the list of fileinfo, printing out a progress bar throughout.
    """

    num_files = len(fileinfo_to_create)
    files_completed = 0
    num_pages_gend = 0

    total_num_pages = 0
    for pdf, err, src_id, num_pages in fileinfo_to_create:
        total_num_pages += num_pages

    start_time = time.time()
    for pdf, err, src_id, num_pages in fileinfo_to_create:
        pdf_str = os.path.basename(pdf)[:20] + "..."

        def rmrl_cb(percentage):
            est_num_pages_gend = num_pages_gend + int(num_pages*percentage/100.0)
            if est_num_pages_gend < 100:
                est_time_per_page = 0.7
            else:
                est_time_per_page = (time.time() - start_time)/est_num_pages_gend

            etr = (total_num_pages - est_num_pages_gend)*est_time_per_page
            etr_str = get_time_str(etr)

            printProgressBar(est_num_pages_gend, total_num_pages, prefix=f"{pdf_str:23} (ETR: {etr_str})", length=75-len(etr_str))

        output = rmrl.render(src_id, progress_cb=rmrl_cb)
        with open(pdf, "wb") as f:
            f.write(output.read())

        #new_pages_gend = int(subprocess.check_output(f"pdfinfo {pdf} | grep Pages | sed 's/[^0-9]*//'", shell=True))
        #total_pages_gend += new_pages_gend
        num_pages_gend += num_pages

        files_completed += 1

    return num_pages_gend, time.time() - start_time

def read_time_file(f_name):
    time_ref = {}
    
    if os.path.isfile(f_name):
        with open(f_name) as f:    
            data = f.read()
            time_ref = json.loads(data)

    return time_ref

def write_time_file(time_ref, f_name):
    with open(f_name, "w") as f:
        json.dump(time_ref, f, indent=4)

def signal_handler(signal, frame):
    sys.exit(0)

def printProgressBar(iteration, total, prefix="", suffix="", decimals=1,
        length=100, fill="█", printEnd="\r"):
    """
    Call in a loop to create terminal progress bar

        https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters

    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def resolve_cmdline_args():
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(
            description='Construct file tree from remarkable system, converting remarkable formats to pdfs')
    parser.add_argument('-s', '--source', dest='source_dir',
            help='path to (copy of) remarkable xochitl folder')
    parser.add_argument('-d', '--dest', dest='dest_dir',
            help='path to where you want the new file tree')
    parser.add_argument('--nosync', action='store_true', dest='no_sync',
            help="does not delete extra files in dest_dir")
    parser.add_argument('--sync_warn', action='store_true', dest='sync_warn',
            help="warns of files to be deleted if sync enabled")
    parser.add_argument('-t', '--time_file', dest='time_file',
            help="file containing reference times to avoid creating file if only the metadata was updated")
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='print status output')
    parser.add_argument('--debug', dest='debug', action='store_true', help='print debug output')
    args = parser.parse_args()

    # Pull default values from ~/.remarkable_params.sh
    default_arg_file = os.path.expanduser("~/.remarkable_params.sh")
    if os.path.isfile(default_arg_file):
        with open(default_arg_file) as f:
            for line in f.readlines():
                if line.startswith("RMKBL_LOCAL_DIR") and args.source_dir is None:
                    args.source_dir = line.strip().split("=")[1]
                if line.startswith("RMKBL_FILE_DIR") and args.dest_dir is None:
                    args.dest_dir = line.strip().split("=")[1]

    if args.debug:
        print("===== Args =========")
        for k, v in vars(args).items():
            print(f"{k:<10}\t{v}")
        print("====================")

    invalid_args = False
    if args.source_dir is None:
        print("You must specify a source diractory or list it in your ~/.remarkable_params.sh file")
        invalid_args = True
    if args.dest_dir is None:
        print("You must specify a destination directory file or list it in your " +\
                "~/.remarkable_params.sh file")
        invalid_args = True
    if args.time_file is None:
        if os.path.isfile("time_file.json"):
            args.time_file = "time_file.json"
        else:
            response = input("No time file found, would you like to proceed without one? [y/n]")
            if response.lower() != "y":
                invalid_args = True

    if invalid_args:
        exit(1)
    
    return args

if __name__ == "__main__":
    args = resolve_cmdline_args()

    node_dict = get_node_dict(args.source_dir)
    root = make_graph(node_dict)

    if args.debug:
        print("===== File Tree ====")
        print(f"{root.get_str()}====================")

    if args.debug or args.verbose:
        print("Creating PDFs and Directories...")

    if args.time_file:
        time_ref = read_time_file(args.time_file)
    else:
        time_ref = None

    files_to_create = root.create_structure(args.source_dir, args.dest_dir, args.debug or args.verbose, time_ref)
    num_files = len(files_to_create)

    num_pages, elapsed_time = create_pdfs(files_to_create)

    if args.time_file:
        write_time_file(time_ref, args.time_file)

    if not args.no_sync or args.sync_warn:
        root.process_extra_files(args.dest_dir, args.verbose, args.sync_warn)

    if num_files > 0:
        time_per_page = elapsed_time / num_pages
        print(f"{num_files} pdfs ({num_pages} pages) created in {get_time_str(elapsed_time)} (~{time_per_page:.1f}s per page)")
    else:
        print("No files to create!")

