#!/usr/bin/env python

#Copyright (c) 2010, Timothy G. Flynn
#All rights reserved.
#
# See the file license.txt for license terms.

"""
This program uses Word Net's synset similarity function to score semantic
similarity files.

Input format :

  Similarity records correspond to lines.
  
  All words on a line are space separated.

  The first word is the base word similarity is measured against.

  All subsequent words on the same line are words which have been found
  to be similar to the base word.
  


"""

import sys
import os
import math
import re
import time

from optparse import OptionParser

from nltk.corpus import wordnet

import NLPC

def scoreWord( baseSynsets, targetSynsets ):
    bestScore = 0
    for baseSynset in baseSynsets:
        for targetSynset in targetSynsets:
            simScore = baseSynset.path_similarity( targetSynset )
            if simScore > bestScore:
                bestScore = simScore
    return bestScore

def scoreFile( filename, targetWords, verbose = False ):
    meanScore = 0.0
    baseWordCount = 0
    wordCount = 0
    f = file( filename )
    for l in f:
        wordScored = False
        fields = [ x.strip().lower() for x in re.split( r'\s+', l ) ]
        if ( targetWords is not None ) and ( fields[0] not in targetWords ):
            continue
        baseSynsets = wordnet.synsets( fields[0] )
        if baseSynsets is None:
            continue
        for word in fields[1:]:
            # Ignore identical word if it occurs
            if word == fields[0]:
                continue
            targetSynsets = wordnet.synsets( word )
            if targetSynsets is None:
                continue
            wordScore = scoreWord( baseSynsets, targetSynsets )
            meanScore += wordScore
            wordCount += 1
            wordScored = True
        baseWordCount += ( 1 if wordScored else 0 )
        if verbose:
            if ( baseWordCount > 0 ) and ( baseWordCount % 1000 == 0 ):
                print "Words scored : %d, Current Score : %f" % ( baseWordCount, meanScore / ( wordCount if wordCount > 0 else 1 ) )
    f.close()
    meanScore /= ( wordCount if wordCount > 0 else 1 )
    return { 'baseWordCount'  : baseWordCount,
             'totalWordCount' : wordCount,
             'meanScore'      : meanScore }


if __name__ == "__main__":
    
    parser = OptionParser()

    parser.add_option( "-i",
                       "--input-filename",
                       dest = "inputFilename",
                       action = "store",
                       help = "Input File to score" )

    parser.add_option( "-t",
                       "--target-words-filename",
                       dest = "targetWordsFilename",
                       action = "store",
                       help = "List of words to which the scoring should be restricted (if not provided all words found in WN are scored)" )

    parser.add_option( "-v",
                       "--verbose",
                       dest = "verbose",
                       action = "store_true",
                       default = False,
                       help = "Increase verbosity" )

    
    (options,args) = parser.parse_args()

    if not options.inputFilename:
        print "ERROR: No input file provided"
        sys.exit( -1 )

    targetWords = None
    if options.targetWordsFilename:
        targetWords = NLPC.loadWordList( options.targetWordsFilename )

    score = scoreFile( options.inputFilename, targetWords, options.verbose )

    print "Number base words scored : ",score['baseWordCount']
    print "Mean Score               : ",score['meanScore']
