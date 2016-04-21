#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

"""
Creates the long and short vectors (as described in the paper) from the Tádé
frame list file.
"""
from argparse import ArgumentParser
from itertools import imap
from operator import itemgetter

from tade_corpus_tools.use.tade import Tade
from tade_corpus_tools.gen.vector_io import write_vectors


def parse_arguments():
    parser = ArgumentParser(
        description='Creates the long and short vectors (as described in the '
                    'paper) from the Tádé frame list file.\n\nNeeds numpy for '
                    'the .npz format and scipy for sparse representations. '
                    'Long vectors are only generated if the latter is available.')
    parser.add_argument('tade_file',
                        help='The Tádé file.')
    parser.add_argument('vector_file',
                        help='The output vector file name. Must have the '
                             '.txt or .npz extension, though only .npz is '
                             'valid for long vectors due to sparsity.')
    parser.add_argument('--long', '-l', action='store_true',
                        help='Create long vectors. By default, short vectors '
                             'are generated.')
    parser.add_argument('--cutoff', '-c', type=int, default=1,
                        help='Frequency cutoff for verbs.')
    args = parser.parse_args()
    if args.vector_file[-4:] not in ['.npz', '.txt']:
        parser.error('The vector file must have .npz or .txt as extension.')
    if args.vector_file.endswith('.txt') and args.long:
        parser.error('Only the .npz format is supported for long vectors.')
    if args.vector_file.endswith('.npz'):
        try:
            import numpy as np  # NOQA
        except:
            parser.error('The .npz format requires that numpy is installed.')
    if args.long:
        try:
            from scipy.sparse import dok_matrix  # NOQA
        except:
            parser.error('The long vectors require that scipy is installed.')

    return args.tade_file, args.vector_file, args.long, args.cutoff


def create_short_vectors(tade_file, vector_file, cutoff):
    tade = Tade(tade_file)
    verbs, args = [], set()
    # First count the number of argument types
    for verb, vo in tade.verb_index.iteritems():
        if vo.freq >= cutoff:
            verbs.append(verb)
            for arg in vo.arg_index.iterkeys():
                args.add(arg)
    verbs = sorted(verbs)
    args = {a: i for i, a in enumerate(sorted(args))}

    # Now fill the vectors...
    try:
        import numpy as np
        vectors = np.zeros((len(verbs), len(args)), dtype=int)
    except:
        vectors = [[0] * len(args) for _ in verbs]

    for vi, verb in enumerate(verbs):
        vo = tade.verb_index[verb]
        for arg, freqs in vo.arg_index.iteritems():
            vectors[vi][args[arg]] = sum(imap(itemgetter(0),
                                              freqs.itervalues()))

    # Change to sparse representation, if possible
    if vector_file.endswith('.npz'):
        try:
            if np.count_nonzero(vectors) / float(vectors.size) <= 0.5:
                from scipy.sparse import csr_matrix
                vectors = csr_matrix(vectors)
        except:
            pass

    # And now: print everything
    _write_results(verbs, args.keys(), vectors, vector_file, 'args')


def create_long_vectors(tade_file, vector_file, cutoff):
    tade = Tade(tade_file)
    verbs, frames = [], set()
    # First count the number of frame types
    for verb, vo in tade.verb_index.iteritems():
        if vo.freq >= cutoff:
            verbs.append(verb)
            for frame in vo.frames.iterkeys():
                frames.add(frame)
    verbs = sorted(verbs)
    frames = {f: i for i, f in enumerate(sorted(frames))}

    # Now fill the vectors...
    from scipy.sparse import dok_matrix
    vectors = dok_matrix((len(verbs), len(frames)), dtype=int)

    for vi, verb in enumerate(verbs):
        vo = tade.verb_index[verb]
        for frame, freq in vo.frames.iteritems():
            vectors[vi, frames[frame]] = freq[0]

    # And now: print everything
    _write_results(verbs, ['_'.join(f) for f in frames.keys()], vectors,
                   vector_file, 'frames')


def _write_results(verbs, columns, vectors, vector_file, columns_type):
    write_vectors(verbs, vectors, vector_file)
    with open(vector_file[:-3] + columns_type, 'w') as outf:
        outf.write("\n".join(sorted(columns)))


if __name__ == '__main__':
    tade_file, vector_file, longv, cutoff = parse_arguments()
    if longv:
        create_long_vectors(tade_file, vector_file, cutoff)
    else:
        create_short_vectors(tade_file, vector_file, cutoff)
