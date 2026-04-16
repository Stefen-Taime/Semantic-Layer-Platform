#!/usr/bin/env bash

set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  git \
  gnupg \
  lsb-release \
  make \
  unzip \
  wget

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${VERSION_CODENAME}") stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y --no-install-recommends \
  containerd.io \
  docker-buildx-plugin \
  docker-ce \
  docker-ce-cli \
  docker-compose-plugin

install -m 0755 -d /usr/local/lib/docker/cli-plugins
if [ -x /usr/libexec/docker/cli-plugins/docker-compose ]; then
  ln -sf /usr/libexec/docker/cli-plugins/docker-compose /usr/local/lib/docker/cli-plugins/docker-compose
fi

systemctl enable docker
systemctl start docker

if id -u ubuntu >/dev/null 2>&1; then
  usermod -aG docker ubuntu
fi

cat >/etc/motd <<'EOF'
MetricForge NYC demo VM is ready.

Next steps:
1. SSH into the VM
2. Clone the repository
3. Run:
   ./scripts/run_demo_stack.sh
EOF
