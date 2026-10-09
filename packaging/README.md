# Packaging

FleetCommander (`fcwm`) is pure Python. Every package installs the same files:

| Path | Content |
|---|---|
| `/usr/bin/fcwm` | entry point (`fcwm.cli:main`) |
| Python `site-packages`/`dist-packages` | package `fcwm` incl. `fcwm/static/*.html` |
| `/usr/lib/systemd/user/fcwm.service` | systemd **user** unit (`ExecStart=/usr/bin/fcwm web`), not enabled automatically |
| `/usr/share/applications/fcwm.desktop` | menu entry ("FleetCommander", runs `fcwm open`) |
| `/usr/share/doc/fcwm/` | `README.md`, `README.de.md`, `config.example.yaml` |
| license | `LICENSE` (GPL-3.0-or-later) |

## Distributions

| Distribution | Files | Build | Install |
|---|---|---|---|
| Arch Linux / Manjaro | `arch/PKGBUILD`, `arch/fcwm.install` | `cd packaging/arch && makepkg -s` | `sudo pacman -U fcwm-*.pkg.tar.zst` (or `makepkg -si`) |
| Debian 13 (trixie)+, Ubuntu/Kubuntu 25.04+ | `debian/` | `packaging/debian/build-deb.sh` | `sudo apt install ./packaging/debian/out/fcwm_<ver>_all.deb` |
| Fedora 43+ | `rpm/fcwm.spec` | `packaging/rpm/build-rpm.sh` | `sudo dnf install ~/rpmbuild/RPMS/noarch/fcwm-<ver>-1.*.noarch.rpm` |
| openSUSE Tumbleweed | `rpm/fcwm.spec` | `packaging/rpm/build-rpm.sh` | `sudo zypper install ~/rpmbuild/RPMS/noarch/fcwm-<ver>-1.*.noarch.rpm` |
| anything else | `install.sh` | – | `packaging/install.sh` (per user) or `sudo packaging/install.sh --prefix /usr/local` |

Plasma 6 is required for the KWin backend (Debian/Ubuntu releases with Plasma 5 lack
`libkf6config-bin`). Building needs **setuptools ≥ 77** (`pyproject.toml` uses the SPDX
`license` string and `license-files`), which rules out e.g. Fedora 42 and Ubuntu 25.04 for
building – build there with a newer setuptools or use `install.sh`.

### Debian / Ubuntu

`dpkg-buildpackage` needs `debian/` at the source root, so `build-deb.sh` copies the project
files (same selection as the PKGBUILD: `fcwm`, `tests`, `pyproject.toml`, READMEs,
`config.example.yaml`, `LICENSE`, `packaging/fcwm.{service,desktop}` – never your personal
`config.yaml`) plus `packaging/debian/*` into a temporary directory and runs
`dpkg-buildpackage -us -uc -b` there. Result: `packaging/debian/out/`.

```sh
sudo apt install dpkg-dev debhelper dh-python pybuild-plugin-pyproject \
                 python3-all python3-setuptools python3-wheel python3-yaml
packaging/debian/build-deb.sh            # extra args go to dpkg-buildpackage
DEB_BUILD_OPTIONS=nocheck packaging/debian/build-deb.sh   # skip the unit tests
```

Build uses `dh` + `dh-python` + pybuild (pyproject plugin), source format `3.0 (native)`.
The user unit is installed via `debian/fcwm.install` (not `dh_installsystemduser`, which
would enable it for every user). `README.md` stays uncompressed because the unit's
`Documentation=` points to it.

### Fedora / openSUSE

`build-rpm.sh` packs the same file selection into `~/rpmbuild/SOURCES/fcwm-<ver>.tar.gz`
and runs `rpmbuild -ba` (set `RPM_TOPDIR` for another tree; extra args go to rpmbuild).

```sh
# Fedora
sudo dnf install rpm-build python3-devel pyproject-rpm-macros python3-setuptools \
                 python3-pyyaml systemd-rpm-macros desktop-file-utils
# openSUSE
sudo zypper install rpm-build python3-pip python3-setuptools python3-wheel \
                    python3-PyYAML systemd-rpm-macros desktop-file-utils
packaging/rpm/build-rpm.sh
```

On Fedora the spec uses `%pyproject_buildrequires`/`%pyproject_wheel`/`%pyproject_install`/
`%pyproject_save_files`; if rpmbuild stops on missing generated build requirements, run
`sudo dnf builddep ~/rpmbuild/SRPMS/fcwm-*.buildreqs.nosrc.rpm` and build again. On openSUSE
(`%if 0%{?suse_version}`) the wheel is built and installed with `pip --no-index
--no-build-isolation`. KDE/systemd tools are required by file path (`/usr/bin/kwriteconfig6`,
`/usr/bin/kscreen-doctor`, …) so the same spec resolves on both distributions.

