from __future__ import print_function

import math
import os


def human_size_format(filesize):
    filesize = abs(filesize)
    if (filesize == 0):
        return "0 Bytes"
    p = int(math.floor(math.log(filesize, 2) / 10))
    return "%0.2f %s" % (
        filesize / math.pow(1024, p), ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'][p])


origsize = os.path.getsize('upx.exe')
newsize = os.path.getsize('dist/wrapper.exe')
print('{} --> {} ({:0.1f}%)'.format(human_size_format(origsize),
                                    human_size_format(newsize),
                                    100.0 * newsize / origsize))
