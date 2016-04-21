# class for representing ta1de1 data
from collections import defaultdict


class TadeVerb():
    def __init__(self, verb, frames, freq):
        self.verb = verb
        self.freq = freq
        self.frames = {}
        for frame_str, fr_freq, ratio in frames:
            frame = tuple(frame_str.split('_'))
            self.frames[frame] = (fr_freq, ratio)

    def index(self):
        self.arg_index = defaultdict(dict)
        for frame, (freq, ratio) in self.frames.iteritems():
            for arg in frame:
                self.arg_index[arg][frame] = (freq, ratio)

    def __repr__(self):
        return 'TadeVerb(verb: {}, freq: {}, #frames: {})'.format(
            self.verb, self.freq, len(self.frames))


def tade_iterator(tsv_file, min_verb_freq=1):
    """Iterates through the file and returns TadeVerbs."""
    already_seen = set()
    curr_verb, curr_freq, curr_frames = None, None, None
    with open(tsv_file) as inf:
        for line in inf:
            verb, frame, fr_freq, v_freq, ratio = line.strip().split('\t')
            if verb != curr_verb:
                if verb in already_seen:
                    raise Exception('tsv not sorted!')

                if curr_verb is not None:
                    already_seen.add(curr_verb)
                    if curr_freq >= min_verb_freq:
                        yield TadeVerb(curr_verb, curr_frames, curr_freq)
                curr_verb = verb
                curr_freq = int(v_freq)
                curr_frames = []

            curr_frames.append((frame, int(fr_freq), float(ratio)))
        else:
            if curr_freq >= min_verb_freq:
                yield TadeVerb(curr_verb, curr_frames, curr_freq)


class Tade():
    def __init__(self, tsv_file, index=True, min_verb_freq=1):
        curr_verb, curr_freq, curr_frames = None, None, None
        print 'reading tade data...',
        self.verb_index = {tv.verb: tv for tv in
                           tade_iterator(tsv_file, min_verb_freq)}
        print 'done'

        if index:
            self.index()

    def index(self):
        print 'indexing args and frames...',
        self.frame_freqs = defaultdict(int)
        self.arg_index = defaultdict(lambda: defaultdict(dict))
        for verb, tade_verb in self.verb_index.iteritems():
            tade_verb.index()
            for arg, frames in tade_verb.arg_index.iteritems():
                for frame, (freq, ratio) in frames.iteritems():
                    self.arg_index[arg][frame][verb] = (freq, ratio)
                    self.frame_freqs[frame] += 1
        print 'done'

def most_freq_frames(tade, arg, n=10):
    return sorted(
        ((frame, tade.frame_freqs[frame])
         for frame in tade.arg_index[arg].iterkeys()),
        key=lambda f: -f[1])[:n]


def test():
    import sys
    tade = Tade(sys.argv[1])
    print most_freq_frames(tade, 'NP<CAS><TER>')
