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
import threading
import copy

from optparse import OptionParser

from NLPC import loadVocabulary,TIC,TOC

import NLPC

from NLPC.Corpus import Corpus


def topn( l, n ):
    v = [ [ None, 0.0 ] for x in range( n ) ]
    for i in range( n ):
        for x in l:
            score = x[1]
            if ( score > v[i][1] ) and ( ( i == 0 ) or ( score < v[i-1][1] ) ):
                v[i][0] = x[0]
                v[i][1] = score
    return v
    

def neighborhood( word, matrix, radius, neighbors ):
    """Finds all words within distance radius of word in the graph
    defined by the matrix.  Connectedness is determined by having a non-zero entry
    in the matrix"""
    if ( radius < 1 ) or ( not matrix.has_key( word ) ):
        return None
    row = matrix[ word ]
    for w in row.keys():
        neighbors.add( w )
        if radius > 1:
            n = neighborhood( w, matrix, radius - 1, neighbors )
            if n:
                neighbors = neighbors.union( n )
    return neighbors
    
def sparseDot( v1, v2 ):
    """Calculate the dot product between 2 sparse vectors represented by Python
    dictionaries"""
    val = 0.0
    for k in v1.keys():
        if v2.has_key( k ):
            val += v1[k] * v2[k]
    return val

def sparseDistance( v1, v2 ):
    """Calculate the Euclidean distance between 2 sparse vectors represented by Python
    dictionaries"""
    val = 0.0
    for k in v1.keys():
        if v2.has_key( k ):
            val += ( v2[k] - v1[k] )**2
        else:
            val += ( v1[k] )**2
    for k in v2.keys():
        if not v1.has_key( k ):
            val += ( v2[k] )**2
    return math.sqrt( val )

def processDataset( voc, frequencies, path ):
    if frequencies is None:
        frequencies = {}
        for word in voc.keys():
            frequencies[ word ] = {}
    if os.path.isdir( path ):
        for f in os.listdir( path ):
            processDataset( voc, frequencies, os.path.join( path, f ) )
    elif os.path.isfile( path ):
        generateFrequencies( voc, frequencies, path )
    return frequencies
    
def generateFrequencies( voc, frequencies, filename ):
    """Create and return a sparse matrix of word co-occurrence frequencies for all
    words in voc within the dataset file filename."""
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
                    if w == u:
                        continue
                    if not frequencies[w].has_key( u ):
                        frequencies[w][u] = 0
                    frequencies[w][u] += 1
    f.close()

def generateSimilarityFile( words, frequencies, filename ):
    """Creates similarity file based on second order co-occurrence frequency"""
    f = file( filename, 'w' )
    count = 0
    for word1 in words:
        neighbors = neighborhood( word1, frequencies, 2, set() )
        if ( not neighbors ):
            continue
        row1 = frequencies[word1]
        similar = []
        for word2 in neighbors:
            if ( word1 == word2 ) or ( not frequencies.has_key( word2 ) ):
                continue
            row2 = frequencies[word2]
            simScore = sparseDistance( row1, row2 )
            similar.append( ( word2, simScore ) )
        if len( similar ) < 1:
            continue
        #similar.sort( key = lambda x: x[1], reverse = True )
        similar.sort( key = lambda x: x[1], reverse = False )
        f.write( "%s " % ( word1 ) )
        for pair in similar[ 0: min( len(similar), 10 ) ]:
            if pair[0] is not None:
                f.write( "%s " % ( pair[0] ) )
        f.write( "\n" )
        count += 1
        if count % 50 == 0:
            #print "Processed %7d lines" % ( count )
            f.flush()
    f.close()

def generateSimilarityFile2( frequencies, filename ):
    """Creates similarity file based on second order co-occurrence frequency"""
    f = file( filename, 'w' )
    words = frequencies.keys()
    words.sort()
    count = 0
    for word1 in words:
        row1 = frequencies[word1]
        similar = []
        for word2 in words:
            if ( word1 == word2 ) or ( not frequencies.has_key( word2 ) ):
                continue
            row2 = frequencies[word2]
            simScore = sparseDot( row1, row2 )
            similar.append( ( word2, simScore ) )
        if len( similar ) < 1:
            continue
        similar.sort( key = lambda x: x[1], reverse = True )
        f.write( "%s " % ( word1 ) )
        for pair in similar[ 0: min( len(similar), 10 ) ]:
            if pair[0] is not None:
                f.write( "%s " % ( pair[0] ) )
        f.write( "\n" )
        count += 1
        if count % 50 == 0:
            print "Processed %7d lines" % ( count )
            f.flush()
    f.close()

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

