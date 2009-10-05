# Copyright (c) 2009 Brian Zimmer <bzimmer@ziclix.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from decimal import Decimal
from sqlalchemy.sql import func
from sqlalchemy.orm import eagerload
from collections import defaultdict

from openroom import Exif, Iptc, Image, Develop

def stats(seq):

    buckets = defaultdict(list)
    for a, b in seq:
        buckets[a].append(b)

    yield buckets

    for key, values in buckets.items():
        # compute mode
        m = defaultdict(int)
        for a in values:
            m[a] += 1
        mode = sorted((v, k) for k, v, in m.items())[-1][-1]
        mean = sum(values) / len(values)
        yield key, mean, mode, len(values)

class Reports(object):

    def __init__(self, session):
        self.session = session

    def query(self, *entity):
        return self.session.query(*entity)

    def imageCounts(self):
        q = self.query(Image, func.count()).options(eagerload("exif")).join(Exif)
        q = q.filter(Exif.dateYear >= 2007)
        q = q.group_by(Exif.dateYear).group_by(Exif.dateMonth)
        for a, cnt in q:
            yield a.exif.dateYear, a.exif.dateMonth, cnt

    def locations(self):
        q = self.query(Image).join(Iptc).filter(Image.pick == True)
        q = q.filter(Iptc.location != None).filter(Iptc.city != None).filter(Iptc.country != None)
        for a in q:
            yield a.iptc.location.name, a.iptc.city.name, a.iptc.country.name

    def focalLengths(self, pick=None):
        q = self.query(Image).options(eagerload("exif")).join(Exif)
        if pick is not None:
            q = q.filter(Image.pick == pick)
        q = q.filter(Exif.lens != None).filter(Exif.focalLength != None).filter(Exif.lens != None)

        return stats((g.exif.lens, g.exif.focalLength.to_integral()) for g in q.all())

    def crops(self, pick=None):
        q = self.query(Image).options(eagerload("develop"), eagerload("exif")).join(Develop).join(Exif)
        if pick is not None:
            q = q.filter(Image.pick == pick)
        q = q.filter(Develop.croppedHeight != None).filter(Develop.croppedWidth != None).filter(Exif.lens != None)

        c = list()
        for g in q.all():
            if g.develop.fileHeight is None:
                continue
            p = (g.develop.croppedHeight + g.develop.croppedWidth) / (g.develop.fileHeight + g.develop.fileWidth)
            c.append((g.exif.lens, Decimal("%0.2f" % (p))))
        return stats(c)

