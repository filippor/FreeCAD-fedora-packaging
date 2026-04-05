#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from generate_tests_fmf import list_registered_tests


def run_test(command: list[str], env: dict[str, str], timeout: int) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            capture_output=True,
            env=env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        output = (error.stdout or "") + (error.stderr or "")
        return False, f"TIMEOUT after {timeout}s\n{output}"

    output = completed.stdout
    if completed.stderr:
        output += completed.stderr

    if completed.returncode != 0:
        return False, output

    return True, output


def compute_tests(args: argparse.Namespace) -> list[str]:
    if args.suite == "cmd":
        tests = list_registered_tests(args.cmd_binary)
        return [test_name for test_name in tests if test_name != "TestCoinNodeSnapshots"]

    gui_tests = list_registered_tests(args.gui_binary)
    cmd_tests = set(list_registered_tests(args.cmd_binary))
    extra_gui_tests = [test_name for test_name in gui_tests if test_name not in cmd_tests]

    if "TestCoinNodeSnapshots" not in extra_gui_tests and "TestCoinNodeSnapshots" in gui_tests:
        extra_gui_tests.append("TestCoinNodeSnapshots")

    return extra_gui_tests


def build_command(args: argparse.Namespace, test_name: str) -> tuple[list[str], dict[str, str]]:
    env = os.environ.copy()

    if args.suite == "cmd":
        return [args.cmd_binary, "-t", test_name], env

    runner = ["wlheadless-run"]
    if test_name == "TestCoinNodeSnapshots":
        output_dir = Path(env.get("TMT_TEST_DATA", "/tmp/FreeCADTesting")) / "CoinNodeSnapshots"
        env["FC_VISUAL_OUT_DIR"] = str(output_dir)
        runner.extend(["--width=1024", "--height=768"])

    runner.extend(["--", args.gui_binary, "-t", test_name])
    return runner, env


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run FreeCAD registered test suites discovered at runtime.")
    parser.add_argument("--suite", choices=["cmd", "gui"], required=True)
    parser.add_argument("--cmd-binary", default="/usr/bin/FreeCADCmd")
    parser.add_argument("--gui-binary", default="/usr/bin/FreeCAD")
    parser.add_argument("--timeout", type=int, default=300, help="Per-test timeout in seconds")
    args = parser.parse_args(argv)

    selected_tests = compute_tests(args)
    if not selected_tests:
        print(f"No tests selected for suite '{args.suite}'", file=sys.stderr)
        return 1

    print(f"Running suite '{args.suite}' with {len(selected_tests)} tests")

    failures: list[str] = []

    for index, test_name in enumerate(selected_tests, start=1):
        command, env = build_command(args, test_name)
        print(f"[{index}/{len(selected_tests)}] {test_name}")
        print("COMMAND:", " ".join(command))

        passed, output = run_test(command, env, args.timeout)
        sys.stdout.write(output)
        if output and not output.endswith("\n"):
            sys.stdout.write("\n")

        if not passed:
            failures.append(test_name)
            print(f"FAILED: {test_name}", file=sys.stderr)

    if failures:
        print("Failing tests:", ", ".join(failures), file=sys.stderr)
        return 1

    print(f"Suite '{args.suite}' passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))