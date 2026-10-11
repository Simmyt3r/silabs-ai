# Silabs AI GPU Runner

Silabs AI training uses a temporary self-hosted NVIDIA GPU runner for jobs that
are too slow on GitHub's standard CPU runners.

## Why this architecture

The alignment smoke experiment requires 57 optimizer steps on CPU and was
taking roughly five minutes per step. Two CPU attempts were cancelled by
workflow timeouts even though the training code and data were valid.

The GPU workflow keeps preparation on GitHub-hosted CPU infrastructure and
routes only training plus candidate evaluation to a CUDA runner.

GitHub's managed GPU larger runner is a Tesla T4 with 16 GB VRAM, but managed
larger runners require an organization on GitHub Team or Enterprise. The
portable path for this repository is therefore a temporary self-hosted GPU VM.

## Minimum GPU

Recommended minimum:

- NVIDIA GPU with at least 8 GB VRAM;
- 16 GB VRAM preferred;
- Ubuntu/Linux x64;
- working NVIDIA driver and `nvidia-smi`;
- outbound internet access to GitHub and Hugging Face.

A Tesla T4 16 GB is sufficient for the current 360M-parameter LoRA smoke
experiment. Faster cards such as an L4, A10, RTX 3090/4090 or A100 reduce the
runtime further.

## Security model

The repository is public. Do not attach a long-lived self-hosted runner to it.

The supplied bootstrap registers the runner as:

- repository-scoped;
- manually started;
- labelled `gpu` and `silabs-ai`;
- **ephemeral**, so it accepts one job and then de-registers.

The GPU workflow is `workflow_dispatch` only. It does not run for pull
requests or pushes.

Destroy or stop the GPU VM after the job completes.

## 1. Start a GPU VM

Start an Ubuntu CUDA GPU instance from the provider of your choice. Use an
image that already has a working NVIDIA driver.

In the VM terminal, confirm:

```bash
nvidia-smi
```

If that fails, do not register the runner yet.

## 2. Get a fresh GitHub runner token

Open:

```text
GitHub
→ Simmyt3r/silabs-ai
→ Settings
→ Actions
→ Runners
→ New self-hosted runner
→ Linux
→ x64
```

GitHub will display a short-lived registration token. Copy only the token.

Never commit this token to the repository.

## 3. Register the GPU as an ephemeral runner

On the GPU VM:

```bash
git clone https://github.com/Simmyt3r/silabs-ai.git
cd silabs-ai

export RUNNER_TOKEN='PASTE_THE_FRESH_GITHUB_TOKEN_HERE'
bash scripts/bootstrap_gpu_runner.sh
```

The script:

1. verifies `nvidia-smi`;
2. downloads the latest GitHub Actions runner;
3. registers it to `Simmyt3r/silabs-ai`;
4. assigns the `gpu` and `silabs-ai` labels;
5. registers it as ephemeral;
6. starts the runner in the foreground.

Keep that terminal open.

## 4. Launch the GPU experiment

After the runner appears as **Idle** in GitHub:

```text
GitHub
→ Simmyt3r/silabs-ai
→ Actions
→ Alignment LoRA Smoke GPU
→ Run workflow
```

The workflow performs preparation on a normal GitHub runner, then hands the
prepared artifact to:

```yaml
runs-on: [self-hosted, linux, x64, gpu]
```

The GPU job validates CUDA before training. It installs the CUDA 12.6 PyTorch
wheel and refuses to continue if no CUDA device or insufficient VRAM is found.

## 5. Promotion gates

GPU acceleration changes compute, not quality policy.

The candidate still must satisfy:

- compact behavior >= 95%;
- corrected capability v2 >= 84%;
- raw safety >= 33.3%;
- zero compact regressions;
- zero capability regressions;
- zero raw-safety regressions.

A faster failure is still a failure. We merely waste fewer hours discovering
it.

## 6. Shut the GPU down

When the Actions job finishes:

1. confirm the runner has gone offline/de-registered;
2. stop or delete the cloud GPU VM;
3. review the uploaded `silabs-ai-alignment-smoke-gpu` artifact.

Do not leave paid GPU hardware running after the experiment.


## Fast path: RunPod

A RunPod GPU Pod works well for this ephemeral runner pattern because it gives
you a Linux terminal on a dedicated GPU container.

Recommended flow:

1. Create a RunPod account.
2. Open **Pods** and choose **Deploy Pod**.
3. Choose the official **RunPod PyTorch** template.
4. Choose one NVIDIA GPU:
   - T4 16 GB: sufficient;
   - A10 / RTX 3090 / RTX 4090: preferred for faster smoke training;
   - larger cards are unnecessary for the current 360M LoRA experiment.
5. Use at least 20 GB container disk and about 20 GB system RAM.
6. Deploy the Pod.
7. Open its web terminal.
8. Run `nvidia-smi`.
9. Follow the GitHub runner-token and bootstrap steps above.
10. When the Actions job finishes, terminate the Pod so billing stops.

The Pod does not need the Silabs datasets preloaded. GitHub Actions and the
repository workflows reconstruct/download everything required.
