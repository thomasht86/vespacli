# Vespa-client - Vespa CLI - python package

![tests](https://github.com/thomasht86/vespa-client/actions/workflows/cross_platform_tests.yml/badge.svg)

Vespa CLI binaries are distributed as part of the Vespa engine. Docs and installation instructions can be found in the [Vespa documentation](https://docs.vespa.ai/en/vespa-cli.html).

As a Python user, moving between different environments and handling dependencies, and PATHS can be cumbersome.

By providing the Vespa CLI as a Python package, it is even easier to use Vespa in Python environments.

Installation is as simple as running `pip install vespacli`.

The Github Action perform a daily check for new releases of the Vespa CLI. If a new version is found, the python package is updated and a new release is made.

Package should work for Windows, Linux and MacOS.
Python versions >=3.8 <=3.11 are tested, but no reason to believe it should not work for other versions. 

## Usage

For usage of the Vespa CLI, see the [Vespa documentation](https://docs.vespa.ai/en/vespa-cli.html).

## Disclaimer

This is an independent contribution and is not affiliated with, nor has it been authorized, sponsored, or otherwise approved by Vespa.ai or any of its affiliates.