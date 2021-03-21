%global         debug_package %{nil}
%global         __strip /bin/true
%global         snap 1

# Remove bundled libraries from requirements/provides
%global         __requires_exclude ^(libcef\\.so.*|libwidevinecdm.*\\.so.*|libEGL\\.so.*|libGLESv2\\.so.*|libcurl-gnutls\\.so\\..*)$
%global         __provides_exclude ^(lib.*\\.so.*)$

Name:           spotify-client
Summary:        Spotify music player native client
Version:        1.1.55.498.gf9a83c60
Release:        1%{?dist}
Epoch:          1
License:        https://www.spotify.com/legal/end-user-agreement
URL:            http://www.spotify.com/
ExclusiveArch:  x86_64

%if 0%{?snap:1}
# Get it with:
# curl -H 'Snap-Device-Series: 16' http://api.snapcraft.io/v2/snaps/info/spotify | jq
Source0:        https://api.snapcraft.io/api/v1/snaps/download/pOBIoZ2LrCB3rDohMxoYGnbN14EHOgD7_46.snap
%else
Source0:        http://repository.spotify.com/pool/non-free/s/%{name}/%{name}_%{version}-37_amd64.deb
%endif

Source2:        spotify-wrapper
Source3:        spotify.xml
Source4:        spotify.appdata.xml

Source10:       README.Fedora

BuildRequires:  chrpath
BuildRequires:  desktop-file-utils
BuildRequires:  firewalld-filesystem
BuildRequires:  libappstream-glib

%if 0%{?snap:1}
BuildRequires:  squashfs-tools
%endif

Provides:       spotify = %{version}-%{release}

Requires:       firewalld-filesystem
Requires(post): firewalld-filesystem
Requires:       hicolor-icon-theme
# Chrome Embedded Framework dynamically loads libXss.so.1:
Requires:       libXScrnSaver%{?_isa}
Requires:       spotify-curl%{?_isa}
Requires:       spotify-ffmpeg%{?_isa}

%description
Think of Spotify as your new music collection. Your library. Only this time your
collection is vast: millions of tracks and counting. Spotify comes in all shapes
and sizes, available for your PC, Mac, home audio system and mobile phone.
Wherever you go, your music follows you. And because the music plays live,
there’s no need to wait for downloads and no big dent in your hard drive.

%prep
%setup -q -c -T

%if 0%{?snap:1}
unsquashfs -f -d . %{SOURCE0}
%else
ar x %{SOURCE0}
tar -xzf data.tar.gz
%endif

chrpath -d .%{_datadir}/spotify/spotify

sed -i -e 's/^Icon=.*/Icon=spotify/g' .%{_datadir}/spotify/spotify.desktop

cp %{SOURCE10} .

%build
# Nothing to build

%install
mkdir -p %{buildroot}%{_libdir}/%{name}

# Program resources
cp -frp .%{_datadir}/spotify/* %{buildroot}%{_libdir}/%{name}
rm -fr %{buildroot}%{_libdir}/%{name}/{apt-keys,icons,*.desktop}

# Set permissions
find %{buildroot}%{_libdir}/%{name} -name "*.so" -exec chmod 755 {} \;
chmod 755 %{buildroot}%{_libdir}/%{name}/spotify

# 512x512 icon along main executable is needed by the client
install -p -D -m 644 .%{_datadir}/spotify/icons/spotify-linux-512.png \
    %{buildroot}%{_libdir}/%{name}/icons/spotify-linux-512.png

# Wrapper script
mkdir -p %{buildroot}%{_bindir}
cat %{SOURCE2} | sed -e 's|INSTALL_DIR|%{_libdir}/%{name}|g' \
    > %{buildroot}%{_bindir}/spotify
chmod +x %{buildroot}%{_bindir}/spotify

# Desktop file
install -m 0644 -D -p .%{_datadir}/spotify/spotify.desktop \
    %{buildroot}%{_datadir}/applications/spotify.desktop
desktop-file-validate %{buildroot}%{_datadir}/applications/spotify.desktop

# Icons
for size in 16 22 24 32 48 64 128 256 512; do
    install -p -D -m 644 .%{_datadir}/spotify/icons/spotify-linux-${size}.png \
        %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/spotify.png
done

# Firewalld rules
install -D -m 644 -p %{SOURCE3} \
    %{buildroot}%{_prefix}/lib/firewalld/services/spotify.xml

# Install AppData
mkdir -p %{buildroot}%{_metainfodir}/
install -p -m 0644 %{SOURCE4} %{buildroot}%{_metainfodir}/
appstream-util validate-relax --nonet %{buildroot}/%{_metainfodir}/spotify.appdata.xml

%post
%firewalld_reload

%files
%doc README.Fedora
%{_bindir}/spotify
%{_datadir}/applications/spotify.desktop
%{_datadir}/icons/hicolor/*/apps/spotify.png
%{_libdir}/%{name}
%{_metainfodir}/spotify.appdata.xml
%{_prefix}/lib/firewalld/services/spotify.xml

