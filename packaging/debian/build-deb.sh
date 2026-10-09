#!/usr/bin/env bash
# Build fcwm_<version>_all.deb from this repository (Debian trixie / Ubuntu 25.04+).
#
# Build dependencies:
#   sudo apt install dpkg-dev debhelper dh-python pybuild-plugin-pyproject \
#                    python3-all python3-setuptools python3-wheel python3-yaml
#
# Usage: packaging/debian/build-deb.sh [extra dpkg-buildpackage args]
# Output: packaging/debian/out/ (override with OUT_DIR=...)
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
top=$(cd "$here/../.." && pwd)
out=${OUT_DIR:-$here/out}

version=$(sed -n 's/^version *= *"\([^"]*\)".*/\1/p' "$top/pyproject.toml" | head -n1)
[[ -n $version ]] || { echo "error: no version in pyproject.toml" >&2; exit 1; }

if ! command -v dpkg-buildpackage >/dev/null; then
    echo "error: dpkg-buildpackage not found. Install the build dependencies:" >&2
    sed -n '5,6p' "$0" | sed 's/^# *//' >&2
    exit 1
fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
src="$work/fcwm-$version"

# same file selection as packaging/arch/PKGBUILD prepare() – no personal config.yaml/state
mkdir -p "$src/packaging" "$src/debian/source"
cp -r "$top"/{fcwm,tests,pyproject.toml,README.md,README.de.md,config.example.yaml,LICENSE,NOTICE} "$src/"
cp "$top"/packaging/fcwm.{service,desktop} "$src/packaging/"
cp "$here"/{control,rules,changelog,copyright,fcwm.install,fcwm.docs,postinst,prerm} "$src/debian/"
cp "$here/source/format" "$src/debian/source/"
find "$src" -name __pycache__ -type d -prune -exec rm -rf {} +

# version comes from pyproject.toml; add a changelog entry in the staged copy if needed
deb_version=$(sed -n '1s/^fcwm (\([^)]*\)).*/\1/p' "$here/changelog")
if [[ $deb_version != "$version" ]]; then
    echo "warning: debian/changelog is at $deb_version, pyproject.toml at $version –" \
         "adding a temporary entry (please update packaging/debian/changelog)" >&2
    {
        printf 'fcwm (%s) unstable; urgency=medium\n\n  * New upstream version %s.\n\n' "$version" "$version"
        printf ' -- %s  %s\n\n' "Jan-Frederic Schubert <jfschubert@gmail.com>" "$(LC_ALL=C date -R)"
        cat "$here/changelog"
    } > "$src/debian/changelog"
fi

(cd "$src" && dpkg-buildpackage -us -uc -b "$@")

mkdir -p "$out"
mv "$work"/*.deb "$out/"
mv "$work"/*.buildinfo "$work"/*.changes "$out/" 2>/dev/null || true
echo "==> built: $(ls "$out"/fcwm_"$version"*_all.deb)"
echo "    install: sudo apt install $out/fcwm_${version}_all.deb"
