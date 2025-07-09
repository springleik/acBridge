#!/usr/bin/env python3
# CompTree.py directional JSON tree comparison
# https://github.com/springleik/PompTree/blob/master/CompTree.py
# M. Williamsen  26 November 2023

import json, sys, math

# ---------------- Library Functions ---------------- #
# locate key in data
# return generator for value
# may return multiple values in a list
def locateKey(key, data):
    if isinstance(data, dict):
        if key in data: yield data[key]
        for i, j in data.items():
            for k in locateKey(key, j): yield k
    elif isinstance(data, list):
        for m in data:
            for n in locateKey(key, m): yield n

# --------------------------------------------------- #
# locate key-value pair in data
# return generator for containing object
# may return multiple objects in a list
def locatePair(key, value, data):
    if isinstance(data, dict):
        if (key in data) and (data[key] == value): yield data
        for i, j in data.items():
            for k in locatePair(key, value, j): yield k
    elif isinstance(data, list):
        for m in data:
            for n in locatePair(key, value, m): yield n

# --------------------------------------------------- #
# Compare two JSON tree structures for equality
# returns true if matched, false if not.
# Pass in an error list to obtain detailed report
# Do not pass in a path list, the error list contains path info 
# Note this quirk of Python: that default objects like
# lists get reused as if they were static!
def treeCompare (ref, tst, error = None, path = None) -> bool:
    if error is None: error = []
    if path is None: path = []
    
    # try to match dictionary keys
    if isinstance (ref, dict) and isinstance (tst, dict):
        # The following three lines of code allow for an early exit, if uncommented.
        # The early exit means that no dictionary entries will be compared, if the
        # test dictionary has less entries than the reference dictionary.
        
        # if len(tst) < len(ref):
        #     error.append ({'dictErr':len(tst),'path':path})
        #     return False
        
        noErrs = True
        for key in ref:
            if key not in tst:
                error.append ({'keyErr':key,'path':path})
                noErrs = False
            elif not treeCompare (ref[key], tst[key], error, path + [key]):
                noErrs = False
        return noErrs

    # try to match list elements
    elif isinstance (ref, list) and isinstance (tst, list):
        # The following three lines of code allow for an early exit.
        # The early exit means that no array elements will be compared
        # if the test array has less entries than the reference array.
        
        if len(tst) < len(ref):
            error.append ({'listErr':len(tst),'path':path})
            return False
            
        noErrs = True
        for n, r in enumerate(ref):
            if not treeCompare (r, tst[n], error, path + [n]):
                noErrs = False
        return noErrs

    # try to match simple types
    elif ref is None and tst is None: return True
    elif isinstance (ref, int)   and isinstance (tst, int):  return leafCompare (ref, tst, error, path)
    elif isinstance (ref, str)   and isinstance (tst, str):  return leafCompare (ref, tst, error, path)
    elif isinstance (ref, bool)  and isinstance (tst, bool): return leafCompare (ref, tst, error, path)
    elif isinstance (ref, float) and isinstance (tst, float):
        if math.isnan(ref)   and math.isnan(tst): return True
        elif math.isinf(ref) and math.isinf(tst): return True
        return leafCompare (ref, tst, error, path)

    # this point reached if types are different or unknown
    else: error.append ({'typeErr':[str(type(ref)), str(type(tst))],'path':path}); return False

# helper function for treeCompare
def leafCompare (ref, tst, error, path) -> bool:
    if ref == tst: return True
    error.append ({'valErr':[ref, tst],'path':path})
    return False

# --------------------------------------------------- #
# locate instances of a subtree by recursive descent
# returns a list of matches
def locateTree(sub, data, match = None) -> bool:
    if match is None: match = []
    # check for match at current level
    if treeCompare (sub, data): match.append(data)

    # check for matches beneath
    if isinstance(data, dict):
        for key, value in data.items():
            locateTree (sub, value, match)
    elif isinstance(data, list):
        for value in data:
            locateTree (sub, value, match)
    return match

# compare two JSON trees, given two file names
def compareTrees (refFileName, tstFileName) -> int:
    # parse json input files
    # print ('Ref: {}, Tst: {}'.format(refFileName, tstFileName), file = sys.stderr)
    try:
        with open(refFileName, 'r') as refFile:
            refData = json.load(refFile)
    except ValueError as e:
        print ('Ref file {} is not valid JSON'.format(refFileName), file = sys.stderr)
        return -3
    try:
        with open(tstFileName, 'r') as tstFile:
            tstData = json.load(tstFile)
    except ValueError as e:
        print ('Tst file {} is not valid JSON'.format(tstFileName), file = sys.stderr)
        return -4
    rept = []
    rslt = treeCompare(refData, tstData, rept)
    print (json.dumps(rept, indent = 2), file = sys.stderr)
    if not rslt: return -1
    else: return 0
    
# ---------------- Main Entry Point ---------------- #
def main() -> int:
    # check command line args, expect two file names
    refFileName = 'Ref.json'
    tstFileName = 'Tst.json'
    args = sys.argv
    if 2 < len(args):
        refFileName = args[1]
        tstFileName = args[2]
    else:
        print ('Usage: python3 TreeCompare.py Ref.json Tst.json', file = sys.stderr)
        return -2
    return compareTrees (refFileName, tstFileName)
    
# ------------------------------------------- #
# this doesn't run, when invoked as a library
if __name__ == '__main__':
    sys.exit(main())
