#!/bin/sh

if [[ -z "$1" ]]; then
    echo "Provide version" 1>&2
    exit 1
fi


VERSION=$1
NAME=spotify-client
REPO=https://repository-origin.spotify.com/pool/non-free/s/spotify-client/
DEB=spotify-client_${VERSION}_amd64.deb

rm -fr ${NAME}*.deb ${NAME}.tar.xz temp

rpmdev-bumpspec -D -c "Update to ${VERSION}." -n ${VERSION} ${NAME}.spec

mkdir temp
pushd temp
    wget -c ${REPO}/${DEB}
    ar x ${DEB}
    tar -xzf data.tar.gz
    mv usr/share/spotify ../${NAME}-${VERSION}
popd
rm -fr temp
tar -cJf ${NAME}-${VERSION}.tar.xz --remove-files ${NAME}-${VERSION}

git commit -a -m "Update to ${VERSION}"