%changelog
* Sun Mar 21 2021 Simone Caronni <negativo17@gmail.com> - 1:1.1.55.498.gf9a83c60-1
- Update to 1.1.55.498.gf9a83c60.

* Tue Feb 09 2021 Simone Caronni <negativo17@gmail.com> - 1:1.1.52.687.gf5565fe5-1
- Update to 1.1.52.687.gf5565fe5.

* Sat Dec 26 2020 Simone Caronni <negativo17@gmail.com> - 1:1.1.46.916.g416cacf1-1
- Update to 1.1.46.916.g416cacf1.
- Allow unpacking snap archive directly from SPEC file.

* Sat Oct 03 2020 Christian Birk <chris.h3o66@gmail.com> - 1:1.1.42.622.gbd112320-1
- Update to 1.1.42.622.gbd112320 from deb.

* Wed Feb 12 2020 Simone Caronni <negativo17@gmail.com> - 1:1.1.26.501.gbe11e53b-1
- Update to 1.1.26.501.gbe11e53b from snap.
- Fix desktop icon.

* Sun Sep 29 2019 Simone Caronni <negativo17@gmail.com> - 1:1.1.10.546.ge08ef575-2
- Fix Obsoletes as per new packaging guidelines.

* Thu Jul 18 2019 Simone Caronni <negativo17@gmail.com> - 1:1.1.10.546.ge08ef575-1
- Update to 1.1.10.546.ge08ef575.

* Fri May 03 2019 Simone Caronni <negativo17@gmail.com> - 1:1.1.5.153.gf614956d-1
- Update to 1.1.5.153.gf614956d.

* Mon Feb 18 2019 Simone Caronni <negativo17@gmail.com> - 1:1.1.0.237.g378f6f25-1
- Update to 1.1.0.237.g378f6f25.
- Trim changelog.

* Sat Feb 02 2019 Simone Caronni <negativo17@gmail.com> - 1:1.0.98.78.gb45d2a6b-1
- Update to 1.0.98.78.gb45d2a6b.
- Remove RHEL/CentOS 7 support, no longer supported due to Chrome Embedded
- Framework requiring glibc 2.18+.

* Sat Jan 12 2019 Simone Caronni <negativo17@gmail.com> - 1:1.0.96.181.gf6bc1b6b-1
- Update to 1.0.96.181.gf6bc1b6b.

* Thu Dec 06 2018 Simone Caronni <negativo17@gmail.com> - 1:1.0.94.262.g3d5c231c-1
- Update to 1.0.94.262.g3d5c231c.

* Fri Oct 26 2018 Simone Caronni <negativo17@gmail.com> - 1:1.0.92.390.g2ce5ec7d-1
- Update to 1.0.92.390.g2ce5ec7d.

* Fri Sep 14 2018 Simone Caronni <negativo17@gmail.com> - 1:1.0.89.313.g34a58dea-1
- Update to 1.0.89.313.g34a58dea.

* Thu Aug 23 2018 Simone Caronni <negativo17@gmail.com> - 1:1.0.88.353.g15c26ea1-1
- Update to 1.0.88.353.g15c26ea1.

* Sun Aug 19 2018 Simone Caronni <negativo17@gmail.com> - 1:1.0.88.345.gc64d9bb3-1
- Update to 1.0.88.345.gc64d9bb3.

* Tue Jul 24 2018 Simone Caronni <negativo17@gmail.com> - 1:1.0.80.480.g51b03ac3-2
- Update build requirements.

* Thu May 31 2018 Simone Caronni <negativo17@gmail.com> - 1:1.0.80.480.g51b03ac3-1
- Update to version 1.0.80.480.g51b03ac3.

* Fri Apr 27 2018 Simone Caronni <negativo17@gmail.com> - 1:1.0.79.223.g92622cc2-1
- Update to 1.0.79.223.g92622cc2.

* Mon Apr 23 2018 Simone Caronni <negativo17@gmail.com> - 1:1.0.77.338.g758ebd78-2
- Update filters and requirements.

* Mon Apr 23 2018 Simone Caronni <negativo17@gmail.com> - 1:1.0.77.338.g758ebd78-1
- Update to 1.0.77.338.g758ebd78.
- Remove i686 support.

* Mon Mar 05 2018 Simone Caronni <negativo17@gmail.com> - 1:1.0.72.117.g6bd7cc73-1
- Update to 1.0.72.117.g6bd7cc73.

* Sat Jan 06 2018 Simone Caronni <negativo17@gmail.com> - 1:1.0.70.399.g5ffabd56-1
- Update to 1.0.70.399.g5ffabd56.
- OpenSSL requirement has switched to 1.1, so add a spotify-openssl 1.1 package
  to RHEL/CentOS and obsolete the 1.0 one in Fedora.
- Require CURL update only on Fedora 27 (too new) and RHEL 7 (too old).
