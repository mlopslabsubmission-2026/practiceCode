# Cloud Demo — Fund Transfer

A **Fund Transfer** service that orchestrates three
atomic services — **Fee**, **Account**, **Journal** — over HTTP. Same code
runs three ways: directly, in Docker Compose, and in Kubernetes.

```
                 POST /transfer
                       |
                       v
           +-----------------------+
           |  fund-transfer-service |
           +-----------------------+
             |         |         |
      GET /fee   POST /debit  POST /journal
             |    POST /credit      |
             v         v            v
      fee-service  account-service  journal-service
```

## Before class: open this in a Codespace

**[codespaces.new/mlopslabsubmission-2026/practiceCode](https://codespaces.new/mlopslabsubmission-2026/practiceCode)**
— one click, while signed into GitHub, provisions your own personal
Codespace from this repo. No local install needed — Docker and
`kubectl`/`minikube` are already in the container image. Open this a few
minutes before the session starts so the environment is ready when we
begin.

## Running order — 50 minutes

| Time | Segment |
|---|---|
| 10 min | Part A — Docker & Compose |
| 25 min | Part B — Kubernetes |
| 10 min | Part C — CI/CD walkthrough |

---

## Part A — Docker & Compose

Build and run all four services together:

```bash
docker compose up --build -d
docker compose ps
```

Call each atomic service directly first, so you see it work in isolation
before anything is composed:

```bash
curl "http://localhost:8001/fee?amount=1000"
curl "http://localhost:8002/accounts/ACC1001"
curl http://localhost:8003/journal
```

Now call the composite service — watch it call the other three for you:

```bash
curl -X POST http://localhost:8000/transfer \
  -H "Content-Type: application/json" \
  -d '{"from_account": "ACC1001", "to_account": "ACC1002", "amount": 500}'
```

Watch it happen live in another terminal tab:

```bash
docker compose logs -f fund-transfer-service
```

Try the failure path — Meera's account (`ACC1003`) only has ₹800:

```bash
curl -X POST http://localhost:8000/transfer \
  -H "Content-Type: application/json" \
  -d '{"from_account": "ACC1003", "to_account": "ACC1001", "amount": 5000}'
```

That should fail with a 400 and never touch the journal — confirm with
`curl http://localhost:8003/journal`.

Tear down before moving to Part B:

```bash
docker compose down
```

---

## Part B — Kubernetes

Start a local cluster (~60–90 seconds):

```bash
minikube start --driver=docker
```

Build the images and load them into the cluster (minikube's Docker isn't
the same Docker your `docker compose build` used, so images need loading
explicitly):

```bash
docker compose build
minikube image load fee-service:local
minikube image load account-service:local
minikube image load journal-service:local
minikube image load fund-transfer-service:local
```

Apply everything — namespace, then all four Deployments and Services:

```bash
kubectl apply -f k8s/
kubectl get pods -n fintech-demo
```

Reach the composite service from outside the cluster:

```bash
kubectl port-forward -n fintech-demo svc/fund-transfer-service 8000:8000
```

In a second terminal, run the same `curl -X POST .../transfer` command from
Part A — same request, same code, now running as four pods instead of four
containers on one Docker network.

**Scaling and self-healing**, live:

```bash
kubectl scale deployment fund-transfer-service -n fintech-demo --replicas=3
kubectl get pods -n fintech-demo -w
```

Once three pods are running, delete one and watch Kubernetes replace it
without being asked twice:

```bash
kubectl delete pod -n fintech-demo <one-of-the-fund-transfer-pod-names>
kubectl get pods -n fintech-demo -w
```

Clean up:

```bash
minikube delete
```

---

## Part C — CI/CD walkthrough

Open [`.github/workflows/ci-cd.yaml`](.github/workflows/ci-cd.yaml) and
walk through it as a diagram, not just a file:


---


