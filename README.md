# Vespa-client - Vespa CLI as python package

![ci](https://github.com/thomasht86/vespa-client/actions/workflows/cross_platform_tests.yml/badge.svg)

Vespa CLI binaries are distributed as part of the Vespa engine, and installation instructions can be found in the [Vespa documentation](https://docs.vespa.ai/en/vespa-cli.html).

As a Python user, moving between different environments and handling dependencies can be cumbersome. By providing the Vespa CLI as a Python package, I aim to make it easier to use Vespa in Python environments.

Installation is as simple as running `pip install vespa-client`.

Tested on Python 3.8, 3.9 and 3.10.
Support for Windows, Linux and MacOS.

The Github Action perform a daily check for new releases of the Vespa CLI. If a new version is found, the python package is updated and a new release is made.

## Usage

For usage, see the [Vespa documentation](https://docs.vespa.ai/en/vespa-cli.html).
