"""Common functions."""
from gzip import open as gopen

import numpy as np
from scipy.sparse import csr_matrix, spmatrix


def write_vectors(words, vectors, vectors_file):
    """
    Writes the vectors to vectors_file. The format depends on the file name
    extension (see read_vectors for more information).
    """
    if vectors_file.endswith('.npz'):
        if isinstance(vectors, spmatrix):
            sparse = csr_matrix(vectors)
            np.savez(vectors_file, words=words, vectors_data=sparse.data,
                     vectors_indices=sparse.indices,
                     vectors_indptr=sparse.indptr, vectors_shape=sparse.shape)
        else:
            np.savez(vectors_file, words=words, vectors=vectors)
    else:
        with (gopen if vectors_file.endswith('.gz') else open)(vectors_file, 'w') as outf:
            for i, word in enumerate(words):
                print >>outf, word, ' '.join(map(str, vectors[i]))


def read_vectors(vectors_file, normalize=False):
    """
    Reads the vectors in vectors_file and returns the list of words and X
    (num_vec x vec_dim).

    This function supports several formats:
    - GloVe .txt format (.txt or .gz)
    - dense .npz format (with 'words' and 'vectors' keys)
    - sparse .npz format (with 'words', 'vectors_data', 'vectors_indices',
                          'vectors_indptr' and 'vectors_shape').

    @param normalize if @c True, all vectors are normalized to unit L2 length.
    """
    def read_text_vectors():
        with (gopen if vectors_file.endswith('.gz') else open)(vectors_file) as inf:
            list_data = [line.strip().split() for line in inf]
            words = [l[0] for l in list_data]
            X = np.matrix([map(float, l[1:]) for l in list_data])
            return words, X

    def read_npz_vectors():
        npz = np.load(vectors_file)
        words = npz['words']
        if 'vectors' in npz:
            X = npz['vectors']
        else:
            X = csr_matrix((npz['vectors_data'], npz['vectors_indices'],
                            npz['vectors_indptr']), shape=npz['vectors_shape'])
        return words, X

    if vectors_file.endswith('.npz'):
        words, X = read_npz_vectors()
    else:
        words, X = read_text_vectors()
    if normalize:
        X = normalize_rows(X)
    return words, X


def normalize_rows(X):
    """
    Normalizes the rows of matrix X. If X is sparse, it is converted to a
    csr_matrix.
    """
    if isinstance(X, spmatrix):
        X = csr_matrix(X)
        norms = np.array(np.sqrt(X.multiply(X).sum(axis=1)))[:, 0]
        row_indices, _ = X.nonzero()
        X.data /= norms[row_indices]
        return X
    else:
        return X / np.linalg.norm(X, axis=1)[:, np.newaxis]
