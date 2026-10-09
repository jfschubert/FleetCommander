#!/usr/bin/env bash
# Set a new version everywhere it is recorded, ready for a release tag.
#
# Usage: packaging/bump-version.sh 0.3.0 ["changelog line"]
#
# Updates pyproject.toml, fcwm/__init__.py, packaging/arch/PKGBUILD (pkgrel back to 1),
# the default version and a %changelog entry in packaging/rpm/fcwm.spec and a packaging/debian/changelog entry.
# Pushing the tag v<version> then builds and publishes the release (.github/workflows/release.yml).
set -euo pipefail

new=${1:-}
note=${2:-"New upstream version $new."}
[[ $new =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "usage: $0 X.Y.Z [changelog line]" >&2; exit 1; }

top=$(cd "$(dirname "$0")/.." && pwd)
cd "$top"
old=$(sed -n 's/^version *= *"\([^"]*\)".*/\1/p' pyproject.toml | head -n1)
[[ $new != "$old" ]] || { echo "already at $new" >&2; exit 1; }

sed -i "s/^version *= *\"$old\"/version = \"$new\"/" pyproject.toml
sed -i "s/^__version__ = \".*\"/__version__ = \"$new\"/" fcwm/__init__.py
sed -i -e "s/^pkgver=.*/pkgver=$new/" -e "s/^pkgrel=.*/pkgrel=1/" packaging/arch/PKGBUILD
sed -i "s/%global fcwm_version [^}]*}/%global fcwm_version $new}/" packaging/rpm/fcwm.spec
sed -i "/^%changelog/a * $(LC_ALL=C date '+%a %b %d %Y') Jan-Frederic Schubert <jfschubert@gmail.com> - $new-1\\n- $note\\n" packaging/rpm/fcwm.spec
{
    printf 'fcwm (%s) unstable; urgency=medium\n\n  * %s\n\n' "$new" "$note"
    printf ' -- %s  %s\n\n' "Jan-Frederic Schubert <jfschubert@gmail.com>" "$(LC_ALL=C date -R)"
    cat packaging/debian/changelog
} > packaging/debian/changelog.new
mv packaging/debian/changelog.new packaging/debian/changelog

echo "==> $old -> $new"
git --no-pager diff --stat 2>/dev/null || true
cat <<EOF

Next steps:
  git commit -am "Release $new"
  git tag v$new
  git push && git push origin v$new      # GitHub Actions builds and publishes the release
EOF
