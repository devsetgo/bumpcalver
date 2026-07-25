# bumpcalver-plugin-example

A minimal, real, installable example of a third-party `bumpcalver` plugin.
It registers a handler for a new `ini` file_type without modifying
`bumpcalver` itself, using the `bumpcalver.handlers` entry-point group.

See [`docs/development-guide.md`](../../docs/development-guide.md)'s
"Distributing Your Handler as a Plugin" section for the full writeup of how
this works.

## Try it

```bash
# From the repository root, with bumpcalver's own dev environment active:
pip install -e examples/bumpcalver-plugin-example

cd examples/bumpcalver-plugin-example
bumpcalver --build
cat example.ini
```

`bumpcalver.toml` in this directory declares `example.ini` with
`file_type = "ini"` — a type that doesn't exist until the plugin is
installed. The `ini` file_type is not defined anywhere in `bumpcalver`'s own source —
installing this package is what makes it available, via
[`src/bumpcalver_plugin_example/handler.py`](src/bumpcalver_plugin_example/handler.py)'s
`IniVersionHandler`, declared in [`pyproject.toml`](pyproject.toml):

```toml
[project.entry-points."bumpcalver.handlers"]
ini = "bumpcalver_plugin_example.handler:IniVersionHandler"
```

To remove it again: `pip uninstall bumpcalver-plugin-example`.
