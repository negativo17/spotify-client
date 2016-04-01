%global         debug_package %{nil}
%global         __strip /bin/true

# Remove bundled libraries from requirements/provides
%global         __requires_exclude ^(libcef\\.so.*|libffmpegsumo\\.so.*|libcrypto\\.so\\..*|libssl\\.so\\..*|libcurl\\.so\\..*)$
%global         __provides_exclude ^(lib.*\\.so.*)$

Name:           spotify-client
Summary:        Spotify music player native client
Version:        1.0.25.127.g58007b4c
Release:        1%{?dist}
License:        https://www.spotify.com/legal/end-user-agreement
URL:            http://www.spotify.com/
ExclusiveArch:  x86_64 %{ix86}

Source0:        http://repository.spotify.com/pool/non-free/s/%{name}/%{name}_%{version}-22_amd64.deb
Source1:        http://repository.spotify.com/pool/non-free/s/%{name}/%{name}_%{version}-6_i386.deb
# Debian libraries, required by the binaries. Ugh.
Source2:        http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.0.0_1.0.2f-2ubuntu1_amd64.deb
Source3:        http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.0.0_1.0.2f-2ubuntu1_i386.deb

Provides:       spotify = %{version}-%{release}

# Libraries linked in the package (no auto require)
Provides:       bundled(libssl-Debian) = 1.0.2f

# Obsoletes old data subpackage
Provides:       spotify-client-data = %{version}-%{release}
Obsoletes:      spotify-client-data < %{version}-%{release}

BuildRequires:  desktop-file-utils
#BuildRequires:  chrpath
Requires:       ffmpeg-libs
Requires:       hicolor-icon-theme

%if 0%{?fedora} || 0%{?rhel} >= 8
Requires:       compat-libgcrypt
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
ar x %{SOURCE2}
tar -xJf data.tar.xz
%endif

%ifarch %{ix86}
ar x %{SOURCE1}
tar -xzf data.tar.gz
ar x %{SOURCE3}
tar -xJf data.tar.xz
%endif

# chrpath -d spotify Data/SpotifyHelper

%build
# Nothing to build

%install
mkdir -p %{buildroot}%{_libdir}/%{name}
cp -frp .%{_datadir}/spotify/* %{buildroot}%{_libdir}/%{name}
rm -fr %{buildroot}%{_libdir}/%{name}/*.{sh,txt,desktop}
chmod +x %{buildroot}%{_libdir}/%{name}/*.so

mkdir -p %{buildroot}%{_bindir}
ln -sf %{_libdir}/%{name}/spotify %{buildroot}%{_bindir}/spotify

install -m 0644 -D -p .%{_datadir}/spotify/spotify.desktop \
    %{buildroot}%{_datadir}/applications/spotify.desktop

# Also leave icons along main executable as they are needed by the client. We
# can't just symlink them or RPM will complain with the broken links.
for size in 16 22 24 32 48 64 128 256 512; do
    install -p -D -m 644 .%{_datadir}/spotify/icons/spotify-linux-${size}.png \
        %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/%{name}.png
done

desktop-file-validate %{buildroot}%{_datadir}/applications/spotify.desktop

# Extra libraries: the binaries expects the libraries along with the main
# "spotify" binary or in the "Data" folder. "SpotifyHelper" expects them only in
# the "Data" folder. So put everything in the "Data" folder.
cp -f ./lib/*-linux-gnu/lib*.so* %{buildroot}%{_libdir}/%{name}/
chmod 0755 %{buildroot}%{_libdir}/%{name}/lib*.so*

%post
%{_bindir}/update-mime-database %{_datadir}/mime &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
%{_bindir}/update-desktop-database &> /dev/null || :

%postun
%{_bindir}/update-mime-database %{_datadir}/mime &> /dev/null || :
%{_bindir}/update-desktop-database &> /dev/null || :
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    %{_bindir}/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi

%posttrans
%{_bindir}/update-mime-database %{?fedora:-n} %{_datadir}/mime &> /dev/null || :
%{_bindir}/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%files
%doc .%{_datadir}/spotify/README.txt
%{_bindir}/spotify
%{_libdir}/%{name}
%{_datadir}/applications/spotify.desktop
%{_datadir}/icons/hicolor/*/apps/%{name}.png

%changelog
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
