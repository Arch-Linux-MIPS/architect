#!/usr/bin/env python3

import argparse
import sys
import zmq

from cmd_loader import CmdLoader
from config import Config

if __name__ == "__main__":
	cmds = CmdLoader.load("Client")

	parser = argparse.ArgumentParser(description="Arch Linux MIPS Architect")
	parser.add_argument(
		"--config",
		dest="config",
		default="architect.conf",
		help="use the specified config file"
	)

	subparsers = parser.add_subparsers(
		title="subcommands",
		description="""
			You may interact with a running architect daemon using the
			following subcommands."""
	)

	for cmd in cmds:
		cmd.setup_args(subparsers)

	args = parser.parse_args()

	if not "cmd" in args:
		print("No command specified")
		sys.exit(1)

	if not Config.load(args.config):
		print("Failed to load config")
		sys.exit(1)

	sys.exit(args.cmd().run(args))
