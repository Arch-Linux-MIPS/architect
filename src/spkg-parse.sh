#!/bin/sh

set -eu
set -o pipefail

tmpDir="`mktemp -d`"

cleanup()
{
    rm -rf "${tmpDir}"
    trap - EXIT INT TERM
}
trap cleanup EXIT INT TERM

die()
{
    echo "$@" >&2
    exit 1
}

pkgBuild="$1"
[ -e "${pkgBuild}" ] || die "PKGBUILD not found"

outputName=`mktemp --tmpdir=/usr/bin -u XXXXXXXX`
outputName=`basename ${outputName}`

writeOutput=`mktemp --tmpdir=/usr/bin -u XXXXXXXX`
writeOutput=`basename ${writeOutput}`

touch ${tmpDir}/output
mkdir -p ${tmpDir}/root/pkg/{src,pkg}

cat >${tmpDir}/__write_output <<EOF
#!/bin/sh
cat <&0 >>/usr/bin/${outputName}
EOF
chmod +x ${tmpDir}/__write_output

cp "${pkgBuild}" ${tmpDir}/root/pkg/PKGBUILD

PATH="/usr/bin" `which proot` \
    -r "${tmpDir}/root" -w /pkg \
    -b /usr -b /etc -b /bin -b /lib -b /lib64 \
    -b /usr/bin/true:/usr/bin/cp \
    -b /usr/bin/true:/usr/bin/install \
    -b /usr/bin/true:/usr/bin/mv \
    -b "${tmpDir}/output:/usr/bin/${outputName}" \
    -b "${tmpDir}/__write_output:/usr/bin/${writeOutput}" \
    bash --restricted --noprofile --norc >/dev/null 2>&1 <<EOF
export CARCH="mips32r2el"
export CHOST="mipsel-unknown-linux-gnu"

srcdir=\${PWD}/src
depends=()
makedepends=()
checkdepends=()
provides=()
arch=()

source PKGBUILD

set -e
set -o pipefail

escape_json()
{
  echo -n "\$@" | \
    sed 's|\\\\|\\\\\\\\|g' | \
    sed 's|\\"|\\\\"|g' | \
    sed 's|\\[\\b\\]|\\\\b|g' | \
    sed 's|\\f|\\\\f|g' | \
    tr '\\n' ' ' | \
    tr '\\r' ' ' | \
    sed 's|\\t|\\\\t|g'
}

echo "{" | ${writeOutput}
[ -z "\${pkgbase}" ] || echo "  \"base\": \"\${pkgbase}\"," | ${writeOutput}
echo "  \"ver\": \"\${pkgver}\"," | ${writeOutput}
echo "  \"rel\": \"\${pkgrel}\"," | ${writeOutput}
[ -z "\${epoch}" ] || echo "  \"epoch\": \"\${epoch}\"," | ${writeOutput}

