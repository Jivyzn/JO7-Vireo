# Original prototype code archive

These files preserve source recovered from the supplied project reports and original launcher. They retain hard-coded paths, prototype naming and known issues for provenance.

Use the maintained files under `src/`, `firmware/` and `scripts/` for deployment.

Notable changes in the maintained release include:

- repository-relative, environment-configurable paths;
- a real 15-second timeout instead of `sleep 15` after a blocking process;
- hardware-independent unit tests;
- descriptive firmware names and boot-failure handling;
- optional eSpeak fallback when personal WAV files are absent;
- corrected Ollama subprocess text input;
- bounded microphone and announcement queues;
- safer shutdown and clearer error messages.
