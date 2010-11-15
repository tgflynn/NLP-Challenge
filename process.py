#!/usr/bin/env python

#Copyright (c) 2010, Timothy G. Flynn
#All rights reserved.
#
# See the file license.txt for license terms.

"""
This program reads a vocabulary file and a dataset file in the format defined by the Metoptimize NLP challenge
(http://metaoptimize.com/blog/2010/11/05/nlp-challenge-find-semantically-related-terms-over-a-large-vocabulary-1m/)
and generates an output file consisting of a set of lines where each line consists of a space separated list of words,
The first word on each line contains a word from the vocabulary list.  The remaining words on the line consist of
those words from the dataset which have been found to co-occur with the vocabulary word.  They are in descreasing
order by co-occurrence frequency.
"""


import sys
import os
import math
import re
import time

from optparse import OptionParser

from NLPC import loadVocabulary,TIC,TOC


def topn( l, n ):
    v = [ [ None, 0.0 ] for x in range( n ) ]
    for i in range( n ):
        for x in l:
            score = x[1]
            if ( score > v[i][1] ) and ( ( i == 0 ) or ( score < v[i-1][1] ) ):
                v[i][0] = x[0]
                v[i][1] = score
    return v
    

def generateFrequencies( voc, filename ):
    frequencies = {}
    for word in voc.keys():
        frequencies[ word ] = {}
    f = file( filename )
    lineCount = 0
    for l in f:
        words = [ x.strip() for x in re.split( r'\s+', l.strip() ) ]
        for i in range( len( words ) ):
            w = words[i]
            if frequencies.has_key( w ):
                for j in range( len( words ) ):
                    if i == j:
                        continue
                    u = words[j]
                    if not frequencies[w].has_key( u ):
                        frequencies[w][u] = 0
                    frequencies[w][u] += 1
    f.close()
    return frequencies

def dumpMatrix( frequencies, filename ):
    f = file( filename, 'w' )
    words = frequencies.keys()
    words.sort()
    for w in words:
        d = frequencies[ w ]
        v = [ ( k,v ) for (k,v) in d.items() ]
        v.sort( key = lambda x: x[1], reverse = True )
        f.write( "%s " % ( w ) )
        for pair in v[ 0: min( len(v), 10 ) ]:
            if pair[0] is not None:
                f.write( "%s " % ( pair[0] ) )
        f.write( "\n" )
    f.close()

def filterFile( inputFilename, outputFilename ):
    fin = file( inputFilename )
    fout = file( outputFilename, 'w' )
    for l in fin:
        words = [ x.strip() for x in re.split( r'\s+', l.strip() ) ]
        #print 'words = ',words
        filtered = [ w for w in words if ( re.match( r'^[a-zA-Z]*$', w ) != None ) ]
        #print 'filtered = ',filtered
        if len( filtered ) > 0:
            for w in filtered:
                fout.write( '%s ' % ( w ) )
            fout.write( '\n' )
    fout.close()
    fin.close()

def makeVocabulary( inputFilename, outputFilename ):
    fin = file( inputFilename )

    wordMap = {}
    for l in fin:
        words = [ x.strip() for x in re.split( r'\s+', l.strip() ) ]
        for w in words:
            if not wordMap.has_key( w ):
                wordMap[ w ] = { 'count' : 0 }
            wordMap[w]['count'] += 1
    fin.close()
    wordList = wordMap.keys()
    wordList.sort()
    fout = file( outputFilename, 'w' )
    for w in wordList:
        fout.write( '%d %s\n' % ( wordMap[w]['count'], w ) )
    fout.close()
                        
if __name__ == "__main__":

    parser = OptionParser()

    parser.add_option( "-f",
                       "--filter-filename",
                       dest = "filterFilename",
                       action = "store",
                       help = "File to filter" )
    
    parser.add_option( "-d",
                       "--dataset-filename",
                       dest = "datasetFilename",
                       action = "store",
                       help = "Dataset file" )

    parser.add_option( "-o",
                       "--output-filename",
                       dest = "outputFilename",
                       action = "store",
                       help = "Output file" )

    parser.add_option( "-v",
                       "--vocabulary-filename",
                       dest = "vocabularyFilename",
                       action = "store",
                       help = "Vocabulary file" )

    parser.add_option( "-m",
                       "--make-vocabulary",
                       dest = "makeVocabulary",
                       action = "store_true",
                       default = False,
                       help = "Make vocabulary file" )
    
    (options,args) = parser.parse_args()

    if options.filterFilename and options.outputFilename:
        print "Filtering %s -> %s" % ( options.filterFilename, options.outputFilename )
        filterFile( options.filterFilename, options.outputFilename )
        sys.exit( 0 )

    if options.makeVocabulary and options.datasetFilename and options.outputFilename:
        print "Creating vocabulary file %s -> %s" % ( options.datasetFilename, options.outputFilename )
        makeVocabulary( options.datasetFilename, options.outputFilename )
        sys.exit( 0 )
    
    if options.datasetFilename is None:
        print "ERROR: No dataset file supplied"
        sys.exit( -1 )

    if options.outputFilename is None:
        print "ERROR: No output file supplied"
        sys.exit( -1 )
        
    if options.vocabularyFilename is None:
        print "ERROR: No vocabulary file supplied"
        sys.exit( -1 )

    t = TIC()
    voc = loadVocabulary( options.vocabularyFilename )
    TOC( t, "loadVocabulary" )

    t = TIC()
    frequencies = generateFrequencies( voc, options.datasetFilename )
    TOC( t, "generateFrequencies" )

    t = TIC()
    dumpMatrix( frequencies, options.outputFilename )
    TOC( t, "dumpMatrix" )

