%global         debug_package %{nil}
%global         __strip /bin/true

# Remove bundled libraries from requirements/provides
%global         __requires_exclude ^(libcef\\.so.*|libffmpegsumo\\.so.*|libcrypto\\.so\\..*|libssl\\.so\\..*|libcurl\\.so\\..*|libwidevine.*\\.so.*)$
%global         __provides_exclude ^(lib.*\\.so.*)$

# If firewalld macro is not defined, define it here:
%{!?firewalld_reload:%global firewalld_reload test -f /usr/bin/firewall-cmd && firewall-cmd --reload --quiet || :}

Name:           spotify-client
Summary:        Spotify music player native client
Version:        1.0
Release:        15%{?dist}
Epoch:          1
License:        https://www.spotify.com/legal/end-user-agreement
URL:            http://www.spotify.com/
ExclusiveArch:  x86_64 %{ix86}

# Misaligned versions between 32 and 64 bit, sometimes on minor releases as well. Just use the base version.
Source0:        http://repository.spotify.com/pool/non-free/s/%{name}/%{name}_%{version}.49.125.g72ee7853-111_amd64.deb
Source1:        http://repository.spotify.com/pool/non-free/s/%{name}/%{name}_%{version}.49.125.g72ee7853-22_i386.deb
Source2:        spotify-wrapper
Source3:        spotify.xml
Source4:        spotify.appdata.xml

Source10:       README.Fedora

BuildRequires:  chrpath
BuildRequires:  desktop-file-utils

%if 0%{?fedora} >= 25
BuildRequires:  libappstream-glib
%endif

Provides:       spotify = %{version}-%{release}
Requires:       hicolor-icon-theme
Requires:       spotify-ffmpeg%{?_isa}
Requires:       spotify-openssl%{?_isa}

# Required for the firewall rules
# http://fedoraproject.org/wiki/PackagingDrafts/ScriptletSnippets/Firewalld
%if 0%{?rhel}
Requires:       firewalld
Requires(post): firewalld
%else
Requires:       firewalld-filesystem
Requires(post): firewalld-filesystem
%endif

%description
Think of Spotify as your new music collection. Your library. Only this time your
collection is vast: millions of tracks and counting. Spotify comes in all shapes
and sizes, available for your PC, Mac, home audio system and mobile phone.
Wherever you go, your music follows you. And because the music plays live,
there’s no need to wait for downloads and no big dent in your hard drive.

%prep
%setup -q -c -T

%ifarch x86_64
ar x %{SOURCE0}
tar -xzf data.tar.gz
%endif

%ifarch %{ix86}
ar x %{SOURCE1}
tar -xzf data.tar.gz
%endif

chrpath -d \
    .%{_datadir}/spotify/libwidevinecdmadapter.so \
    .%{_datadir}/spotify/spotify

cp %{SOURCE10} .

%build
# Nothing to build

%install
mkdir -p %{buildroot}%{_libdir}/%{name}

