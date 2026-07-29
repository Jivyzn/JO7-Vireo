# Security policy

## Supported version

The current supported public research release is `1.x`.

## Reporting a vulnerability

Do not publish exploitable security, privacy or hardware-safety issues in a public issue before the maintainer has had a reasonable opportunity to review them. Use a private GitHub security advisory after the repository is created.

Reports should include:

- affected version and file;
- reproducible steps;
- expected and observed behaviour;
- impact on privacy, local command execution, camera/microphone use or physical hardware;
- suggested mitigation when available.

## Sensitive material

Never commit:

- SSH keys, passwords or tokens;
- Wi-Fi credentials;
- private Roboflow links;
- participant recordings or identifiable user-study data;
- exact home addresses or emergency contacts;
- unreviewed battery-pack instructions.

## Local command execution

The optional Ollama integration invokes the local `ollama` executable with recognised speech as model input. It does not intentionally execute generated shell commands. Keep that boundary intact.
