#!/usr/bin/env python

#Copyright (c) 2010, Timothy G. Flynn
#All rights reserved.

# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation and/or
#      other materials provided with the distribution.

#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
#INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
#WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
#USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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

from optparse import OptionParser

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
            f.write( "%s " % ( pair[0] ) )
        f.write( "\n" )
    f.close()
                        
if __name__ == "__main__":

    parser = OptionParser()

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
    
    (options,args) = parser.parse_args()

    if options.datasetFilename is None:
        print "ERROR: No dataset file supplied"
        sys.exit( -1 )

    if options.outputFilename is None:
        print "ERROR: No output file supplied"
        sys.exit( -1 )
        
    if options.vocabularyFilename is None:
        print "ERROR: No vocabulary file supplied"
        sys.exit( -1 )

    voc = loadVocabulary( options.vocabularyFilename )

    frequencies = generateFrequencies( voc, options.datasetFilename )

    dumpMatrix( frequencies, options.outputFilename )
    