# Program resources - 512x512 icon along main executable is needed by the client
cp -frp \
    .%{_datadir}/spotify/*.{pak,dat,bin} \
    .%{_datadir}/spotify/{Apps,locales} \
    %{buildroot}%{_libdir}/%{name}
install -p -D -m 644 .%{_datadir}/spotify/icons/spotify-linux-512.png \
    %{buildroot}%{_libdir}/%{name}/icons/spotify-linux-512.png

# Binaries
install -p -m 755 \
    .%{_datadir}/spotify/*.so \
    .%{_datadir}/spotify/spotify \
    %{buildroot}%{_libdir}/%{name}/

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
        %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/%{name}.png
done

# Firewalld rules
install -D -m 644 -p %{SOURCE3} \
    %{buildroot}%{_prefix}/lib/firewalld/services/spotify.xml

%if 0%{?fedora} >= 25
# Install AppData
mkdir -p %{buildroot}%{_datadir}/appdata
install -p -m 0644 %{SOURCE4} %{buildroot}%{_datadir}/appdata/
appstream-util validate-relax --nonet %{buildroot}/%{_datadir}/appdata/spotify.appdata.xml
%endif

%post
%if 0%{?fedora} == 23 || 0%{?rhel} == 7
%{_bindir}/update-mime-database %{_datadir}/mime &> /dev/null || :
%endif
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
%if 0%{?fedora} == 24 || 0%{?fedora} == 23 || 0%{?rhel} == 7
/usr/bin/update-desktop-database &> /dev/null || :
%endif
%firewalld_reload

%postun
%if 0%{?fedora} == 23 || 0%{?rhel} == 7
%{_bindir}/update-mime-database %{_datadir}/mime &> /dev/null || :
%endif
%if 0%{?fedora} == 24 || 0%{?fedora} == 23 || 0%{?rhel} == 7
/usr/bin/update-desktop-database &> /dev/null || :
%endif
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    %{_bindir}/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi

%posttrans
%if 0%{?fedora} == 23 || 0%{?rhel} == 7
%{_bindir}/update-mime-database %{?fedora:-n} %{_datadir}/mime &> /dev/null || :
%endif
%{_bindir}/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%files
%doc README.Fedora
%{_bindir}/spotify
%{_datadir}/applications/spotify.desktop
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%if 0%{?fedora} >= 25
%{_datadir}/appdata/spotify.appdata.xml
%endif
%{_libdir}/%{name}
%{_prefix}/lib/firewalld/services/spotify.xml

%changelog
* Mon Mar 06 2017 Simone Caronni <negativo17@gmail.com> - 1:1.0-15
- Remove all icons from the program data folder except the 512x512 one that is
  used as a resource by the client.

* Mon Mar 06 2017 Simone Caronni <negativo17@gmail.com> - 1:1.0-13
- Update firewalld rules for allowing syncing of local files across devices on
  the same Wi-Fi network.

* Wed Mar 01 2017 Simone Caronni <negativo17@gmail.com> - 1:1.0-12
- Use a wrapper script to remove RUNPATH and make the client find all its
  libraries in a private location.
- Require compatiblity packages of the same architecture.

* Fri Feb 24 2017 Simone Caronni <negativo17@gmail.com> - 1:1.0-11
- Update to newer builds of 1.0.49.125.g72ee7853.

* Tue Feb 21 2017 Simone Caronni <negativo17@gmail.com> - 1:1.0-10
- Require custom built FFMpeg 0.10.x without external dependencies to support
  playing / syncing of local files.

* Sun Feb 12 2017 Simone Caronni <negativo17@gmail.com> - 1:1.0-9
- Move OpenSSL 1.0.0t compatibility libraries to the Spotify folder. Having them
  installed on the system breaks some Steam games which are built agains the
  Steam Runtime (mostly Feral Interactive games).

* Sun Feb 12 2017 Simone Caronni <negativo17@gmail.com> - 1:1.0-8
- Update to 1.0.49.125.g72ee7853.

* Thu Feb 02 2017 Simone Caronni <negativo17@gmail.com> - 1:1.0-7
- Update to 1.0.48.103.g15edf1ec.

* Sat Jan 14 2017 Andrea Giardini <contact@andreagiardini.com> - 1:1.0-6
- Update to 1.0.47.13.gd8e05b1f.

* Wed Dec 21 2016 Simone Caronni <negativo17@gmail.com> - 1:1.0-5
- Update to 1.0.45.186.g3b5036d6.

* Thu Dec 15 2016 Simone Caronni <negativo17@gmail.com> - 1:1.0-4
- Update to 1.0.45.182.gbbd5909f.

* Wed Dec 14 2016 Simone Caronni <negativo17@gmail.com> - 1:1.0-3
- Add firewalld macro if not defined.

* Wed Dec 14 2016 Simone Caronni <negativo17@gmail.com> - 1:1.0-2
- Update to 1.0.44.100.ga60c0ce1.

* Tue Dec 13 2016 Simone Caronni <negativo17@gmail.com> - 1:1.0-1
- Add spotify connect firewall rules.
- Switch to a base version number with incremental releases to solve the problem
  of 32 and 64 bit client versions not being in sync.

* Thu Dec 08 2016 Simone Caronni <negativo17@gmail.com> - 1.0.43.125.g376063c5-1
- Update to 1.0.43.125.g376063c5 (x86_64 only).
- Suggests compat-ffmpeg-libs (2.8.x) instead of requiring ffmpeg-libs (3.2.x).

* Tue Nov 29 2016 Simone Caronni <negativo17@gmail.com> - 1.0.43.123.g80176796-1
- Update to 1.0.43.123.g80176796.

* Wed Nov 09 2016 Simone Caronni <negativo17@gmail.com> - 1.0.42.151.g19de0aa6-1
- Update to 1.0.42.151.g19de0aa6.

* Thu Nov 03 2016 Simone Caronni <negativo17@gmail.com> - 1.0.42.145.g7a5a182e-1
- Update to 1.0.42.145.g7a5a182e.

* Wed Oct 12 2016 Simone Caronni <negativo17@gmail.com> - 1.0.38.171.g5e1cd7b2-4
- No longer requires compatibility libgcrypt package.
- Move SSL libraries in compatibility package.

* Sat Sep 24 2016 Simone Caronni <negativo17@gmail.com> - 1.0.38.171.g5e1cd7b2-3
- Do not run update-mime-database on Fedora 24+.

* Fri Sep 23 2016 Simone Caronni <negativo17@gmail.com> - 1.0.38.171.g5e1cd7b2-2
- Do not run update-desktop-database on Fedora 25+.
- Add AppStream metadata for Gnome Software.

* Fri Sep 23 2016 Simone Caronni <negativo17@gmail.com> - 1.0.38.171.g5e1cd7b2-1
- Update to 1.0.38.171.g5e1cd7b2.

* Tue Sep 06 2016 Simone Caronni <negativo17@gmail.com> - 1.0.37.152.gc83ea995-1
- Update to 1.0.37.152.gc83ea995.

* Wed Aug 17 2016 Simone Caronni <negativo17@gmail.com> - 1.0.36.120.g536a862f-1
- Update to 1.0.36.120.g536a862f.

* Wed Aug 03 2016 Simone Caronni <negativo17@gmail.com> - 1.0.33.106.g60b5d1f0-1
- Update to 1.0.33.106.g60b5d1f0.

* Fri Jul 01 2016 Simone Caronni <negativo17@gmail.com> - 1.0.32.96.g3c8a06e6-1
- Update to 1.0.32.96.g3c8a06e6.

* Wed Jun 22 2016 Anass Ahmed <anass.1430@gmail.com> - 1.0.32.94.g8a839395-1
- Update to 1.0.32.94.g8a839395.
- Update OpenSSL libraries.

* Thu Jun 09 2016 Simone Caronni <negativo17@gmail.com> - 1.0.31.56.g526cfefe-1
- Update to 1.0.31.56.g526cfefe.

* Mon May 23 2016 Simone Caronni <negativo17@gmail.com> - 1.0.29.92.g67727800-1
- Update to 1.0.29.92.g67727800.

* Fri Apr 29 2016 Simone Caronni <negativo17@gmail.com> - 1.0.28.89.gf959d4ce-1
- Update to 1.0.28.89.gf959d4ce.

* Thu Apr 21 2016 Simone Caronni <negativo17@gmail.com> - 1.0.27-1
- Starting from 1.0.27.x clients versions are misaligned again between 32 and 64
  bit. Just the base version.

* Fri Apr 01 2016 Simone Caronni <negativo17@gmail.com> - 1.0.26.125.g64dc8bc6-1
- Update to 1.0.26.125.g64dc8bc6
- Update OpenSSL libraries.

* Wed Mar 16 2016 Simone Caronni <negativo17@gmail.com> - 1.0.25.127.g58007b4c-1
- Update to 1.0.25.127.g58007b4c.

* Fri Mar 04 2016 Simone Caronni <negativo17@gmail.com> - 1.0.24.104.g92a22684-2
- Update to 1.0.24.104.g92a22684.

* Tue Feb 23 2016 Simone Caronni <negativo17@gmail.com> - 1.0.23.93.gd6cfae15-1
- Update to 1.0.23.93.gd6cfae15.
- Update library filters.

* Tue Dec 01 2015 Simone Caronni <negativo17@gmail.com> - 1.0.19.106.gb8a7150f-1
- Update to 1.0.19.106.gb8a7150f.

* Tue Nov 10 2015 Simone Caronni <negativo17@gmail.com> - 1.0.17.75.g8f111100-2
- Fix 32 bit build.

* Thu Oct 29 2015 Simone Caronni <negativo17@gmail.com> - 1.0.17.75.g8f111100-1
- Update to 1.0.17.75.g8f111100.

* Wed Oct 21 2015 Simone Caronni <negativo17@gmail.com> - 1.0.16.104.g3b776c9e-1
- Update to 1.0.16.104.g3b776c9e.
- Re-enable 32 bit package.

* Tue Oct 13 2015 Simone Caronni <negativo17@gmail.com> - 1.0.15.137.gbdf68615-1
- Update to version 1.0.15.137.gbdf68615.

* Fri Sep 18 2015 Simone Caronni <negativo17@gmail.com> - 1.0.14.124.g4dfabc51-1
- Update to 1.0.14.124.g4dfabc51.

* Tue Sep 08 2015 Simone Caronni <negativo17@gmail.com> - 1.0.13.112.g539ef41b-1
- Update to 1.0.13.112.g539ef41b.
- Update Ubuntu SSL libraries.

* Tue Sep 01 2015 Simone Caronni <negativo17@gmail.com> - 1.0.13.111.g6bd0deca-1
- Update to 1.0.13.111.g6bd0deca.

* Fri Jul 31 2015 Simone Caronni <negativo17@gmail.com> - 1.0.11.131.gf4d47cb0-1
- Update to 1.0.11.131.gf4d47cb0.

* Mon Jul 13 2015 Simone Caronni <negativo17@gmail.com> - 1.0.9.133.gcedaee38-1
- Update to version 1.0.9.133.gcedaee38.
- Filter out libcurl.so.4(CURL_OPENSSL_3)(64bit) from requirements.

* Mon Jun 08 2015 Simone Caronni <negativo17@gmail.com> - 1.0.7.153.gb9e8174a-1
- Update to 1.0.7.153.gb9e8174a.
- Require new ffmpeg-libs, removed compat-ffmpeg dependancy.
- Merge data subpackage in main package.
- Add MimeType registration.
- Remove License file, there is no license file provided anymore.
- Filter out also ffmpegsumo/cef from package.

* Wed Jun 03 2015 Simone Caronni <negativo17@gmail.com> - 0.9.17.8.gd06432d.31-3
- Add dbus-x11 dependency.

* Tue May 19 2015 Simone Caronni <negativo17@gmail.com> - 0.9.17.8.gd06432d.31-2
- Require ffmpeg-compat also on el7.

* Tue May 12 2015 Simone Caronni <negativo17@gmail.com> - 0.9.17.8.gd06432d.31-1
- Update to version 0.9.17.8.gd06432d.31.
- Add license macro.

* Wed Apr 01 2015 Simone Caronni <negativo17@gmail.com> - 0.9.17.1.g9b85d43.7-4
- Use Debian packages also for openssl libraries.

* Wed Apr 01 2015 Simone Caronni <negativo17@gmail.com> - 0.9.17.1.g9b85d43.7-3
- Use original debian package as source, the size of the package is now the same
  size of the resulting tarball.
- Remove compat-libgcrypt explicit requirement and requirement filter, so the
  library is pulled in automatically.
- Format SPEC file.

* Wed Apr 01 2015 Simone Caronni <negativo17@gmail.com> - 0.9.17.1.g9b85d43.7-2
- Require compat-libgcrypt and get rid of some hacks.

* Wed Apr 01 2015 Simone Caronni <negativo17@gmail.com> - 0.9.17.1.g9b85d43.7-1
- Update to latest 0.9.17.1.g9b85d43.7.

* Tue Dec 16 2014 Simone Caronni <negativo17@gmail.com> - 0.9.11.27.g2b1a638.81-5
- Add support for playing local files on Fedora.

* Wed Nov 26 2014 Simone Caronni <negativo17@gmail.com> - 0.9.11.27.g2b1a638.81-4
- Fix libgcrypto error on Fedora 21+.

* Tue Sep 30 2014 Simone Caronni <negativo17@gmail.com> - 0.9.11.27.g2b1a638.81-3
- Use 64 bit Debian libraries for real.

* Mon Sep 29 2014 Simone Caronni <negativo17@gmail.com> - 0.9.11.27.g2b1a638.81-2
- Add compatibility libgcrypt for Fedora 21+.
- Drop entirely i386 support, no longer updated upstream.

* Sat Aug 23 2014 Simone Caronni <negativo17@gmail.com> - 0.9.11.27.g2b1a638.81-1
- Update to 0.9.11.27.g2b1a638.81.

* Thu Jul 03 2014 Simone Caronni <negativo17@gmail.com> - 0.9.11.26.g995ec04.78-1
- Update to 0.9.11.26.g995ec04.78.

* Mon Jun 23 2014 Simone Caronni <negativo17@gmail.com> - 0.9.10.17.g4129e1c.78-2
- Updated Debian OpenSSL libraries.
- Removed extra nspr, nss, nss-utils symlink requirements, adjusted RPM filters.

* Thu Jun 19 2014 Simone Caronni <negativo17@gmail.com> - 0.9.10.17.g4129e1c.78-1
- Update to 0.9.10.17.g4129e1c.78.

* Thu Dec 19 2013 Simone Caronni <negativo17@gmail.com> - 0.9.4.183.g644e24e.428-2
- Update library filters to latest package guidelines.
- Regenerate tarballs to reduce source package size by 40% (so my hosting
  provider does not cut me off during file transfer..).
  
* Wed Nov 20 2013 Simone Caronni <negativo17@gmail.com> - 0.9.4.183.g644e24e.428-1
- First build.
