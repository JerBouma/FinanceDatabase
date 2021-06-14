# -*- coding: utf-8 -*-

import sys

is_py3 = (sys.version_info[0] > 2)

if is_py3:
    text = str
    from urllib import robotparser
    import csv
    from urllib.parse import quote
else:
    text = unicode
    import robotparser
    from backports import csv
    from urllib import quote
