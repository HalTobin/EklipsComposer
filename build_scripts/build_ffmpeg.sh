#!/bin/sh
# Build a decode-only, LGPL ffmpeg (~8–15 MB) for bundling.
# imageio-ffmpeg ships a ~47 MB kitchen-sink binary (x264/x265 encoders, etc.).
set -eu

if [ "$(uname -s)" != "Darwin" ]; then
  echo "build_ffmpeg.sh currently supports macOS only." >&2
  exit 1
fi

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
FFMPEG_VERSION="${FFMPEG_VERSION:-7.1.1}"
OUT_DIR="$ROOT/third_party/ffmpeg"
OUT_BIN="$OUT_DIR/ffmpeg"
STAMP="$OUT_DIR/.build-id"
BUILD_ID="ffmpeg-${FFMPEG_VERSION}-decode-videotoolbox-v2"

if [ -x "$OUT_BIN" ] && [ -f "$STAMP" ] && [ "$(cat "$STAMP")" = "$BUILD_ID" ]; then
  echo "Using cached decode-only ffmpeg ($OUT_BIN)"
  ls -lh "$OUT_BIN"
  exit 0
fi

WORK="${FFMPEG_WORK_DIR:-$ROOT/output/ffmpeg-build}"
SRC="$WORK/FFmpeg-n${FFMPEG_VERSION}"
TAR="$WORK/ffmpeg-${FFMPEG_VERSION}.tar.gz"
URL="https://github.com/FFmpeg/FFmpeg/archive/refs/tags/n${FFMPEG_VERSION}.tar.gz"

echo "Building decode-only ffmpeg ${FFMPEG_VERSION}…"
mkdir -p "$WORK" "$OUT_DIR"

if [ ! -d "$SRC" ]; then
  if [ ! -f "$TAR" ]; then
    echo "Downloading $URL"
    curl -L --fail --retry 3 -o "$TAR" "$URL"
  fi
  tar -xzf "$TAR" -C "$WORK"
fi

cd "$SRC"
make distclean >/dev/null 2>&1 || true

# Native H.264/HEVC/ProRes/etc. decoders only — no libx264/x265/libaom.
# VideoToolbox hwaccel stays available on macOS without extra dylibs.
./configure \
  --prefix="$WORK/prefix" \
  --disable-all \
  --disable-autodetect \
  --disable-debug \
  --disable-doc \
  --disable-htmlpages \
  --disable-manpages \
  --disable-podpages \
  --disable-txtpages \
  --disable-network \
  --enable-small \
  --enable-lto \
  --enable-ffmpeg \
  --enable-avcodec \
  --enable-avformat \
  --enable-avutil \
  --enable-avfilter \
  --enable-swscale \
  --enable-swresample \
  --enable-protocol=file \
  --enable-protocol=pipe \
  --enable-demuxer=mov \
  --enable-demuxer=matroska \
  --enable-demuxer=avi \
  --enable-demuxer=mpegts \
  --enable-demuxer=mpegps \
  --enable-demuxer=flv \
  --enable-demuxer=image2 \
  --enable-decoder=h264 \
  --enable-decoder=hevc \
  --enable-decoder=mpeg4 \
  --enable-decoder=mpeg2video \
  --enable-decoder=mjpeg \
  --enable-decoder=png \
  --enable-decoder=prores \
  --enable-decoder=vp8 \
  --enable-decoder=vp9 \
  --enable-decoder=rawvideo \
  --enable-parser=h264 \
  --enable-parser=hevc \
  --enable-parser=mpeg4video \
  --enable-parser=mpegvideo \
  --enable-parser=mjpeg \
  --enable-parser=vp8 \
  --enable-parser=vp9 \
  --enable-bsf=h264_mp4toannexb \
  --enable-bsf=hevc_mp4toannexb \
  --enable-encoder=rawvideo \
  --enable-muxer=rawvideo \
  --enable-muxer=null \
  --enable-filter=scale \
  --enable-filter=null \
  --enable-filter=format \
  --enable-filter=crop \
  --enable-filter=hflip \
  --enable-filter=vflip \
  --enable-filter=rotate \
  --enable-filter=transpose \
  --enable-filter=trim \
  --enable-filter=aformat \
  --enable-filter=anull \
  --enable-filter=atrim \
  --enable-zlib \
  --enable-videotoolbox \
  --enable-hwaccel=h264_videotoolbox \
  --enable-hwaccel=hevc_videotoolbox \
  --enable-hwaccel=mpeg4_videotoolbox \
  --enable-hwaccel=prores_videotoolbox \
  --extra-cflags="-Os" \
  --extra-ldflags="-Wl,-dead_strip"

JOBS=$(sysctl -n hw.ncpu 2>/dev/null || echo 4)
make -j"$JOBS"
make install

cp "$WORK/prefix/bin/ffmpeg" "$OUT_BIN"
chmod +x "$OUT_BIN"
strip -x "$OUT_BIN" 2>/dev/null || strip "$OUT_BIN" || true
printf '%s\n' "$BUILD_ID" > "$STAMP"

echo "Built $OUT_BIN"
ls -lh "$OUT_BIN"
file "$OUT_BIN"
