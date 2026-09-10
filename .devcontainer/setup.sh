#!/usr/bin/env bash
set -euo pipefail

pip install --user -r requirements-dev.txt

# kubectl — official install method from kubernetes.io, not a third-party
# devcontainer feature (the kubectl-helm-minikube feature has a known,
# unresolved checksum-validation bug: devcontainers/features#523).
KUBECTL_VERSION="$(curl -L -s https://dl.k8s.io/release/stable.txt)"
curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl

# minikube — official install method from minikube.sigs.k8s.io
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube /usr/local/bin/minikube
rm minikube

echo "kubectl and minikube installed:"
kubectl version --client
minikube version
