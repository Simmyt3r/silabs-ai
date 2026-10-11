#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/Simmyt3r/silabs-ai}"
RUNNER_TOKEN="${RUNNER_TOKEN:-}"
RUNNER_NAME="${RUNNER_NAME:-silabs-gpu-$(hostname)}"
RUNNER_LABELS="${RUNNER_LABELS:-gpu,silabs-ai}"
RUNNER_DIR="${RUNNER_DIR:-/opt/actions-runner}"

if [[ -z "${RUNNER_TOKEN}" ]]; then
  cat >&2 <<'EOF'
RUNNER_TOKEN is required.

Get a fresh token from:
GitHub repo -> Settings -> Actions -> Runners -> New self-hosted runner

Then run:
  export RUNNER_TOKEN='paste-token-here'
  bash scripts/bootstrap_gpu_runner.sh
EOF
  exit 2
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "ERROR: nvidia-smi is not available. Start this on an NVIDIA CUDA GPU VM." >&2
  exit 3
fi

echo "=== NVIDIA GPU ==="
nvidia-smi

if command -v apt-get >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y curl ca-certificates tar gzip python3
fi

mkdir -p "${RUNNER_DIR}"
cd "${RUNNER_DIR}"

if [[ ! -x ./config.sh ]]; then
  echo "Downloading latest GitHub Actions runner..."
  RUNNER_TAG="$(curl -fsSL https://api.github.com/repos/actions/runner/releases/latest | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"])')"
  RUNNER_VERSION="${RUNNER_TAG#v}"
  ARCH="$(uname -m)"
  case "${ARCH}" in
    x86_64|amd64) RUNNER_ARCH="x64" ;;
    aarch64|arm64) RUNNER_ARCH="arm64" ;;
    *)
      echo "Unsupported architecture: ${ARCH}" >&2
      exit 4
      ;;
  esac

  ARCHIVE="actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"
  curl -fL     "https://github.com/actions/runner/releases/download/${RUNNER_TAG}/${ARCHIVE}"     -o "${ARCHIVE}"
  tar xzf "${ARCHIVE}"
  rm -f "${ARCHIVE}"

  if [[ -x ./bin/installdependencies.sh ]]; then
    ./bin/installdependencies.sh || true
  fi
fi

export RUNNER_ALLOW_RUNASROOT=1

echo "Registering one-job ephemeral GPU runner..."
./config.sh   --url "${REPO_URL}"   --token "${RUNNER_TOKEN}"   --name "${RUNNER_NAME}"   --labels "${RUNNER_LABELS}"   --unattended   --ephemeral   --replace

unset RUNNER_TOKEN

cat <<EOF

Runner registered:
  repository: ${REPO_URL}
  name:       ${RUNNER_NAME}
  labels:     self-hosted, linux, $(uname -m), ${RUNNER_LABELS}

This runner is ephemeral. It will accept one GitHub Actions job and then
de-register itself. Keep this terminal open until the job finishes.

EOF

exec ./run.sh
