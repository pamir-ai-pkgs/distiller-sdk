default:
    @just --list

build arch="arm64": prepare
    #!/usr/bin/env bash
    set -e
    export DEB_BUILD_OPTIONS="parallel=$(nproc)"
    debuild -us -uc -b -a{{ arch }} -d --lintian-opts --profile=debian
    mkdir -p dist && mv ../*.deb dist/ 2>/dev/null || true
    rm -f ../*.{dsc,tar.*,changes,buildinfo,build}

changelog:
    gbp dch -R --ignore-branch --release

clean:
    rm -rf debian/.debhelper debian/files debian/*.log debian/*.substvars debian/distiller-sdk debian/debhelper-build-stamp dist
    rm -f ../*.deb ../*.dsc ../*.tar.* ../*.changes ../*.buildinfo ../*.build
    rm -rf build *.egg-info .venv
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    rm -rf src/distiller_sdk/hardware/eink/lib/target

# Python project recipes
setup:
    uv sync

lint:
    uv run ruff check .
    uv run ruff format --check .
    uv run mypy --ignore-missing-imports src/

fix:
    uv run ruff check --fix .
    uv run ruff format .

# SDK-specific recipes
prepare whisper="":
    ./build.sh {{ whisper }}