__license=\`escape_json "\${license}"\`
[ -z "\${__license}" ] || echo "  \"license\": \"\${__license}\"," | ${writeOutput}

__url=\`escape_json "\${url}"\`
[ -z "\${__url}" ] || echo "  \"url\": \"\${__url}\"," | ${writeOutput}

makedepends=(\$(echo \${depends[@]} \${makedepends[@]}))
if [ \${#makedepends[@]} -gt 0 ]; then
  echo "  \"makedepends\": [" | ${writeOutput}
  i=0
  for __dep in \${makedepends[@]}; do
    __dep=\`escape_json "\${__dep}"\`
    __comma=","
    [ \$i -ne \$((\${#makedepends[@]} - 1)) ] || __comma=""
    echo "    \"\${__dep}\"\${__comma}" | ${writeOutput}
    i=\$((\$i + 1))
  done
  echo "  ]," | ${writeOutput}
fi

if [ \${#checkdepends[@]} -gt 0 ]; then
  # work around things like ('depa ''depb' 'depc') where length=2
  checkdepends=(\$(echo \${checkdepends[@]}))
  echo "  \"checkdepends\": [" | ${writeOutput}
  i=0
  for __dep in \${checkdepends[@]}; do
    __dep=\`escape_json "\${__dep}"\`
    __comma=","
    [ \$i -ne \$((\${#checkdepends[@]} - 1)) ] || __comma=""
    echo "    \"\${__dep}\"\${__comma}" | ${writeOutput}
    i=\$((\$i + 1))
  done
  echo "  ]," | ${writeOutput}
fi

#set +e
#build
#set -e

echo "  \"packages\": [" | ${writeOutput}

for __pkg in \${pkgname[@]}; do
  echo "    {" | ${writeOutput}
  __name=\`escape_json "\${__pkg}"\`
  echo "      \"name\": \"\${__name}\"," | ${writeOutput}

  pkgdir=\${PWD}/pkg
  set +e
  package_\${__pkg}
  set -e

  if [ \${#arch[@]} -gt 0 ]; then
    # work around things like ('depa ''depb' 'depc') where length=2
    arch=(\$(echo \${arch[@]}))
    echo "      \"arch\": [" | ${writeOutput}
    i=0
    for __arch in \${arch[@]}; do
      __arch=\`escape_json "\${__arch}"\`
      __comma=","
      [ \$i -ne \$((\${#arch[@]} - 1)) ] || __comma=""
      echo "        \"\${__arch}\"\${__comma}" | ${writeOutput}
      i=\$((\$i + 1))
    done
    echo "      ]," | ${writeOutput}
  fi

  if [ \${#depends[@]} -gt 0 ]; then
    # work around things like ('depa ''depb' 'depc') where length=2
    depends=(\$(echo \${depends[@]}))
    echo "      \"depends\": [" | ${writeOutput}
    i=0
    for __dep in \${depends[@]}; do
      __dep=\`escape_json "\${__dep}"\`
      __comma=","
      [ \$i -ne \$((\${#depends[@]} - 1)) ] || __comma=""
      echo "        \"\${__dep}\"\${__comma}" | ${writeOutput}
      i=\$((\$i + 1))
    done
    echo "      ]," | ${writeOutput}
  fi

  if [ \${#optdepends[@]} -gt 0 ]; then
    echo "      \"optdepends\": [" | ${writeOutput}
    i=0
    for __dep in "\${optdepends[@]}"; do
      __dep=\`escape_json "\${__dep}"\`
      __comma=","
      [ \$i -ne \$((\${#optdepends[@]} - 1)) ] || __comma=""
      echo "        \"\${__dep}\"\${__comma}" | ${writeOutput}
      i=\$((\$i + 1))
    done
    echo "      ]," | ${writeOutput}
  fi

  if [ \${#provides[@]} -gt 0 ]; then
    # work around things like ('depa ''depb' 'depc') where length=2
    provides=(\$(echo \${provides[@]}))
    echo "      \"provides\": [" | ${writeOutput}
    i=0
    for __dep in \${provides[@]}; do
      __dep=\`escape_json "\${__dep}"\`
      __comma=","
      [ \$i -ne \$((\${#provides[@]} - 1)) ] || __comma=""
      echo "        \"\${__dep}\"\${__comma}" | ${writeOutput}
      i=\$((\$i + 1))
    done
    echo "      ]," | ${writeOutput}
  fi

  if [ \${#conflicts[@]} -gt 0 ]; then
    # work around things like ('depa ''depb' 'depc') where length=2
    conflicts=(\$(echo \${conflicts[@]}))
    echo "      \"conflicts\": [" | ${writeOutput}
    i=0
    for __dep in \${conflicts[@]}; do
      __dep=\`escape_json "\${__dep}"\`
      __comma=","
      [ \$i -ne \$((\${#conflicts[@]} - 1)) ] || __comma=""
      echo "        \"\${__dep}\"\${__comma}" | ${writeOutput}
      i=\$((\$i + 1))
    done
    echo "      ]," | ${writeOutput}
  fi

  if [ \${#replaces[@]} -gt 0 ]; then
    # work around things like ('depa ''depb' 'depc') where length=2
    replaces=(\$(echo \${replaces[@]}))
    echo "      \"replaces\": [" | ${writeOutput}
    i=0
    for __dep in \${replaces[@]}; do
      __dep=\`escape_json "\${__dep}"\`
      __comma=","
      [ \$i -ne \$((\${#replaces[@]} - 1)) ] || __comma=""
      echo "        \"\${__dep}\"\${__comma}" | ${writeOutput}
      i=\$((\$i + 1))
    done
    echo "      ]," | ${writeOutput}
  fi

  if [ \${#groups[@]} -gt 0 ]; then
    # work around things like ('depa ''depb' 'depc') where length=2
    groups=(\$(echo \${groups[@]}))
    echo "      \"groups\": [" | ${writeOutput}
    i=0
    for __dep in \${groups[@]}; do
      __dep=\`escape_json "\${__dep}"\`
      __comma=","
      [ \$i -ne \$((\${#groups[@]} - 1)) ] || __comma=""
      echo "        \"\${__dep}\"\${__comma}" | ${writeOutput}
      i=\$((\$i + 1))
    done
    echo "      ]," | ${writeOutput}
  fi

  __desc=\`escape_json "\${pkgdesc}"\`
  echo "      \"desc\": \"\${__desc}\"" | ${writeOutput}

  __comma=","
  [ "\${__pkg}" != "\${pkgname[\${#pkgname[@]} - 1]}" ] || __comma=""
  echo "    }\${__comma}" | ${writeOutput}

  conflicts=()
  depends=()
  optdepends=()
  provides=()
  replaces=()
  pkgdesc=""
done

echo "  ]" | ${writeOutput}
echo "}" | ${writeOutput}

while kill -9 %% 2>/dev/null; do jobs > /dev/null; done

EOF

cat ${tmpDir}/output
