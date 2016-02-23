## open-humans-downloader

### Installation

```sh
$ pip install --upgrade open-humans-downloader
```

### Usage

```
Usage: oh-download [OPTIONS]

  Download data from Open Humans.

Options:
  -s, --source TEXT     the source to download files from
  -u, --username TEXT   the user to download files from
  -d, --directory TEXT  the directory for downloaded files
  -m, --max-size TEXT   the maximum file size to download
  --help                Show this message and exit.
```

### Examples

```
# download all 23andMe files to 23andme/
$ mkdir 23andme
$ oh-download --source twenty_three_and_me --directory 23andme
# download all of beau's files to the current directory
$ oh-download --username beau
```
