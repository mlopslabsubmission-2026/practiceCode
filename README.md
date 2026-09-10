# Fintech Cloud Demo — Fund Transfer

A working version of the composite/atomic microservices diagram from the
"API Banking" slide: a **Fund Transfer** service that orchestrates three
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
| 5 min | Wrap-up / Q&A |

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

Start a local cluster (~60–90 seconds — this is a good moment to talk
through what a control plane actually spins up while it runs):

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

1. **`test`** — runs on every push and pull request, one matrix job per
   service, `pytest` against each service's own test file.
2. **`build-and-push`** — only runs on `main`, and only after `test`
   passes; builds and pushes each service's image to GitHub Container
   Registry (`ghcr.io`).
3. There is **no deploy job** — and the comment in the file explains why:
   GitHub's hosted runners have no network path to a student's personal
   Codespace or a local cluster. In a real deployment, this stage would run
   `kubectl apply` against a cluster the runner *can* reach — a cloud
   cluster, not a laptop.

### Live run (instructor only)

Only the repo owner can push to `main` — students' own Codespaces have read
access, not write, so this part is done by the instructor, screen-shared.
Students can also open the Actions tab themselves in their own browser and
watch it run live in parallel — it's a public repo, so no push access is
needed to *watch*, only to trigger. Four steps: green, see the build,
red, recover.

**Step 1 — a clean, additive change.** In `services/fee-service/main.py`,
change the return line:

```python
return {"amount": amount, "fee": fee}
```

to:

```python
return {"amount": amount, "fee": fee, "currency": "INR"}
```

Add a test for it in `services/fee-service/test_main.py`:

```python
def test_fee_includes_currency():
    resp = client.get("/fee", params={"amount": 100})
    assert resp.json()["currency"] == "INR"
```

Commit and push:

```bash
git add services/fee-service
git commit -m "Add currency field to fee response"
git push
```

Open `github.com/mlopslabsubmission-2026/practiceCode/actions` and watch
live: all four `test` matrix jobs run (point out that `account-service`,
`journal-service`, and `fund-transfer-service` re-run too, even though
their code didn't change — the matrix tests every service on every push,
not just the one that changed), then `build-and-push` runs once `test` is
fully green.

**Step 2 — show the actual build.** Once `build-and-push` finishes, go to
the repo's main page — the right sidebar shows a **Packages** box once
anything's been published from it. Click into `fee-service`: there's the
image that job just built, tagged both `latest` and with the commit SHA
that's currently on screen in the Actions log. This is the artifact the
whole pipeline exists to produce — worth pausing on, since everything
before this was in service of getting here safely.

**Step 3 — show it fail.** Change `FEE_RATE` in `fee-service/main.py`
*without* updating the existing fee assertions in `test_main.py`, then
push. The `test` job goes red, and `build-and-push` never runs at all —
`needs: test` in the workflow file is what enforces that; nothing shipped,
and nothing had to remember to stop it. Point at the greyed-out
`build-and-push` job in the Actions UI as the visible proof.

**Step 4 — recover.** Revert the `FEE_RATE` change (or fix the test
assertions to match it, whichever makes a better discussion), then push
once more and confirm the run goes green end to end. Leave the repo in
this clean state before the next cohort runs this same session.

This is the same shape as the slide deck's CI/CD pipeline (build → test →
deliver → deploy) — worth naming out loud which stage students just ran by
hand (`kubectl apply`, in Part B) that a real pipeline would run for them
automatically.

---

## Troubleshooting

- **`docker: command not found` inside the codespace** — the Docker-in-Docker
  feature can take a few extra seconds to finish initializing after the
  codespace opens; wait a moment and retry.
- **`ImagePullBackOff` in `kubectl get pods`** — the image wasn't loaded
  into minikube's Docker before `kubectl apply`; re-run the `minikube image
  load` commands, then `kubectl rollout restart deployment -n fintech-demo
  <name>`.
- **`curl: (7) Failed to connect` on port 8000 in Part B** — the
  `kubectl port-forward` command occupies its terminal; make sure it's
  still running in its own tab, and use a second tab for `curl`.

## Discussion prompts for the wrap-up

- Which of the four services would you scale independently in production,
  and why might `account-service` need different scaling rules than
  `fee-service`?
- The compensating-credit logic in `fund-transfer-service` (see the
  `try/except` around the credit step in `main.py`) exists because a
  partial failure mid-transfer is a real risk. What would you add to make
  that safer at real scale — where does this get called a "saga"?
- What's the smallest change to this repo that would let the CI/CD
  pipeline actually deploy somewhere, not just build and push?
