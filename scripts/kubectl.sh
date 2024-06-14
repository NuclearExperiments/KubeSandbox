#!/usr/bin/env bash

# The install script is based off of the MIT-licensed script from glide,
# the package manager for Go: https://github.com/Masterminds/glide.sh/blob/master/get

: ${BINARY_NAME:="kubectl"}
: ${USE_SUDO:="true"}
: ${HELM_INSTALL_DIR:="/usr/local/bin"}
: ${VERIFY_CHECKSUM:="true"}

HAS_CURL="$(type "curl" &> /dev/null && echo true || echo false)"
HAS_WGET="$(type "wget" &> /dev/null && echo true || echo false)"
HAS_OPENSSL="$(type "openssl" &> /dev/null && echo true || echo false)"
HAS_GPG="$(type "gpg" &> /dev/null && echo true || echo false)"
HAS_GIT="$(type "git" &> /dev/null && echo true || echo false)"

# initArch discovers the architecture for this system.
initArch() {
  ARCH=$(uname -m)
  case $ARCH in
    armv5*) ARCH="armv5";;
    armv6*) ARCH="armv6";;
    armv7*) ARCH="arm";;
    aarch64) ARCH="arm64";;
    x86) ARCH="386";;
    x86_64) ARCH="amd64";;
    i686) ARCH="386";;
    i386) ARCH="386";;
  esac
}

initOS() {
  OS=$(echo `uname`|tr '[:upper:]' '[:lower:]')

  case "$OS" in
    # Minimalist GNU for Windows
    mingw*|cygwin*) OS='windows';;
  esac
}

# checkDesiredVersion checks if the desired version is available.
checkDesiredVersion() {
  if [ "x$DESIRED_VERSION" == "x" ]; then
    # Get tag from release URL
    local latest_release_url="https://dl.k8s.io/release/stable.txt"
    local latest_release_response=""
    if [ "${HAS_CURL}" == "true" ]; then
      latest_release_response=$( curl -L --silent --show-error --fail "$latest_release_url" 2>&1 || true )
    elif [ "${HAS_WGET}" == "true" ]; then
      latest_release_response=$( wget "$latest_release_url" -q -O - 2>&1 || true )
    fi
    TAG=$( echo "$latest_release_response" | grep '^v[0-9]' )
    if [ "x$TAG" == "x" ]; then
      printf "Could not retrieve the latest release tag information from %s: %s\n" "${latest_release_url}" "${latest_release_response}"
      exit 1
    fi
  else
    TAG=$DESIRED_VERSION
  fi
}

runAsRoot() {
  if [ $EUID -ne 0 -a "$USE_SUDO" = "true" ]; then
    sudo "${@}"
  else
    "${@}"
  fi
}


# downloadFile downloads the latest binary package and also the checksum
# for that binary.
downloadFile() {
  DOWNLOAD_URL="https://dl.k8s.io/release/$TAG/bin/$OS/$ARCH/kubectl"
  if [ "${HAS_CURL}" == "true" ]; then
    curl -SsL "$DOWNLOAD_URL" -o "kubectl"
  elif [ "${HAS_WGET}" == "true" ]; then
    wget -q -O "kubectl" "$DOWNLOAD_URL"
  fi
}

# installFile installs the Helm binary.
installFile() {
  runAsRoot install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
  rm kubectl
  echo "Installed successfully"
}


set -e
# set -x


initArch
initOS
checkDesiredVersion
downloadFile
installFile