def filterMatrix( frequencies, maxRank ):
    words = frequencies.keys()
    for w in words:
        d = frequencies[ w ]
        v = [ ( k,v ) for (k,v) in d.items() ]
        v.sort( key = lambda x: x[1], reverse = True )
        for pair in v[ maxRank: ]:
            del d[ pair[0] ]

def normalizeFrequencies( frequencies ):
    words = frequencies.keys()
    counts = {}
    for w in words:
        d = frequencies[ w ]
        cnt = 0
        for (w2,v) in d.items():
            cnt += v
        counts[ w ] = cnt
    for w in words:
        d = frequencies[ w ]
        for w2 in d.keys():
            if ( counts.has_key( w ) and counts.has_key( w2 ) ):
                denom = min( 1, ( counts[w] + counts[w2] ) )
                d[w2] /= denom
    
def filterFile( inputFilename, outputFilename ):
    fin = file( inputFilename )
    fout = file( outputFilename, 'w' )
    for l in fin:
        words = [ x.strip() for x in re.split( r'\s+', l.strip() ) ]
        #print 'words = ',words
        filtered = [ w.lower() for w in words if ( re.match( r'^[a-zA-Z]*$', w ) != None ) ]
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

class Task( threading.Thread ):

    def __init__( self, words, frequencies, outputPrefix, threadNumber ):
        threading.Thread.__init__( self )
        self.words = words
        self.frequencies = frequencies
        self.threadNumber = threadNumber
        self.filename = "%s-%03d.txt" % ( outputPrefix, threadNumber )
        self.finishedEvent = threading.Event()
        self.finishedEvent.clear()

    def run( self ):
        s = set()
        generateSimilarityFile( self.words, self.frequencies, self.filename )
        self.finishedEvent.set()
    
if __name__ == "__main__":

    parser = OptionParser()

    parser.add_option( "-a",
                       "--algorithm",
                       dest = "algorithm",
                       action = "store",
                       default = "SCOFREQ",
                       help = "Algorithm : ( COFREQ, SCOFREQ )" )
    
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

    parser.add_option( "-n",
                       "--normalize-counts",
                       dest = "normalizeCounts",
                       action = "store_true",
                       default = False,
                       help = "Normalize frequency counts to P(A,B)/(P(A)+P(B))" )
    
    parser.add_option( "-c",
                       "--corpus-directory",
                       dest = "corpusDirectory",
                       action = "store",
                       help = "Top-level directory of corpus to create from data file" )

    parser.add_option( "-t",
                       "--number-threads",
                       dest = "numberThreads",
                       action = "store",
                       help = "Number of threads to run" )

    numberThreads = 2
    
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

    if options.corpusDirectory:
        print "Creating corpus directory %s -> %s" % ( options.datasetFilename, options.corpusDirectory )
        corpus = Corpus( options.datasetFilename, options.corpusDirectory )
        corpus.makeTree()
        sys.exit( 0 )
        
    if options.outputFilename is None:
        print "ERROR: No output file supplied"
        sys.exit( -1 )
        
    if options.vocabularyFilename is None:
        print "ERROR: No vocabulary file supplied"
        sys.exit( -1 )

    if options.numberThreads is not None:
        numberThreads = int( options.numberThreads )

    t = TIC()
    voc = loadVocabulary( options.vocabularyFilename )
    TOC( t, "loadVocabulary" )

    t = TIC()
    frequencies = processDataset( voc, None, options.datasetFilename )
    TOC( t, "generateFrequencies" )

    if options.normalizeCounts:
        t = TIC()
        normalizeFrequencies( frequencies )
        TOC( t, "normalizeFrequencies" )
    
    if options.algorithm == "COFREQ":
        t = TIC()
        dumpMatrix( frequencies, options.outputFilename )
        TOC( t, "dumpMatrix" )
    elif options.algorithm == "SCOFREQ":
        t = TIC()
        filterMatrix( frequencies, 100 )
        TOC( t, "filterMatrix" )
        words = frequencies.keys()
        words.sort()
        threads = []
        numberWords = len( words )
        wordsPerThread = ( numberWords / numberThreads ) + ( 1 if ( numberWords % numberThreads ) != 0 else 0 )
        (outputPrefix,extension) = os.path.splitext( options.outputFilename )
        for i in range( numberThreads ):
            startWord = i * wordsPerThread
            t = Task( words[ startWord:min( len( words ), ( startWord + wordsPerThread ) ) ], frequencies, outputPrefix, i )
            print "Starting thread : ",i
            t.start()
            threads.append( t )

        for t in threads:
            t.finishedEvent.wait()
            
        

