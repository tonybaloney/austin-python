# This file is part of "austin-python" which is released under GPL.
#
# See file LICENCE or go to http://www.gnu.org/licenses/ for full license
# details.
#
# austin-python is a Python wrapper around Austin, the CPython frame stack
# sampler.
#
# Copyright (c) 2018-2020 Gabriele N. Tornetta <phoenix1987@gmail.com>.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from pstats import Stats, add_func_stats

from austin.stats import Sample, InvalidSample

ProfileName = str


class Pstats:
    def __init__(self):
        self.stats = Stats()

    def print_stats(self):
        self.stats.print_stats(1)

    def dump(self, f):
        self.stats.dump_stats(f)

    def add_sample(self, sample: Sample):
        # Stats.stats is a dictionary of Key<Tuple>
        # (fcode.co_filename, fcode.co_firstlineno, fcode.co_name)
        # Add frame to stats (cc, ns, tt, ct, callers)
        #     [0] = The number of times this function was called, not counting direct
        #           or indirect recursion,
        #     [1] = Number of times this function appears on the stack, minus one
        #     [2] = Total time spent internal to this function
        #     [3] = Cumulative time that this function was present on the stack.  In
        #           non-recursive functions, this is the total execution time from start
        #           to finish of each invocation of a function, including time spent in
        #           all subfunctions.
        #     [4] = A dictionary indicating for each function name, the number of times
        #           it was called by us.
        for frame in sample.frames:
            fn = frame.filename, frame.line, frame.function
            stat = (0, 0, 0, 0, {})
            if fn not in self.stats.stats:
                self.stats.stats[fn] = add_func_stats((0, 0, 0, 0, {}), stat)
            else:
                self.stats.stats[fn] = add_func_stats(self.stats.stats[fn], stat)

    def asdict(self):
        return self.stats.stats


def main() -> None:
    """austin2pstat entry point."""
    from argparse import ArgumentParser

    arg_parser = ArgumentParser(
        prog="austin2pstat",
        description=(
            "Convert Austin generated profiles to the cProfile pstat format. "
            "The output will contain a profile "
            "for each thread and metric included in the input file."
        ),
    )

    arg_parser.add_argument(
        "input",
        type=str,
        help="The input file containing Austin samples in normal format.",
    )
    arg_parser.add_argument(
        "output", type=str, help="The name of the output pstat file."
    )

    arg_parser.add_argument("-V", "--version", action="version", version="0.1.0")

    args = arg_parser.parse_args()

    stats = Pstats()
    try:
        with open(args.input, "r") as fin:
            for line in fin:
                try:
                    stats.add_sample(Sample.parse(line))
                except InvalidSample:
                    continue

    except FileNotFoundError:
        print(f"No such input file: {args.input}")
        exit(1)

    stats.dump(args.output)


if __name__ == "__main__":
    main()