### Other distributions: `install.sh`

No pip, no network: copies the `fcwm` package to `~/.local/share/fcwm/lib/` (or
`<prefix>/lib/fcwm/`), writes a small launcher `~/.local/bin/fcwm` (`<prefix>/bin/fcwm`) that
runs `python3 -m fcwm`, and installs the unit (`~/.config/systemd/user/` or
`<prefix>/lib/systemd/user/`, `ExecStart=` rewritten to the launcher), the desktop file
(`~/.local/share/applications/` or `<prefix>/share/applications/`) and the docs. It never calls
`sudo` itself – for a system-wide install run it as root yourself. Install python3, PyYAML and
the KDE tools below with your package manager first.

```sh
packaging/install.sh                                  # per user
packaging/install.sh --uninstall
sudo packaging/install.sh --prefix /usr/local         # system-wide
sudo packaging/install.sh --prefix /usr/local --uninstall
```

## Dependencies per distribution

| What | Arch | Debian / Ubuntu | Fedora | openSUSE |
|---|---|---|---|---|
| Python ≥ 3.10 | `python` | `python3` | `python3` | `python3` |
| PyYAML | `python-yaml` | `python3-yaml` | `python3-pyyaml` | `python3-PyYAML` |
| `busctl`, `journalctl` | `systemd` | `systemd` | `systemd` | `systemd` |
| KWin (Plasma 6) | `kwin` | `kwin-wayland` \| `kwin-x11` | `kwin` (`kwin-wayland`/`kwin-x11`) | `kwin6` |
| `kwriteconfig6`, `kreadconfig6` | `kconfig` | `libkf6config-bin` | `/usr/bin/kwriteconfig6` (kf6-kconfig) | `/usr/bin/kwriteconfig6` (kf6-kconfig) |
| `kscreen-doctor` | `kscreen` | `libkscreen-bin` | `/usr/bin/kscreen-doctor` (libkscreen) | `/usr/bin/kscreen-doctor` (libkscreen) |
| `xdg-open` | `xdg-utils` | `xdg-utils` | `xdg-utils` | `xdg-utils` |
| *recommended* ruamel.yaml (keeps comments in `config.yaml`) | `python-ruamel-yaml` | `python3-ruamel.yaml` | `python3-ruamel-yaml` | `python3-ruamel.yaml` |
| PyQt6-WebEngine (app window, `fcwm app`) – a dependency of all packages; for `install.sh` install it yourself | `python-pyqt6-webengine` | `python3-pyqt6.qtwebengine` | `python3-pyqt6-webengine` | `python3-PyQt6-WebEngine` |
| *optional* X11 backend without KWin | `wmctrl xdotool xorg-xrandr` | `wmctrl xdotool x11-xserver-utils` | `wmctrl xdotool xrandr` | `wmctrl xdotool xrandr` |

The RPM spec requires the KDE/systemd tools by file path; the package names in that table are
for orientation only.

## After installing

```sh
fcwm init                                  # starter config in ~/.config/fcwm/
systemctl --user enable --now fcwm         # start with the Plasma session
xdg-open http://127.0.0.1:8765/            # web UI (or "FleetCommander" in the menu)
```

After an upgrade: `fcwm restart`.

## Uninstall / cleanup

**Before** removing the package, as your user (not root):

```sh
systemctl --user disable --now fcwm
fcwm cleanup        # removes fcwm's KWin window rules, color schemes and shortcuts
```

Then remove it: `sudo pacman -R fcwm` / `sudo apt remove fcwm` / `sudo dnf remove fcwm` /
`sudo zypper remove fcwm` / `packaging/install.sh --uninstall`. Your configuration in
`~/.config/fcwm/` is left untouched; delete it by hand if you want.

## Releasing a new version

Releases are built and published by GitHub Actions (`.github/workflows/release.yml`):

```bash
packaging/bump-version.sh 0.3.0 "Short changelog line"
git commit -am "Release 0.3.0"
git tag v0.3.0
git push && git push origin v0.3.0
```

`bump-version.sh` sets the version in `pyproject.toml`, `fcwm/__init__.py`, the PKGBUILD (`pkgrel=1`),
the RPM spec (default version + `%changelog`) and `debian/changelog`. The tag push then runs the tests,
checks that all of these match the tag, builds the Arch package (`archlinux:base-devel`), the `.deb`
(`debian:trixie`), the `.rpm` (`fedora:latest`) and wheel + sdist, and attaches them with a `SHA256SUMS`
file and install instructions to a new GitHub release. Running the workflow by hand
(Actions → release → Run workflow) only builds the packages as artifacts, without a release.
