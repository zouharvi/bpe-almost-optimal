from collections import defaultdict
import copy
from formal_bpe.utils import pairs_in_list, flat_seq, debug_flat_seq
from rich.progress import track


def merge_signature(merge):
    if type(merge) is str:
        return merge
    else:
        sig1 = merge_signature(merge[0])
        sig2 = merge_signature(merge[1])
        return sig1+sig2

def compare_merges(a, b):
    # b is smaller, so swap
    if len(a[0]) > len(b[0]):
        return True
    
    # there is conflict, don't swap
    if a[1][1] == b[1][0] or a[1][0] == b[1][1]:
        return False

    # otherwise lexicographically
    return a[0] > b[0]

def insert_into_canonized_sequence(seq, item):
    i = len(seq)
    for i in range(len(seq)-1, -1, -1):
        if not compare_merges(seq[i], item):
            break
    
    seq.insert(i, item)
    return seq

class ExactDynBPE:
    def __init__(self, fix_overlap=False):
        if fix_overlap:
            self.get_word_pair_counts = self.get_word_pair_counts_fix_overlap

        self.explored_seq = set()

    @staticmethod
    def apply_merge_slow(token, pair):
        ys_word = []
        i = 0
        N = len(token)
        while i < N:
            if i < N - 1 and (token[i], token[i + 1]) == pair:
                ys_word.append(pair)
                i += 2
            else:
                ys_word.append(token[i])
                i += 1
        return ys_word

    @staticmethod
    def get_word_pair_counts(tokens_freqs):
        pairs = defaultdict(int)
        for token, token_freq in tokens_freqs.values():
            for (x, y) in pairs_in_list(token):
                pairs[x, y] += token_freq

        return pairs

    @staticmethod
    def get_word_pair_counts_fix_overlap(tokens):
        pairs = defaultdict(int)
        prev_pair = None
        for (x, y) in pairs_in_list(tokens):
            # increment only if the prev suffix does not match our prefix
            # otherwise wrong estimate on `aaa`
            if (x,y) != prev_pair:
                pairs[x, y] += 1
                prev_pair = (x, y)
            else:
                # make sure to clear it so that for `aaaa` we count it twice
                prev_pair = None

        return pairs

    @staticmethod
    def top_pair(pairs):
        return max(pairs, key=pairs.__getitem__)

    def fit_greedy(self, tokens, T, seq=tuple()):
        if T == 0:
            return [debug_flat_seq(x) for x in tokens], 1

        outputs = []

        pairs = self.get_word_pair_counts(tokens)
        for pair, pair_freq in pairs.items():
            pair = (merge_signature(pair), pair)
            new_seq = tuple(insert_into_canonized_sequence(list(seq), pair))
            new_seq_small = tuple([x[1] for x in new_seq])

            # only do those that have not been explored yet
            if new_seq_small in self.explored_seq:
                continue
            
            self.explored_seq.add(new_seq_small)

            tokens_new = self.apply_merge_slow(tokens, pair[1])
            outputs.append(self.fit_greedy(tokens_new, T-1, new_seq))
        else:
            outputs.append((tokens, 1))

        explored_paths = sum(x[1] for x in outputs)

        output = min([x[0] for x in outputs], key=len)
        output = [debug_flat_seq(x) for x in output]
        return output, explored_paths