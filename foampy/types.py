# -*- coding: utf-8 -*-
"""
This module contains classes to work with custom OpenFOAM classes, e.g., lists
and dictionaries.
"""

from __future__ import division, print_function
import os
import foampy
from collections import OrderedDict


class FoamDict(OrderedDict):
    """Object that represents an OpenFOAM dictionary."""

    def __init__(self, name="", casedir="./", subdir="system", **kwargs):
        OrderedDict.__init__(self, kwargs)
        self.name = name
        self.subdir = subdir
        self.casedir = casedir
        self.fpath = os.path.join(casedir, subdir, name)
        self.foam_version = foampy.foam_version
        self.header = ""
        if os.path.isfile(self.fpath):
            self.read()
        else:
            self.header = foampy.dictionaries.build_header(name,
                    self.foam_version, fileclass="dictionary",
                    incl_foamfile=False)
        self.foamfile = FoamSubDict(name="FoamFile", version=2.0,
                                    format="ascii")
        self.foamfile["class"] = "dictionary"
        self.foamfile["object"] = name

    def read(self):
        """Parse dictionary."""
        # Read header first
        with open(self.fpath) as f:
            in_header = False
            for line in f:
                if line[:2] == "/*":
                    in_header = True
                elif line[:2] == r"\*":
                    self.header += line.strip()
                    in_header = False
                if in_header:
                    self.header += line
        # Parse header for OpenFOAM version
        splitheader = self.header.split()
        if "Version:" in splitheader:
            index = splitheader.index("Version:") + 1
            self.foam_version = splitheader[index]


    def __str__(self):
        """Create text from dictionary in OpenFOAM format."""
        txt = self.header + "\n" + str(self.foamfile) + "\n"
        txt += foampy.dictionaries.upper_rule + "\n\n"
        for key, value in self.items():
            if isinstance(value, FoamSubDict):
                value.name = key
                txt += str(value) + "\n\n"
            elif len(key) < 16:
                txt += "{:16s}{};\n\n".format(key, value)
            else:
                txt += "{} {};\n\n".format(key, value)
        txt += foampy.dictionaries.lower_rule + "\n"
        return txt


class FoamSubDict(OrderedDict):
    """Object to represent a dictionary inside a dictionary."""

    def __init__(self, name="", **kwargs):
        self.name = name
        OrderedDict.__init__(self, kwargs)

    def __str__(self):
        txt = self.name + "\n{\n"
        for key, val in self.items():
            if not isinstance(val, FoamSubDict):
                if len(key) < 12:
                    txt += "    {:12s}{};\n".format(key, val)
                else:
                    txt += "    {} {};\n".format(key, val)
        txt += "}"
        return txt


class BlockMeshDict(FoamDict):
    """Object to represent a `blockMeshDict`."""

    def __init__(self, name="blockMeshDict", casedir="./",
                 subdir="constant/polyMesh"):
        FoamDict.__init__(self)


class FoamList(list):
    """Class that represents an OpenFOAM list."""

    def __init__(self, list_in=None, dtype=float):
        if isinstance(list_in, list):
            py_list = [dtype(i) for i in list_in]
        elif isinstance(list_in, str):
            # Attempt to parse string into list
            list_in = list_in.replace("(", "").replace(")", "").split()
            py_list = [dtype(i) for i in list_in]
        else:
            py_list=[]
        list.__init__(self, py_list)

    def __str__(self):
        txt = "("
        for i in self:
            txt += str(i) + " "
        txt = txt[:-1]
        txt += ")"
        return txt


def test_foamdict():
    """Test `FoamDict` class."""
    print("\nTesting FoamDict")
    d = FoamDict(name="controlDict", casedir="test")
    d["someInt"] = 555
    d["someFloat"] = 5.5
    d["subDict"] = FoamSubDict(otherInt=5, otherFloat=5.555)
    print(d)


def test_foamsubdict():
    """Test `FoamSubDict` class."""
    print("\nTesting FoamSubDict")
    d = FoamSubDict(name="FoamFile", version="2.0", format="ascii")
    d["class"] = "dictionary"
    d["object"] = "blockMeshDict"
    print(d)


def test_foamlist():
    """Test `FoamList` class."""
    print("\nTesting FoamList")
    flist = FoamList([1, 2, 3, 4])
    print(flist)

    for i in flist:
        print(i)

    flist2 = FoamList([flist, flist], dtype=FoamList)
    print(flist2)

    flist = FoamList("(0 0 0 0)", dtype=int)
    assert flist[:] == [0]*4
