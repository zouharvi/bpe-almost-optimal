#!/usr/bin/env python3

import orderedset
import itertools
import string
import argparse
from arsenal.iterextras import take
from faster_bpe.model_slow_beam import SlowBeamBPE
from faster_bpe.model_exact_brute import ExactBruteBPE
from faster_bpe.model_slow import SlowBPE
from rich.progress import track

args = argparse.ArgumentParser()
args.add_argument("--example-length-start", type=int, default=None)
args.add_argument("--example-length", type=int, default=12)
args.add_argument("--alphabet-size", type=int, default=3)
args.add_argument("--beam-size", type=int, default=5)
args.add_argument("--merge-count", type=int, default=2)
args = args.parse_args()

if args.example_length_start is None:
    args.example_length_start = args.example_length

min_ratio = 1
alphabet = string.ascii_lowercase[:args.alphabet_size]

for length in range(args.example_length_start, args.example_length + 1):
    iterator = map(
        "".join,
        itertools.product(alphabet, repeat=length)
    )
    total = args.alphabet_size**length
    print(f"\n{length}\n")
    for example in map(
        ''.join,
        track(iterator, total=total)
    ):

        # the letters must be sorted otherwise discard
        # this saves args.alphabet_size times the work
        example_letters = list(orderedset.OrderedSet(example))
        if not all(example_letters[i] <= example_letters[i + 1] for i in range(len(example_letters) - 1)):
            continue
        # the first n letters must be present to prevent duplicates like b,c,d,e..
        if not set(example_letters).issubset(alphabet):
            continue

        model = SlowBPE(fix_overlap=True)
        result_greedy, indecision = model.fit_greedy(
            example, T=args.merge_count,
            debug_output=True, indecision_output=True
        )
        result_greedy = result_greedy[0]

        # model = ExactBruteBPE(fix_overlap=True)
        # result_exact = model.fit_greedy(
        #     example, T=args.merge_count,
        # )

        bpe_beam = SlowBeamBPE()
        result_beam = bpe_beam.fit_beam_search(
            example, T=args.merge_count,
            B=args.beam_size
        )

        if min_ratio >= len(result_beam) / len(result_greedy) and min_ratio != 1:
            # if len(result_greedy) > len(result_beam):
            print("Example:    ", example, "indecision", indecision)
            print(f"Greedy:      ({len(result_greedy)})", result_greedy)
            print(f"Beam search: ({len(result_beam)})", result_beam)
            print(min_ratio)
            print("====")
        min_ratio = min(min_ratio, len(result_beam) / len(result_greedy))
        # assert len(result_exact) <= len(result_greedy)

        # if len(result_exact) < len(result_greedy) and not indecision:
        #     print("Example:    ", example, "indecision", indecision)
        #     print(f"Greedy:      ({len(result_greedy)})", result_greedy)
        #     print(f"Beam search: ({len(result_beam)})", result_beam)
        #     print("====")
