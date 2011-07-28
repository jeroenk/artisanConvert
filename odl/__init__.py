from os.path import abspath, join, split
from sys     import path

# Setup package directories
(head, _) = split(abspath(__file__)) # removes __init__.py part
(head, _) = split(head)              # removes odl part
path.append(join(head, "ply"))       # add ply module
path.append(join(head, "pyth"))      # add pyth module
