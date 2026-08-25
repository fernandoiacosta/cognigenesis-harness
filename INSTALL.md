# Installation

Cognigenesis Harness supports macOS, Linux, and Windows.

Because the repository is currently private, installation requires authenticated access to GitHub. Anonymous raw-file installers will only work after the project or installer is published.

## Preferred package install

If your Git credentials can access the private repository:

```bash
uv tool install git+https://github.com/fernandoiacosta/cognigenesis-harness.git
```

or:

```bash
pipx install git+https://github.com/fernandoiacosta/cognigenesis-harness.git
```

After installation:

```bash
cogni --help
cogni "Create a Python CLI project for tracking expenses"
```

## Authenticated one-liner — macOS/Linux

With GitHub CLI installed and authenticated:

```bash
gh api repos/fernandoiacosta/cognigenesis-harness/contents/scripts/install.sh -H "Accept: application/vnd.github.raw+json" | sh
```

## Authenticated one-liner — Windows PowerShell

With GitHub CLI installed and authenticated:

```powershell
$script = gh api repos/fernandoiacosta/cognigenesis-harness/contents/scripts/install.ps1 -H "Accept: application/vnd.github.raw+json"; Invoke-Expression ($script -join "`n")
```

## Future public one-liners

Once the installer is publicly reachable, the intended UX is:

```bash
curl -fsSL <public-installer-url>/install.sh | sh
```

and:

```powershell
irm <public-installer-url>/install.ps1 | iex
```
