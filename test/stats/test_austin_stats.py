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

import io

from austin.stats import (
    AustinStats,
    Frame,
    FrameStats,
    Metrics,
    ProcessStats,
    Sample,
    ThreadStats,
)


DUMP_LOAD_SAMPLES = """P42;T0x7f45645646;foo (foo_module.py:10) 300
P42;T0x7f45645646;foo (foo_module.py:10);bar (bar_sample.py:20) 1000
"""


def test_austin_stats_single_process():
    stats = AustinStats(42)

    stats.update(Sample.parse("P42;T0x7f45645646;foo (foo_module.py:10) 152"))
    assert stats == AustinStats(
        child_pid=42,
        processes={
            42: ProcessStats(
                pid=42,
                threads={
                    "0x7f45645646": ThreadStats(
                        label="0x7f45645646",
                        total=Metrics(152),
                        children={
                            Frame("foo", "foo_module.py", 10): FrameStats(
                                label=Frame("foo", "foo_module.py", 10),
                                own=Metrics(152),
                                total=Metrics(152),
                            )
                        },
                    )
                },
            )
        },
    )

    stats.update(Sample.parse("P42;T0x7f45645646 148"))
    assert stats == AustinStats(
        child_pid=42,
        processes={
            42: ProcessStats(
                pid=42,
                threads={
                    "0x7f45645646": ThreadStats(
                        label="0x7f45645646",
                        total=Metrics(300),
                        own=Metrics(148),
                        children={
                            Frame("foo", "foo_module.py", 10): FrameStats(
                                label=Frame("foo", "foo_module.py", 10),
                                own=Metrics(152),
                                total=Metrics(152),
                            )
                        },
                    )
                },
            )
        },
    )

    stats.update(Sample.parse("P42;T0x7f45645646;foo (foo_module.py:10) 100"))
    assert stats == AustinStats(
        child_pid=42,
        processes={
            42: ProcessStats(
                pid=42,
                threads={
                    "0x7f45645646": ThreadStats(
                        label="0x7f45645646",
                        total=Metrics(400),
                        own=Metrics(148),
                        children={
                            Frame("foo", "foo_module.py", 10): FrameStats(
                                label=Frame("foo", "foo_module.py", 10),
                                own=Metrics(252),
                                total=Metrics(252),
                            )
                        },
                    )
                },
            )
        },
    )

    stats.update(Sample.parse("P42;T0x7f45645646;bar (foo_module.py:35) 400"))
    assert stats == AustinStats(
        child_pid=42,
        processes={
            42: ProcessStats(
                pid=42,
                threads={
                    "0x7f45645646": ThreadStats(
                        label="0x7f45645646",
                        total=Metrics(800),
                        own=Metrics(148),
                        children={
                            Frame("foo", "foo_module.py", 10): FrameStats(
                                label=Frame("foo", "foo_module.py", 10),
                                own=Metrics(252),
                                total=Metrics(252),
                            ),
                            Frame("bar", "foo_module.py", 35): FrameStats(
                                label=Frame("bar", "foo_module.py", 35),
                                own=Metrics(400),
                                total=Metrics(400),
                            ),
                        },
                    )
                },
            )
        },
    )

    stats.update(Sample.parse("P42;T0x7f45645664;foo (foo_module.py:10) 152"))
    assert stats == AustinStats(
        child_pid=42,
        processes={
            42: ProcessStats(
                pid=42,
                threads={
                    "0x7f45645664": ThreadStats(
                        label="0x7f45645664",
                        total=Metrics(152),
                        children={
                            Frame("foo", "foo_module.py", 10): FrameStats(
                                label=Frame("foo", "foo_module.py", 10),
                                own=Metrics(152),
                                total=Metrics(152),
                            )
                        },
                    ),
                    "0x7f45645646": ThreadStats(
                        label="0x7f45645646",
                        total=Metrics(800),
                        own=Metrics(148),
                        children={
                            Frame("foo", "foo_module.py", 10): FrameStats(
                                label=Frame("foo", "foo_module.py", 10),
                                own=Metrics(252),
                                total=Metrics(252),
                            ),
                            Frame("bar", "foo_module.py", 35): FrameStats(
                                label=Frame("bar", "foo_module.py", 35),
                                own=Metrics(400),
                                total=Metrics(400),
                            ),
                        },
                    ),
                },
            )
        },
    )


def test_dump():
    stats = AustinStats(42)

    FOO_SAMPLE = "P42;T0x7f45645646;foo (foo_module.py:10) 150"
    BAR_SAMPLE = "P42;T0x7f45645646;foo (foo_module.py:10);bar (bar_sample.py:20) 1000"

    stats.update(Sample.parse(FOO_SAMPLE))
    stats.update(Sample.parse(FOO_SAMPLE))
    stats.update(Sample.parse(BAR_SAMPLE))

    buffer = io.StringIO()
    stats.dump(buffer)
    assert buffer.getvalue() == DUMP_LOAD_SAMPLES


def test_load():
    buffer = io.StringIO(DUMP_LOAD_SAMPLES)
    stats = AustinStats.load(buffer)
    assert stats == AustinStats(
        child_pid=0,
        processes={
            42: ProcessStats(
                pid=42,
                threads={
                    "0x7f45645646": ThreadStats(
                        label="0x7f45645646",
                        own=Metrics(time=0, memory_alloc=0, memory_dealloc=0),
                        total=Metrics(time=1300, memory_alloc=0, memory_dealloc=0),
                        children={
                            Frame(
                                function="foo", filename="foo_module.py", line=10
                            ): FrameStats(
                                label=Frame(
                                    function="foo", filename="foo_module.py", line=10
                                ),
                                own=Metrics(time=300, memory_alloc=0, memory_dealloc=0),
                                total=Metrics(
                                    time=1300, memory_alloc=0, memory_dealloc=0
                                ),
                                children={
                                    Frame(
                                        function="bar",
                                        filename="bar_sample.py",
                                        line=20,
                                    ): FrameStats(
                                        label=Frame(
                                            function="bar",
                                            filename="bar_sample.py",
                                            line=20,
                                        ),
                                        own=Metrics(
                                            time=1000, memory_alloc=0, memory_dealloc=0
                                        ),
                                        total=Metrics(
                                            time=1000, memory_alloc=0, memory_dealloc=0
                                        ),
                                        children={},
                                        height=1,
                                    )
                                },
                                height=0,
                            )
                        },
                    )
                },
            )
        },
    )
