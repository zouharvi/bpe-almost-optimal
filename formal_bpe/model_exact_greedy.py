from collections import defaultdict
import collections
import copy
from formal_bpe.utils import pairs_in_list, flat_seq, debug_flat_seq

class ExactGreedyBPE:
    def __init__(self, fix_overlap=False):
        if fix_overlap:
            self.get_word_pair_counts = self.get_word_pair_counts_fix_overlap

        self.explored_seq = set()

    @staticmethod
    def apply_merge_multiple(token, pair):
        ys_word = []
        i = 0
        N = len(token)
        while i < N:
            # we found a possible merge!
            if i < N - 1 and (token[i], token[i + 1]) == pair:
                # oh no the next one is also a possilbe merge
                if i < N -  2 and (token[i+1], token[i + 2]) == pair:
                    # merge now
                    results_1 = [ys_word + [pair] + x for x in  ExactGreedyBPE.apply_merge_multiple(token[i+2:], pair)]
                    # don't merge now
                    results_2 = [ys_word + [token[i]] + x for x in  ExactGreedyBPE.apply_merge_multiple(token[i+1:], pair)]
                    return results_1 + results_2
                else:
                    ys_word.append(pair)
                    i += 2
            else:
                # do not apply merge
                ys_word.append(token[i])
                i += 1
        return [ys_word]

    @staticmethod
    def get_word_pair_counts(tokens):
        pairs = defaultdict(int)
        tokens_freqs = collections.Counter(zip(tokens[0:], tokens[1:]))
        for token, token_freq in tokens_freqs.items():
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

    def fit_greedy(self, tokens, T):
        if T == 0:
            return [debug_flat_seq(x) for x in tokens], False

        type_1_indecision = False

        while T > 0:
            T = T-1
            pairs = self.get_word_pair_counts(tokens)
            max_pair_f = max(pairs.values())
            pairs = [p for p,f in pairs.items() if f == max_pair_f]
            if len(pairs) == 1:
                # good, continue with greedy
                tokens_merged = self.apply_merge_multiple(tokens, pairs[0])
                if len(tokens_merged) != 1:
                    type_1_indecision = True
                    # oh no we have multiple ways of merging
                    outputs = []
                    for tokens_merged_option in tokens_merged:
                        outputs.append(self.fit_greedy(tokens_merged_option, T))
                    output_sequences = [x[0] for x in outputs]
                    type_1_indecision = type_1_indecision or any([x[1] for x in outputs])
                    tokens = min(output_sequences, key=len)
                    break
                else:
                    tokens = tokens_merged[0]
            else:
                outputs = []
                for pair in pairs:
                    tokens_merged = self.apply_merge_multiple(tokens, pair)
                    for tokens_merged_option in tokens_merged:
                        outputs.append(self.fit_greedy(tokens_merged_option, T))
                output_sequences = [x[0] for x in outputs]
                type_1_indecision = type_1_indecision or any([x[1] for x in outputs])
                tokens = min(output_sequences, key=len)
                break

        tokens = [debug_flat_seq(x) for x in tokens]
        return tokens, type_1_indecision