#!/usr/bin/env bash
# Build fcwm-<version>-1.*.noarch.rpm (+ .src.rpm) on Fedora or openSUSE.
#
# Build dependencies:
#   Fedora:   sudo dnf install rpm-build python3-devel pyproject-rpm-macros python3-setuptools \
#                              python3-pyyaml systemd-rpm-macros desktop-file-utils
#   openSUSE: sudo zypper install rpm-build python3-pip python3-setuptools python3-wheel \
#                              python3-PyYAML systemd-rpm-macros desktop-file-utils
#
# Usage: packaging/rpm/build-rpm.sh [extra rpmbuild args]
# Output: ~/rpmbuild/RPMS/noarch/ and ~/rpmbuild/SRPMS/ (override with RPM_TOPDIR=...)
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
top=$(cd "$here/../.." && pwd)
topdir=${RPM_TOPDIR:-$HOME/rpmbuild}

version=$(sed -n 's/^version *= *"\([^"]*\)".*/\1/p' "$top/pyproject.toml" | head -n1)
[[ -n $version ]] || { echo "error: no version in pyproject.toml" >&2; exit 1; }

if ! command -v rpmbuild >/dev/null; then
    echo "error: rpmbuild not found. Install the build dependencies:" >&2
    sed -n '5,8p' "$0" | sed 's/^# *//' >&2
    exit 1
fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
src="$work/fcwm-$version"

# same file selection as packaging/arch/PKGBUILD prepare() – no personal config.yaml/state
mkdir -p "$src/packaging"
cp -r "$top"/{fcwm,tests,pyproject.toml,README.md,README.de.md,config.example.yaml,LICENSE,NOTICE} "$src/"
cp "$top"/packaging/fcwm.{service,desktop} "$src/packaging/"
find "$src" -name __pycache__ -type d -prune -exec rm -rf {} +

mkdir -p "$topdir"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
tar --sort=name --owner=0 --group=0 --numeric-owner -czf "$topdir/SOURCES/fcwm-$version.tar.gz" \
    -C "$work" "fcwm-$version"
cp "$here/fcwm.spec" "$topdir/SPECS/fcwm.spec"

rpmbuild -ba --define "_topdir $topdir" --define "fcwm_version $version" \
    "$topdir/SPECS/fcwm.spec" "$@"

echo "==> built:"; ls "$topdir"/RPMS/noarch/fcwm-"$version"-*.rpm
echo "    install: sudo dnf install <rpm>   or   sudo zypper install <rpm>"
