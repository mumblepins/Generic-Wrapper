# Generic-Wrapper
Generic helper to modify command line arguments of a calling program.

[Get a Pyinstaller all-in-one version in the Releases.](https://github.com/mumblepins/Generic-Wrapper/releases/latest)

Uses either extra command line options or environment variables to modify the command input

Built for windows, but there's no reason it shouldn't work on any other platform as well, I tried to keep things relatively agnostic.

By default writes a log file to `%TEMP%/prog_name.log` where prog_name is the `sys.argv[0]`, or the name of the wrapper.

## Usage

Change options can be specified by either environment variables, or extra command line args.

Multiple command line arguments of each option are allowed; to do multiple versions of environment variables, seperate with a `|`(pipe) symbol.  Command line options should be prefixed with two dashes `--`.

#### Options

* `GWX_DEL`&ndash; Deletes just an option (`side` would delete `--side`)
* `GWX_DEL_ALL`&ndash; Deletes an option with argument (`side` would completely delete `--side up`)
* `GWX_R_ARG`&ndash; Replace the argument of an option (`side=down` would replace `--side up` with `--side down`)
* `GWX_R_OPT`&ndash; Replaces an option (`q=v` would replace `-q` with `-v`, or `--q` with `--v`)
* `GWX_ADD`&ndash; Arguments to add; Should include any dashes
* `GWX_PROG`&ndash; Full path to program being wrapped

A [batch file](bootstrap.bat) is in the repository that is used as a wrapper around the UPX program for the pyinstaller executable builder.  The program first creates an uncompressed version of the wrapper, which is then used to wrap the UPX call and apply maximum compression.
