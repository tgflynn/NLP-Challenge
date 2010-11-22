
import sys
import os
import math
import re
import time

def TIC():
    return time.time()

def TOC( t1, name = "Unnamed" ):
    t2 = time.time()
    deltat = t2 - t1
    print "Time Interval : %50s : Elapsed seconds : %f" % ( name, deltat )

def countLines( filename ):
    f = file( filename )
    lineCount = 0
    for l in f:
        lineCount += 1
    return lineCount

def makePath( path ):
    (head,tail) = os.path.split( path )
    if not head:
        if not os.path.exists( path ):
            os.mkdir( path )
            return
    if not os.path.exists( head ):
        makePath( head )
    if not os.path.exists( path ):
        os.mkdir( path )

def loadVocabulary( filename ):
    voc = {}
    f = file( filename )
    lineCount = 0
    invalidLines = []
    for l in f:
        try:
            fields = re.split( r'\s+', l.strip() )
            if len( fields ) != 2:
                invalidLines.append( lineCount )
                lineCount += 1
                continue
            count = int( fields[0].strip() )
            word = fields[1].strip()
            voc[ word ] = count
            lineCount += 1
        except:
            print "Exception ocurred at line: %d" % ( lineCount )
            print "Line : %s" % ( l )
            invalidLines.append( lineCount )
    f.close()
    return voc

def loadWordList( filename ):
    words = set()
    f = file( filename )
    for l in f:
        words.add( l.strip() )
    f.close()
    return words
