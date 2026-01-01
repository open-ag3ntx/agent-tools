import os
import sys

from rich import print
from rich.columns import Columns

directory = os.listdir('/Users/krishnakorade/Developer/osp/agent-tools')
columns = Columns(directory, equal=True, expand=True)
print(columns)