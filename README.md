# llvm_config.py
The llvm_config.py python script is a helper script to setup LLVM to build LLVM and its components (e.g. clang, lldb, etc.) locally. It supports the setup of already released versions as well as trunk using either SVN or GIT. 

# Usage
The script is a command-line only tool with the following usage string:
```llvm_config.py [OPTIONS] TARGET_DIRECTORY [COMPONENTS]```

## Options
The following options are currently supported:
* `--llvm-version (short: -v)`: The LLVM version (or keyword trunk) to setup
* `--llvm-repo (short: -r)`: Which repository to use, either SVN or GIT. This option is only valid for trunk. 

## Arguments
The following arguments are supported:
* `TARGET_DIRECTORY`: The directory to setup LLVM. For details, please refer to directory layout.
* `COMPONENTS`: The following components are currently supported:
  * cfe (aka. clang)
  * compiler-rt
  * libcxx
  * libcxxabi
  * libunwind
  * openmp
  * lldb
  * test-suite

### Directory Layout
Within the `TARGET_DIRECTORY`, the following directory structure is created:
  * `version`: e.g. trunk or 3.7.1
    * `archive`: where the tar archives are installed to (not used for trunk)
    * `build`: where LLVM is built
    * `install`: where LLVM is installed into
    * `src`: where the source code is extracted (or cloned/checked out) into

## Notes
 * The script may be interruped and restarted later. Only incompleted or not yet downloaded components are processed.
 * It is highly recommend to re-start the setup with the same options (e.g. repository type)
 * LLVM setup with GIT as repository type is pretty slow compared to SVN, because the GIT repo is fairly large including all the meta data

## License

This program is free software. Please use and modify it the way you like. Feedback and failure reports are welcome.
