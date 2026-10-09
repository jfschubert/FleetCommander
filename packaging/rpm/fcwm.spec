# FleetCommander (fcwm) – Fedora (40+) and openSUSE Tumbleweed.
# Build with packaging/rpm/build-rpm.sh, which passes the version from pyproject.toml
# as fcwm_version; the default below is used when building the spec directly.
%{!?fcwm_version:%global fcwm_version 0.2.0}
%{!?_userunitdir:%global _userunitdir %{_prefix}/lib/systemd/user}

Name:           fcwm
Version:        %{fcwm_version}
Release:        1%{?dist}
Summary:        EVE Online window manager for KDE Plasma
License:        GPL-3.0-or-later
URL:            https://github.com/jfschubert/FleetCommander
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools >= 77
BuildRequires:  systemd-rpm-macros
BuildRequires:  desktop-file-utils
%if 0%{?suse_version}
# openSUSE: build the wheel with pip (no %%pyproject_save_files there)
BuildRequires:  python3-pip
BuildRequires:  python3-wheel
BuildRequires:  python3-PyYAML
%else
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3-pyyaml
%endif

%if 0%{?suse_version}
Requires:       python3 >= 3.10
Requires:       python3-PyYAML
Recommends:     python3-ruamel.yaml
Requires:       python3-PyQt6-WebEngine
%else
Requires:       python3-pyyaml
Recommends:     python3-ruamel-yaml
Requires:       python3-pyqt6-webengine
%endif
# file-based requirements resolve to the right package on Fedora and openSUSE
Requires:       /usr/bin/busctl
Requires:       /usr/bin/journalctl
Requires:       /usr/bin/kwriteconfig6
Requires:       /usr/bin/kreadconfig6
Requires:       /usr/bin/kscreen-doctor
Requires:       /usr/bin/xdg-open
Requires:       (/usr/bin/kwin_wayland or /usr/bin/kwin_x11)
# X11 backend without KWin
Suggests:       wmctrl
Suggests:       xdotool
Suggests:       xrandr

%description
FleetCommander (fcwm) arranges EVE Online client windows on KDE Plasma 6
(Wayland and X11): grid layouts, profiles, window stacks, global hotkeys and
live previews, controlled through a local web UI.

%prep
%autosetup -n %{name}-%{version}

%if ! 0%{?suse_version}
%generate_buildrequires
%pyproject_buildrequires
%endif

%build
%if 0%{?suse_version}
%{__python3} -m pip wheel --no-deps --no-build-isolation --no-index \
    --disable-pip-version-check --wheel-dir dist .
%else
%pyproject_wheel
%endif

%install
%if 0%{?suse_version}
%{__python3} -m pip install --no-deps --no-index --disable-pip-version-check \
    --no-warn-script-location --root %{buildroot} --prefix %{_prefix} dist/*.whl
rm -f %{buildroot}%{python3_sitelib}/%{name}-%{version}.dist-info/direct_url.json
sed -i '/direct_url.json/d' %{buildroot}%{python3_sitelib}/%{name}-%{version}.dist-info/RECORD
%else
%pyproject_install
%pyproject_save_files -l fcwm
%endif
install -Dm644 packaging/fcwm.service %{buildroot}%{_userunitdir}/fcwm.service
install -Dm644 packaging/fcwm.desktop %{buildroot}%{_datadir}/applications/fcwm.desktop
install -Dm644 fcwm/static/fcwm.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/fcwm.svg

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/fcwm.desktop
%{__python3} -m unittest discover -s tests -v

%post
%if %{defined systemd_user_post}
%systemd_user_post fcwm.service
%endif
if [ "$1" -eq 1 ]; then
cat <<'MSG'
==> FleetCommander (fcwm) installed.
    1. Create a starter config:    fcwm init
    2. Start it with your session: systemctl --user enable --now fcwm
       (or run `fcwm web` manually)
    3. Open the web UI:            http://127.0.0.1:8765/  (or "FleetCommander" in the menu)
MSG
else
    echo "==> Restart the running instance to use the new version: fcwm restart"
fi

%preun
%if %{defined systemd_user_preun}
%systemd_user_preun fcwm.service
%endif
if [ "$1" -eq 0 ]; then
cat <<'MSG'
==> Before removing, as your user (not root):
      systemctl --user disable --now fcwm
      fcwm cleanup      # removes fcwm's KWin window rules, color schemes and shortcuts
    Your config in ~/.config/fcwm/ is left untouched.
MSG
fi

%if 0%{?suse_version}
%files
%{python3_sitelib}/fcwm/
%{python3_sitelib}/fcwm-%{version}.dist-info/
%else
%files -f %{pyproject_files}
%endif
%license LICENSE NOTICE
%doc README.md README.de.md config.example.yaml
%{_bindir}/fcwm
%{_userunitdir}/fcwm.service
%{_datadir}/applications/fcwm.desktop
%{_datadir}/icons/hicolor/scalable/apps/fcwm.svg

%changelog
* Fri Oct 09 2026 Jan-Frederic Schubert <jfschubert@gmail.com> - 0.2.0-1
- Initial RPM packaging
