# Short installer endpoint (prepared, not live)

Desired public command:

```sh
curl -fsSL https://cognigenesis.tech/install.sh | sh
```

The domain's existing web host must serve the repository's reviewed `install.sh` verbatim at `/install.sh`, with HTTP 200, `Content-Type: text/x-shellscript` (or `text/plain`), and HTTPS. DNS records at Namecheap only select the host; DNS cannot route an individual path. Preserve the existing site's root page and other paths.

## Release steps

1. Complete `PRIVATE_RELEASE_POLICY.md` for the exact release commit and files, including the install script and code delivered by the script. Do not use an anonymous public installer while the harness must remain private. A public shell script that clones an authenticated private GitHub repository will not install for unauthenticated users.
2. Choose the existing `cognigenesis.tech` web host, add `/install.sh` as a static asset there, or add a server route that serves the approved immutable script. Do not point the apex domain at a new host merely to serve this file; doing so could replace the current website.
3. If changing hosting, record the provider's exact apex A/ALIAS target and ownership proof. Apply only those records in Namecheap after verifying the current authoritative DNS and existing site routing.
4. Verify `curl -fIL https://cognigenesis.tech/install.sh` returns 200 and `curl -fsSL https://cognigenesis.tech/install.sh` returns the shell script, not HTML or a redirect to a login page. Compare its SHA-256 to the approved script.
5. Test installation on macOS, Linux, and Termux in disposable environments before advertising the public command.

The GitHub PR contains a root-level installer and a mirrored `scripts/install.sh`. Until the domain route and release gate are complete, the command above is a target, not a working installation method.
