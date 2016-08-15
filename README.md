# open-humans-api

This is work in progress.

## Command line tools

### ohpub-download

```
Usage: ohpub-download [OPTIONS]

  Download public data from Open Humans.

Options:
  -s, --source TEXT     the source to download files from
  -u, --username TEXT   the user to download files from
  -d, --directory TEXT  the directory for downloaded files
  -m, --max-size TEXT   the maximum file size to download
  --help                Show this message and exit.
```

#### Examples

```
# download all 23andMe files to 23andme/
$ mkdir 23andme
$ oh-download --source twenty_three_and_me --directory 23andme
# download all of beau's files to the current directory
$ oh-download --username beau
```

### ohproj-download-all

```
Usage: ohproj-download-all [OPTIONS]

  Download files for all project members to the target directory.

Options:
  -d, --directory TEXT     Target directory for downloaded files.  [required]
  -T, --master-token TEXT  Project master access token.  [required]
  -m, --max-size TEXT      Maximum file size to download.  [default: 128m]
  -v, --verbose            Report INFO level logging to stdout
  -debug                   Report DEBUG level logging to stdout.
  --help                   Show this message and exit.
ohproj-download-all --help  0.20s user 0.02s system 98% cpu 0.215 total
```

### ohproj-download-member
```
Usage: ohproj-download-member [OPTIONS]

  Download files for a specific member to the target directory.

  This command either accepts an OAuth2 user token (-t), or a master access
  token (-T) and project member ID (-m).

Options:
  -d, --directory TEXT     Target directory for downloaded files.  [required]
  -T, --master-token TEXT  Project master access token.
  -m, --member TEXT        Project member ID.
  -t, --access-token TEXT  OAuth2 user access token.
  -m, --max-size TEXT      Maximum file size to download.  [default: 128m]
  -v, --verbose            Report INFO level logging to stdout
  -debug                   Report DEBUG level logging to stdout.
  --help                   Show this message and exit.
```
