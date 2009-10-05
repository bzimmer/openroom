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

import re
import datetime
from decimal import Decimal
from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext import declarative
from sqlalchemy.orm import relation, backref, join, reconstructor
from sqlalchemy.types import Text, Integer, Boolean, Numeric, TypeEngine

__all__ = (
    "Camera", "City", "Country", "Exif", "Image",
    "Iptc", "Lens", "LibraryFile", "LibraryFolder",
    "LibraryRootFolder","Location", "Develop"
)

ZERO = Decimal()

_lenses = (
    # telephoto
    # "17.0-55.0 mm f/2.8",
    # "18-55mm f/3.5-5.6",
    # "18.0-55.0 mm f/3.5-5.6",
    # "28.0-200.0 mm f/3.8-5.6",
    # "5.4-10.8 mm",
    # "5.4-16.2 mm",
    # "5.8-17.4 mm",
    # "55.0-200.0 mm f/4.0-5.6",
    # "7.4-22.2 mm",
    # "7.7-23.1 mm",
    # "70.0-200.0 mm",
    re.compile(r"(?P<minf>[0-9]+\.?[0-9]*)-(?P<maxf>[0-9]*\.?[0-9]*)(?:[ m]+f/(?P<maxa>[0-9]+\.?[0-9]*)-?(?P<mina>[0-9]+\.[0-9]*)?)?"),
    # prime
    # "105.0 mm f/2.8",
    re.compile(r"(?P<minf>[0-9]+\.?[0-9]*)[ m]*f/(?P<maxa>[0-9]+\.?[0-9]*)-?(?P<foo>[0-9]+\.[0-9]*)?"),
)

Base = declarative.declarative_base()

class LrNumeric(TypeEngine):
    """Custom numeric class for Lr.

    Lr occasionally persists Develop.croppedWidth == "uncropped" to represent
    None, this type manages the translation both directions to queries can be
    written::
        q = self.query(Image).join(Develop)
        q = q.filter(Develop.croppedHeight != None)
    """

    def get_dbapi_type(self, dbapi):
        return dbapi.NUMBER

    def bind_processor(self, dialect):
        def process(value):
            return "uncropped" if value is None else value
        return process

    def result_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            return None if value == "uncropped" else Decimal(str(value))
        return process

class Lens(Base):
    __tablename__ = "AgInternedExifLens"
    id = Column("id_local", Integer, primary_key=True)
    name = Column("value", Text)

    def __repr__(self):
        return self.name

    @reconstructor
    def onload(self):
        if not self.name:
            return
        for c in _lenses:
            g = c.match(self.name)
            if g:
                details = g.groupdict()
                break
        else:
            details = dict()

        def _decimal(name):
            x = details.get(name, None)
            if x is None:
                return ZERO
            return Decimal(x)

        self.minimumFocalLength = _decimal("minf")
        self.maximumFocalLength = _decimal("maxf")
        self.maximumAperture = _decimal("maxa")
        self.minimumAperture = _decimal("mina")

    @property
    def focalRange(self):
        return (self.minimumFocalLength, self.maximumFocalLength)

    @property
    def apertureRange(self):
        return (self.maximumAperture, self.minimumAperture)

    @property
    def isPrime(self):
        return self.minimumFocalLength == self.maximumFocalLength

class Camera(Base):
    __tablename__ = "AgInternedExifCameraModel"
    id = Column("id_local", Integer, primary_key=True)
    name = Column("value", Text)

    def __repr__(self):
        return self.name

class Country(Base):
    __tablename__ = "AgInternedIptcCountry"
    id = Column("id_local", Integer, primary_key=True)
    name = Column("value", Text)

    def __repr__(self):
        return self.name

class City(Base):
    __tablename__ = "AgInternedIptcCity"
    id = Column("id_local", Integer, primary_key=True)
    name = Column("value", Text)

    def __repr__(self):
        return self.name

class Location(Base):
    __tablename__ = "AgInternedIptcLocation"
    id = Column("id_local", Integer, primary_key=True)
    name = Column("value", Text)

    def __repr__(self):
        return self.name

class LibraryRootFolder(Base):
    __tablename__ = "AgLibraryRootFolder"
    id = Column("id_local", Integer, primary_key=True)
    absolutePath = Column("absolutePath", Text)

class LibraryFolder(Base):
    __tablename__ = "AgLibraryFolder"
    id = Column("id_local", Integer, primary_key=True)
    root = Column("rootFolder", Integer)
    path = Column("pathFromRoot", Text)

class LibraryFile(Base):
    __tablename__ = "AgLibraryFile"
    id = Column("id_local", Integer, primary_key=True)
    baseName = Column("baseName", Text)
    folderId = Column("folder", Integer, ForeignKey("AgLibraryFolder.id_local"))
    folder = relation(LibraryFolder)

class Image(Base):
    __tablename__ = "Adobe_images"
    id = Column("id_local", Integer, primary_key=True)
    fileId = Column("rootFile", Integer, ForeignKey("AgLibraryFile.id_local"))
    file = relation(LibraryFile, backref=backref("file", uselist=False))
    pick = Column(Boolean)
    rating = Column(Integer)
    colors = Column("colorLabels", Text)
    captureTime = Column(Text)

class Exif(Base):
    __tablename__ = "AgHarvestedExifMetadata"
    id = Column("id_local", Integer, primary_key=True)
    imageId = Column("image", Integer, ForeignKey("Adobe_images.id_local"))
    image = relation(Image, backref=backref('exif', uselist=False))
    aperture = Column(Integer)
    cameraId  = Column("cameraModelRef", Integer, ForeignKey("AgInternedExifCameraModel.id_local"))
    camera = relation(Camera)
    cameraSNId  = Column("cameraSNRef", Integer)
    dateDay = Column(Integer)
    dateMonth = Column(Integer)
    dateYear = Column(Integer)
    flashFired = Column(Boolean)
    focalLength = Column(Numeric)
    hasGPS = Column(Boolean)
    isoSpeedRating = Column(Integer)
    lensId = Column("lensRef", Integer, ForeignKey("AgInternedExifLens.id_local"))
    lens = relation(Lens)
    shutterSpeed = Column(Numeric)

    @property
    def date(self):
        return datetime.date(self.dateYear, self.dateMonth, self.dateDay)

class Iptc(Base):
    __tablename__ = "AgHarvestedIptcMetadata"
    id = Column("id_local", Integer, primary_key=True)
    imageId = Column("image", Integer, ForeignKey("Adobe_images.id_local"))
    image = relation(Image, backref=backref("iptc", uselist=False))
    locationId = Column("locationRef", ForeignKey("AgInternedIptcLocation.id_local"))
    location = relation(Location)
    cityId = Column("cityRef", ForeignKey("AgInternedIptcCity.id_local"))
    city = relation(City)
    countryId = Column("countryRef", ForeignKey("AgInternedIptcCountry.id_local"))
    country = relation(Country)

class Develop(Base):
    __tablename__ = "Adobe_imageDevelopSettings"
    id = Column("id_local", Integer, primary_key=True)
    imageId = Column("image", Integer, ForeignKey("Adobe_images.id_local"))
    image = relation(Image, backref=backref("develop", uselist=False))
    croppedHeight = Column(LrNumeric)
    croppedWidth = Column(LrNumeric)
    fileHeight = Column(Numeric)
    fileWidth = Column(Numeric)
    grayscale = Column(Boolean)
    hasDevelopAdjustments = Column(Boolean)
    whiteBalance = Column(Text)
