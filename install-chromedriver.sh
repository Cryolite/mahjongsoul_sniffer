#!/usr/bin/env bash

set -uxo pipefail

chromedriver_url='https://chromedriver.storage.googleapis.com/83.0.4103.39/chromedriver_linux64.zip'

function print_error_message ()
{
  if [[ -t 2 ]] && type -t tput >/dev/null; then
    if (( "$(tput colors)" == 256 )); then
      echo "$(tput setaf 9)$1$(tput sgr0)" >&2
    else
      echo "$(tput setaf 1)$1$(tput sgr0)" >&2
    fi
  else
    echo "$1" >&2
  fi
}

function print_usage ()
{
    cat <<'EOF'
Usage: install-chromedriver.sh [OPTION]...
Install ChromeDriver.
  --prefix=PREFIX Install prefix. Defaults to `/usr/local`.
  -h, --help      Display this help and exit.
EOF
}

if [[ $(uname -o) != GNU/Linux ]]; then
  print_error_message "Only support for Linux."
  exit 1
fi

architecture="$(uname -i)"
if [[ $architecture != x86_64 ]]; then
  print_error_message "Only support for x86_64."
  exit 1
fi

opts="$(getopt -n "install-chromedriver.sh" -l prefix:,help -- h "$@")"
eval set -- "$opts"

prefix=/usr/local
while test "$#" -ne 0; do
  arg="$1"
  shift
  case "$arg" in
  '--prefix')
    if (($# == 0)); then
      print_error_message "error: A logic error."
      exit 1
    fi
    prefix="$1"
    shift
    ;;
  '-h'|'--help')
    set +x
    print_usage
    exit 0
    ;;
  '--')
    if (($# > 0)); then
      print_error_message "error: An invalid argument \`$1'."
      print_error_message "Try \`install-chromedriver.sh --help' for more information."
      exit 1
    fi
    ;;
  *)
    print_error_message "error: An invalid argument \`$arg'."
    print_error_message "Try \`install-chromedriver.sh --help' for more information."
    exit 1
    ;;
  esac
done

tempdir=$(mktemp -d)
trap "rm -rf '$tempdir'" EXIT

chromedriver_basename="$(basename "$chromedriver_url")"

if which wget >/dev/null 2>&1; then
  (cd "$tempdir" && wget "$chromedriver_url")
elif which curl >/dev/null 2>&1; then
  (cd "$tempdir" && curl -o "$chromedriver_basename" -L "$chromedriver_url")
else
  print_error_message "Either \`wget' or \`curl' is required."
  exit 1
fi

mkdir -p "$prefix/bin"
unzip "$tempdir/$chromedriver_basename" -d "$prefix/bin"
