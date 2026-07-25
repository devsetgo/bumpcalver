# tests/test_handlers.py
import json
import xml.etree.ElementTree as ET
from typing import Any, Optional
from unittest import mock

import pytest
import tomlkit
from ruamel.yaml import YAMLError
from src.bumpcalver.handlers import (
    DockerfileVersionHandler,
    EnvVersionHandler,
    JsonVersionHandler,
    MakefileVersionHandler,
    PropertiesVersionHandler,
    PythonVersionHandler,
    RegexVersionHandler,
    SetupCfgVersionHandler,
    TextVersionHandler,
    TomlVersionHandler,
    VersionHandler,
    XmlVersionHandler,
    YamlVersionHandler,
    get_version_handler,
    update_version_in_files,
)


def test_python_handler_read_version(monkeypatch):
    handler = PythonVersionHandler()
    file_content = """
__version__ = "2023-10-10"
"""
    mock_open = mock.mock_open(read_data=file_content)
    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version("dummy_file.py", "__version__")
    assert version == "2023-10-10"


def test_python_handler_update_version(monkeypatch):
    handler = PythonVersionHandler()
    file_content = """
__version__ = "2023-10-10"
"""
    # Expected content after update
    mock_open = mock.mock_open(read_data=file_content)
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("dummy_file.py", "__version__", "2023-10-11")
    assert result is True

    handle = mock_open()
    handle.write.assert_called_once()
    written_content = handle.write.call_args[0][0]
    assert '__version__ = "2023-10-11"' in written_content


def test_python_handler_update_version_exception(monkeypatch, capsys):
    handler = PythonVersionHandler()
    file_content = '__version__ = "2023-10-10"'

    # Create a mock for 'open' that raises an exception when writing
    mock_open = mock.mock_open(read_data=file_content)
    mock_open.side_effect = [
        mock_open.return_value,
        IOError("Unable to open file for writing"),
    ]

    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("dummy_file.py", "__version__", "2023-10-11")
    assert result is False

    captured = capsys.readouterr()
    assert "Error updating dummy_file.py: Unable to open file for writing" in captured.out


def test_toml_handler_read_version(monkeypatch):
    handler = TomlVersionHandler()
    toml_content = """
[tool.poetry]
version = "2023-10-10"
"""
    mock_open = mock.mock_open(read_data=toml_content)
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr(tomlkit, "load", lambda f: {"tool": {"poetry": {"version": "2023-10-10"}}})

    version = handler.read_version("pyproject.toml", "tool.poetry.version")
    assert version == "2023-10-10"


def test_toml_handler_update_version(monkeypatch):
    handler = TomlVersionHandler()
    toml_content = """
[tool.poetry]
version = "2023-10-10"
"""
    mock_open = mock.mock_open(read_data=toml_content)
    monkeypatch.setattr("builtins.open", mock_open)
    toml_data = {"tool": {"poetry": {"version": "2023-10-10"}}}
    monkeypatch.setattr(tomlkit, "load", lambda f: toml_data)
    dump_mock = mock.Mock()
    monkeypatch.setattr(tomlkit, "dump", dump_mock)

    result = handler.update_version("pyproject.toml", "tool.poetry.version", "2023-10-11")
    assert result is True

    expected_data = {"tool": {"poetry": {"version": "2023-10-11"}}}
    dump_mock.assert_called_once()
    args, kwargs = dump_mock.call_args
    assert args[0] == expected_data


def test_yaml_handler_read_version(monkeypatch):
    from src.bumpcalver import handlers

    handler = YamlVersionHandler()
    mock_open = mock.mock_open(read_data='version: "2023-10-10"\n')
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr(handlers._yaml, "load", lambda f: {"version": "2023-10-10"})

    version = handler.read_version("config.yaml", "version")
    assert version == "2023-10-10"


def test_yaml_handler_update_version(monkeypatch):
    from src.bumpcalver import handlers

    handler = YamlVersionHandler()
    mock_open = mock.mock_open(read_data='version: "2023-10-10"\n')
    monkeypatch.setattr("builtins.open", mock_open)
    yaml_data = {"version": "2023-10-10"}
    monkeypatch.setattr(handlers._yaml, "load", lambda f: yaml_data)
    dump_mock = mock.Mock()
    monkeypatch.setattr(handlers._yaml, "dump", dump_mock)

    result = handler.update_version("config.yaml", "version", "2023-10-11")
    assert result is True

    expected_data = {"version": "2023-10-11"}
    dump_mock.assert_called_once_with(expected_data, mock.ANY)


def test_yaml_handler_update_version_preserves_key_order(tmp_path):
    # Regression test for the real bug: yaml.safe_dump (the plain PyYAML
    # package this handler used before migrating to ruamel.yaml) defaults to
    # sort_keys=True, which would alphabetize every top-level and nested key
    # on every bump, silently destroying the author's intended file layout.
    # Uses a real file (no mocking of ruamel.yaml) so it actually exercises
    # real round-trip behavior rather than assuming it away.
    handler = YamlVersionHandler()
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text(
        "zebra: first\n"
        "configuration:\n"
        "  name: app\n"
        "  version: '1.0'\n"
        "  alpha: last\n"
        "apple: second\n",
        encoding="utf-8",
    )

    result = handler.update_version(str(yaml_file), "configuration.version", "2.0")
    assert result is True

    written = yaml_file.read_text(encoding="utf-8")
    # Original ordering must survive: zebra/configuration/apple at the top
    # level, and name/version/alpha within the nested mapping.
    assert written.index("zebra") < written.index("configuration")
    assert written.index("configuration") < written.index("apple")
    assert written.index("name") < written.index("version") < written.index("alpha")
    assert "version: '2.0'" in written


def test_yaml_handler_update_version_preserves_comments(tmp_path):
    # Regression test for a real bug that predated the ruamel.yaml migration:
    # yaml.safe_load()/yaml.safe_dump() round-trip through a plain dict, which
    # has no comment model, so every comment in the file was silently dropped
    # on write — sort_keys=False (the earlier fix) only ever addressed key
    # ordering, not this. Uses a real file (no mocking of ruamel.yaml) so it
    # actually exercises real round-trip behavior rather than assuming it away.
    handler = YamlVersionHandler()
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text(
        "# top-level comment\n"
        "zebra: first  # inline comment\n"
        "configuration:\n"
        "  # nested comment\n"
        "  name: app\n"
        "  version: '1.0'\n",
        encoding="utf-8",
    )

    result = handler.update_version(str(yaml_file), "configuration.version", "2.0")
    assert result is True

    written = yaml_file.read_text(encoding="utf-8")
    assert "# top-level comment" in written
    assert "# inline comment" in written
    assert "# nested comment" in written
    assert "version: '2.0'" in written


def test_yaml_handler_read_version_exception(monkeypatch, capsys):
    handler = YamlVersionHandler()

    # Simulate an exception during file reading
    def mock_open(*args, **kwargs):
        raise IOError("Unable to open file")

    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version("config.yaml", "version")
    assert version is None

    captured = capsys.readouterr()
    assert "Error reading version from config.yaml: Unable to open file" in captured.out


def test_yaml_handler_update_version_exception(monkeypatch, capsys):
    from src.bumpcalver import handlers

    handler = YamlVersionHandler()

    # Simulate an exception during _yaml.load
    def mock_yaml_load(f):
        raise YAMLError("Malformed YAML")

    monkeypatch.setattr(handlers._yaml, "load", mock_yaml_load)
    mock_open = mock.mock_open()
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("config.yaml", "version", "2023-10-11")
    assert result is False

    captured = capsys.readouterr()
    assert "Error updating config.yaml: Malformed YAML" in captured.out


def test_json_handler_read_version(monkeypatch):
    handler = JsonVersionHandler()
    json_content = """
{
    "version": "2023-10-10"
}
"""
    mock_open = mock.mock_open(read_data=json_content)
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr(json, "load", lambda f: {"version": "2023-10-10"})

    version = handler.read_version("package.json", "version")
    assert version == "2023-10-10"


def test_json_handler_update_version(monkeypatch):
    handler = JsonVersionHandler()
    json_content = """
{
    "version": "2023-10-10"
}
"""
    mock_open = mock.mock_open(read_data=json_content)
    monkeypatch.setattr("builtins.open", mock_open)
    json_data = {"version": "2023-10-10"}
    monkeypatch.setattr(json, "load", lambda f: json_data)
    dump_mock = mock.Mock()
    monkeypatch.setattr(json, "dump", dump_mock)

    result = handler.update_version("package.json", "version", "2023-10-11")
    assert result is True

    expected_data = {"version": "2023-10-11"}
    dump_mock.assert_called_once_with(expected_data, mock.ANY, indent=2)


def test_json_handler_read_version_exception(monkeypatch, capsys):
    handler = JsonVersionHandler()

    # Simulate an exception during json.load
    def mock_json_load(f):
        raise json.JSONDecodeError("Malformed JSON", "", 0)

    monkeypatch.setattr("json.load", mock_json_load)
    mock_open = mock.mock_open()
    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version("package.json", "version")
    assert version is None

    captured = capsys.readouterr()
    assert "Error reading version from package.json: Malformed JSON" in captured.out


def test_json_handler_update_version_exception(monkeypatch, capsys):
    handler = JsonVersionHandler()

    # Simulate an exception during json.load
    def mock_json_load(f):
        raise json.JSONDecodeError("Malformed JSON", "", 0)

    monkeypatch.setattr("json.load", mock_json_load)
    mock_open = mock.mock_open()
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("package.json", "version", "2023-10-11")
    assert result is False

    captured = capsys.readouterr()
    assert "Error updating package.json: Malformed JSON" in captured.out


def test_xml_handler_read_version(monkeypatch):
    handler = XmlVersionHandler()
    mock_tree = mock.Mock()
    mock_root = mock.Mock()
    mock_element = mock.Mock()
    mock_element.text = "2023-10-10"
    mock_root.find.return_value = mock_element
    mock_tree.getroot.return_value = mock_root
    monkeypatch.setattr(ET, "parse", lambda f: mock_tree)

    version = handler.read_version("config.xml", "version")
    assert version == "2023-10-10"


def test_xml_handler_update_version(monkeypatch):
    handler = XmlVersionHandler()
    mock_tree = mock.Mock()
    mock_root = mock.Mock()
    mock_element = mock.Mock()
    mock_root.find.return_value = mock_element
    mock_tree.getroot.return_value = mock_root
    monkeypatch.setattr(ET, "parse", lambda f, parser=None: mock_tree)

    result = handler.update_version("config.xml", "version", "2023-10-11")
    assert result is True

    assert mock_element.text == "2023-10-11"
    mock_tree.write.assert_called_once_with("config.xml", xml_declaration=True, encoding="UTF-8")


def test_xml_handler_read_version_exception(monkeypatch, capsys):
    handler = XmlVersionHandler()

    # Simulate an exception during ET.parse
    def mock_et_parse(file):
        raise ET.ParseError("Malformed XML")

    monkeypatch.setattr("xml.etree.ElementTree.parse", mock_et_parse)

    version = handler.read_version("config.xml", "version")
    assert version is None

    captured = capsys.readouterr()
    assert "Error reading version from config.xml: Malformed XML" in captured.out


def test_xml_handler_update_version_exception(monkeypatch, capsys):
    handler = XmlVersionHandler()

    # Simulate an exception during ET.parse
    def mock_et_parse(file, parser=None):
        raise ET.ParseError("Malformed XML")

    monkeypatch.setattr("xml.etree.ElementTree.parse", mock_et_parse)

    result = handler.update_version("config.xml", "version", "2023-10-11")
    assert result is False

    captured = capsys.readouterr()
    assert "Error updating config.xml: Malformed XML" in captured.out


def test_xml_handler_update_version_preserves_declaration_and_comments(tmp_path):
    # Regression test for the real bug: ET.parse()/tree.write() silently drop
    # the <?xml ?> declaration and all comments on a plain round-trip. Uses
    # real files (no mocking of ET.parse/tree.write) so it actually exercises
    # ElementTree's behavior rather than assuming it away.
    handler = XmlVersionHandler()
    xml_file = tmp_path / "config.xml"
    xml_file.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<project>\n"
        "    <!-- inner comment describing the version below -->\n"
        "    <version>1.0.0</version>\n"
        "</project>\n",
        encoding="utf-8",
    )

    result = handler.update_version(str(xml_file), "version", "2.0.0")
    assert result is True

    written = xml_file.read_text(encoding="utf-8")
    assert written.startswith("<?xml version=")
    assert "inner comment describing the version below" in written
    assert "<version>2.0.0</version>" in written


def test_dockerfile_handler_read_version(monkeypatch):
    handler = DockerfileVersionHandler()
    dockerfile_content = """
FROM python:3.8
ARG VERSION=2023-10-10
"""
    mock_open = mock.mock_open(read_data=dockerfile_content)
    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version("Dockerfile", "VERSION", directive="ARG")
    assert version == "2023-10-10"


def test_dockerfile_handler_update_version(monkeypatch):
    handler = DockerfileVersionHandler()
    dockerfile_content = """
FROM python:3.8
ARG VERSION=2023-10-10
"""
    mock_open = mock.mock_open(read_data=dockerfile_content)
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("Dockerfile", "VERSION", "2023-10-11", directive="ARG")
    assert result is True

    handle = mock_open()
    handle.write.assert_called_once()
    written_content = handle.write.call_args[0][0]
    assert "ARG VERSION=2023-10-11" in written_content


def test_dockerfile_handler_update_version_invalid_directive(capsys):
    handler = DockerfileVersionHandler()

    result = handler.update_version("Dockerfile", "VERSION", "2023-10-11", directive="INVALID")
    assert result is False

    captured = capsys.readouterr()
    assert "Invalid or missing directive for variable 'VERSION' in Dockerfile." in captured.out


def test_dockerfile_handler_read_version_invalid_directive(capsys):
    handler = DockerfileVersionHandler()

    version = handler.read_version("Dockerfile", "VERSION", directive="INVALID")
    assert version is None

    captured = capsys.readouterr()
    assert "Invalid or missing directive for variable 'VERSION' in Dockerfile." in captured.out


def test_dockerfile_handler_update_version_exception(monkeypatch, capsys):
    handler = DockerfileVersionHandler()

    # Simulate an exception during file reading
    def mock_open(*args, **kwargs):
        raise IOError("Unable to open file")

    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("Dockerfile", "VERSION", "2023-10-11", directive="ARG")
    assert result is False

    captured = capsys.readouterr()
    assert "Error updating Dockerfile: Unable to open file" in captured.out


def test_dockerfile_handler_read_version_exception(monkeypatch, capsys):
    handler = DockerfileVersionHandler()

    # Simulate an exception during file reading
    def mock_open(*args, **kwargs):
        raise IOError("Unable to open file")

    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version("Dockerfile", "VERSION", directive="ARG")
    assert version is None

    captured = capsys.readouterr()
    assert "Error reading version from Dockerfile: Unable to open file" in captured.out


def test_makefile_handler_read_version(monkeypatch):
    handler = MakefileVersionHandler()
    makefile_content = """
VERSION = 2023-10-10
"""
    mock_open = mock.mock_open(read_data=makefile_content)
    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version("Makefile", "VERSION")
    assert version == "2023-10-10"


def test_makefile_handler_update_version(monkeypatch):
    handler = MakefileVersionHandler()
    makefile_content = """
VERSION = 2023-10-10
"""
    mock_open = mock.mock_open(read_data=makefile_content)
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("Makefile", "VERSION", "2023-10-11")
    assert result is True

    handle = mock_open()
    handle.write.assert_called_once()
    written_content = handle.write.call_args[0][0]
    assert "VERSION = 2023-10-11" in written_content


def test_makefile_handler_read_version_exception(monkeypatch, capsys):
    handler = MakefileVersionHandler()

    # Simulate an exception during file reading
    def mock_open(*args, **kwargs):
        raise IOError("Unable to open file")

    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version("Makefile", "VERSION")
    assert version is None

    captured = capsys.readouterr()
    assert "Error reading version from Makefile: Unable to open file" in captured.out


def test_makefile_handler_update_version_exception(monkeypatch, capsys):
    handler = MakefileVersionHandler()

    # Simulate an exception during file reading
    def mock_open(*args, **kwargs):
        raise IOError("Unable to open file")

    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("Makefile", "VERSION", "2023-10-11")
    assert result is False

    captured = capsys.readouterr()
    assert "Error updating Makefile: Unable to open file" in captured.out


def test_makefile_handler_read_version_uses_explicit_utf8_encoding(monkeypatch):
    # Regression test: read_version() must open the file with an explicit
    # utf-8 encoding rather than relying on the platform default (which is
    # locale-dependent on Windows), so content parses consistently across
    # the CI matrix's ubuntu/windows runners. Asserting the open() call
    # arguments directly is what actually pins this down — merely reading
    # ASCII content back correctly would pass even without the fix, since
    # this sandbox's own default encoding is already utf-8.
    handler = MakefileVersionHandler()
    mock_open = mock.mock_open(read_data="VERSION = 2023-10-10\n")
    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version("Makefile", "VERSION")
    assert version == "2023-10-10"
    mock_open.assert_called_once_with("Makefile", "r", encoding="utf-8")


def test_makefile_handler_read_version_non_ascii_content(tmp_path):
    handler = MakefileVersionHandler()
    makefile = tmp_path / "Makefile"
    makefile.write_text("# Réglages généraux — see docs\nVERSION = 2023-10-10\n", encoding="utf-8")

    version = handler.read_version(str(makefile), "VERSION")
    assert version == "2023-10-10"


def test_get_version_handler():
    handler = get_version_handler("python")
    assert isinstance(handler, PythonVersionHandler)

    with pytest.raises(ValueError):
        get_version_handler("unsupported")


def test_python_handler_read_version_exception(monkeypatch, capsys):
    handler = PythonVersionHandler()

    # Simulate an exception during file reading
    def mock_open(*args, **kwargs):
        raise IOError("Unable to open file")

    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version("nonexistent_file.py", "__version__")
    assert version is None

    captured = capsys.readouterr()
    assert "Error reading version from nonexistent_file.py: Unable to open file" in captured.out


def test_python_handler_update_version_variable_not_found(monkeypatch, capsys):
    handler = PythonVersionHandler()
    file_content = """
__not_version__ = "2023-10-10"
"""
    mock_open = mock.mock_open(read_data=file_content)
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("dummy_file.py", "__version__", "2023-10-11")
    assert result is False

    captured = capsys.readouterr()
    assert "Variable '__version__' not found in dummy_file.py" in captured.out


def test_toml_handler_read_version_malformed_toml(monkeypatch, capsys):
    from src.bumpcalver import handlers

    handler = handlers.TomlVersionHandler()

    # Simulate malformed TOML content
    def mock_toml_load(f):
        raise handlers.tomlkit.exceptions.TOMLKitError("Malformed TOML")

    # Monkeypatch the 'tomlkit.load' function in the handlers module
    monkeypatch.setattr(handlers.tomlkit, "load", mock_toml_load)

    mock_open = mock.mock_open()
    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version("pyproject.toml", "tool.poetry.version")
    assert version is None

    captured = capsys.readouterr()
    assert "Error reading version from pyproject.toml: Malformed TOML" in captured.out


def test_toml_handler_update_version_exception(monkeypatch, capsys):
    from src.bumpcalver import handlers

    handler = handlers.TomlVersionHandler()

    # Simulate an exception during tomlkit.load
    def mock_toml_load(f):
        raise handlers.tomlkit.exceptions.TOMLKitError("Malformed TOML")

    monkeypatch.setattr(handlers.tomlkit, "load", mock_toml_load)
    mock_open = mock.mock_open()
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("pyproject.toml", "tool.poetry.version", "2023-10-11")
    assert result is False

    captured = capsys.readouterr()
    assert "Error updating pyproject.toml: Malformed TOML" in captured.out


def test_toml_handler_update_version_preserves_comments(tmp_path):
    # Regression test for the real bug: toml.load()/toml.dump() round-trip
    # through a plain dict, which has no comment model, so every comment in
    # the file was silently dropped on write. Uses a real file (no mocking of
    # tomlkit.load/dump) so it actually exercises tomlkit's style-preserving
    # behavior rather than assuming it away. This matters most for this
    # handler's primary target, pyproject.toml, which commonly has comments.
    handler = TomlVersionHandler()
    toml_file = tmp_path / "pyproject.toml"
    toml_file.write_text(
        '# top-level comment\n[tool.poetry]\nversion = "1.0.0"  # inline comment\nname = "demo"\n',
        encoding="utf-8",
    )

    result = handler.update_version(str(toml_file), "tool.poetry.version", "2.0.0")
    assert result is True

    written = toml_file.read_text(encoding="utf-8")
    assert "# top-level comment" in written
    assert "# inline comment" in written
    assert 'version = "2.0.0"' in written
    assert 'name = "demo"' in written


def test_get_version_handler_unsupported_file_type():
    with pytest.raises(ValueError) as exc_info:
        get_version_handler("unsupported")
    assert "Unsupported file type: unsupported" in str(exc_info.value)


def test_update_version_in_files_value_error(capsys):
    new_version = "2023-10-11"
    file_configs = [
        {
            "path": "dummy_file.unsupported",
            "file_type": "unsupported",
            "variable": "__version__",
        }
    ]

    try:
        update_version_in_files(new_version, file_configs)
    except ValueError as e:
        assert str(e) == "Unsupported file type: unsupported"


def test_toml_handler_read_version_variable_not_found(monkeypatch, capsys):
    handler = TomlVersionHandler()
    toml_content = """
[tool.poetry]
name = "example"
"""
    mock_open = mock.mock_open(read_data=toml_content)
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr(tomlkit, "load", lambda f: {"tool": {"poetry": {"name": "example"}}})

    version = handler.read_version("pyproject.toml", "tool.poetry.version")
    assert version is None

    captured = capsys.readouterr()
    assert "Variable 'tool.poetry.version' not found in pyproject.toml" in captured.out


def test_toml_handler_update_version_variable_not_found(monkeypatch, capsys):
    handler = TomlVersionHandler()
    toml_content = """
[tool.poetry]
name = "example"
"""
    mock_open = mock.mock_open(read_data=toml_content)
    monkeypatch.setattr("builtins.open", mock_open)
    toml_data = {"tool": {"poetry": {"name": "example"}}}
    monkeypatch.setattr(tomlkit, "load", lambda f: toml_data)
    dump_mock = mock.Mock()
    monkeypatch.setattr(tomlkit, "dump", dump_mock)

    result = handler.update_version("pyproject.toml", "tool.poetry.version", "2023-10-11")
    assert result is False

    captured = capsys.readouterr()
    assert "Variable 'tool.poetry.version' not found in pyproject.toml" in captured.out


def test_yaml_handler_read_version_variable_not_found(monkeypatch, capsys):
    from src.bumpcalver import handlers

    handler = YamlVersionHandler()
    mock_open = mock.mock_open(read_data='version: "2023-10-10"\n')
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr(handlers._yaml, "load", lambda f: {"version": "2023-10-10"})

    version = handler.read_version("config.yaml", "nonexistent_variable")
    assert version is None

    captured = capsys.readouterr()
    assert "Variable 'nonexistent_variable' not found in config.yaml" in captured.out


def test_xml_handler_update_version_variable_not_found(monkeypatch, capsys):
    handler = XmlVersionHandler()
    xml_content = """
<configuration>
    <version>2023-10-10</version>
</configuration>
"""
    mock_open = mock.mock_open(read_data=xml_content)
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr(
        ET, "parse", lambda f, parser=None: ET.ElementTree(ET.fromstring(xml_content))
    )

    result = handler.update_version("config.xml", "nonexistent_variable", "2023-10-11")
    assert result is False

    captured = capsys.readouterr()
    print(f"Captured output: {captured.out}")  # Debugging line
    assert "Variable 'nonexistent_variable' not found in config.xml" in captured.out


def test_dockerfile_handler_read_version_variable_not_found(monkeypatch, capsys):
    handler = DockerfileVersionHandler()
    dockerfile_content = """
FROM python:3.8
"""
    mock_open = mock.mock_open(read_data=dockerfile_content)
    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version("Dockerfile", "VERSION", directive="ARG")
    assert version is None

    captured = capsys.readouterr()
    assert "No ARG variable 'VERSION' found in Dockerfile" in captured.out


def test_dockerfile_handler_update_version_variable_not_found(monkeypatch, capsys):
    handler = DockerfileVersionHandler()
    dockerfile_content = """
FROM python:3.8
"""
    mock_open = mock.mock_open(read_data=dockerfile_content)
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("Dockerfile", "VERSION", "2023-10-11", directive="ARG")
    assert result is False

    captured = capsys.readouterr()
    assert "No ARG variable 'VERSION' found in Dockerfile" in captured.out


def test_xml_handler_read_version_variable_not_found(monkeypatch, capsys):
    handler = XmlVersionHandler()
    mock_tree = mock.Mock()
    mock_root = mock.Mock()
    mock_root.find.return_value = None
    mock_tree.getroot.return_value = mock_root
    monkeypatch.setattr(ET, "parse", lambda f: mock_tree)

    version = handler.read_version("config.xml", "version")
    assert version is None

    captured = capsys.readouterr()
    assert "Variable 'version' not found in config.xml" in captured.out


def test_makefile_handler_update_version_variable_not_found(monkeypatch, capsys):
    handler = MakefileVersionHandler()
    file_content = """
VERSION = 2023-10-10
"""
    mock_open = mock.mock_open(read_data=file_content)
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("Makefile", "NON_EXISTENT_VARIABLE", "2023-10-11")
    assert result is False

    captured = capsys.readouterr()
    assert "Variable 'NON_EXISTENT_VARIABLE' not found in Makefile" in captured.out


def test_update_version_in_files_no_file_type(capsys):
    new_version = "2023-10-11"
    file_configs = [{"path": "dummy_file.py", "variable": "__version__"}]

    try:
        update_version_in_files(new_version, file_configs)
    except ValueError as e:
        assert str(e) == "Unsupported file type: "


# Tests for PropertiesVersionHandler
def test_properties_handler_read_version(monkeypatch):
    """Test reading version from a properties file."""
    handler = PropertiesVersionHandler()
    properties_content = """sonar.projectKey=devsetgo_bumpcalver
sonar.organization=devsetgo
sonar.projectName=bumpcalver
sonar.projectVersion=2024-09-27-007
sonar.language=python
sonar.sources=src
"""
    mock_open = mock.mock_open(read_data=properties_content)
    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version("sonar-project.properties", "sonar.projectVersion")
    assert version == "2024-09-27-007"


def test_properties_handler_update_version(monkeypatch):
    """Test updating version in a properties file."""
    handler = PropertiesVersionHandler()
    properties_content = """sonar.projectKey=devsetgo_bumpcalver
sonar.organization=devsetgo
sonar.projectName=bumpcalver
sonar.projectVersion=2024-09-27-007
sonar.language=python
sonar.sources=src
"""
    mock_open = mock.mock_open(read_data=properties_content)
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version(
        "sonar-project.properties", "sonar.projectVersion", "2025-08-01-001"
    )
    assert result is True

    handle = mock_open()
    handle.writelines.assert_called_once()
    written_lines = handle.writelines.call_args[0][0]
    # Check that the version line was updated
    version_line_found = any(
        "sonar.projectVersion=2025-08-01-001" in line for line in written_lines
    )
    assert version_line_found


def test_properties_handler_read_version_not_found(monkeypatch, capsys):
    """Test reading a non-existent property."""
    handler = PropertiesVersionHandler()
    properties_content = """sonar.projectKey=devsetgo_bumpcalver
sonar.organization=devsetgo
"""
    mock_open = mock.mock_open(read_data=properties_content)
    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version("sonar-project.properties", "sonar.projectVersion")
    assert version is None


def test_properties_handler_update_version_not_found(monkeypatch, capsys):
    """Test updating a non-existent property."""
    handler = PropertiesVersionHandler()
    properties_content = """sonar.projectKey=devsetgo_bumpcalver
sonar.organization=devsetgo
"""
    mock_open = mock.mock_open(read_data=properties_content)
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version(
        "sonar-project.properties", "sonar.projectVersion", "2025-08-01-001"
    )
    assert result is False

    captured = capsys.readouterr()
    assert "Property 'sonar.projectVersion' not found in sonar-project.properties" in captured.out


def test_properties_handler_read_version_exception(monkeypatch, capsys):
    """Test exception handling during read operation."""
    handler = PropertiesVersionHandler()

    def mock_open(*args, **kwargs):
        raise IOError("Unable to open file")

    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version("sonar-project.properties", "sonar.projectVersion")
    assert version is None

    captured = capsys.readouterr()
    assert "Error reading sonar-project.properties: Unable to open file" in captured.out


def test_properties_handler_update_version_exception(monkeypatch, capsys):
    """Test exception handling during update operation."""
    handler = PropertiesVersionHandler()

    def mock_open(*args, **kwargs):
        raise IOError("Unable to open file")

    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version(
        "sonar-project.properties", "sonar.projectVersion", "2025-08-01-001"
    )
    assert result is False

    captured = capsys.readouterr()
    assert "Error updating sonar-project.properties: Unable to open file" in captured.out


# Tests for EnvVersionHandler
def test_env_handler_read_version(monkeypatch):
    """Test reading version from a .env file."""
    handler = EnvVersionHandler()
    env_content = """# Environment variables
DEBUG=true
VERSION=1.0.0
DATABASE_URL=postgresql://localhost/mydb
"""
    mock_open = mock.mock_open(read_data=env_content)
    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version(".env", "VERSION")
    assert version == "1.0.0"


def test_env_handler_read_version_with_quotes(monkeypatch):
    """Test reading version from a .env file with quotes."""
    handler = EnvVersionHandler()
    env_content = """VERSION="1.0.0"
API_KEY='secret123'
"""
    mock_open = mock.mock_open(read_data=env_content)
    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version(".env", "VERSION")
    assert version == "1.0.0"


def test_env_handler_update_version(monkeypatch):
    """Test updating version in a .env file."""
    handler = EnvVersionHandler()
    env_content = """# Environment variables
DEBUG=true
VERSION=1.0.0
DATABASE_URL=postgresql://localhost/mydb
"""
    mock_open = mock.mock_open(read_data=env_content)
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version(".env", "VERSION", "2025-08-01-001")
    assert result is True

    handle = mock_open()
    handle.writelines.assert_called_once()
    written_lines = handle.writelines.call_args[0][0]
    # Check that the version line was updated
    version_line_found = any("VERSION=2025-08-01-001" in line for line in written_lines)
    assert version_line_found


def test_env_handler_read_version_not_found(monkeypatch):
    """Test reading a non-existent environment variable."""
    handler = EnvVersionHandler()
    env_content = """DEBUG=true
DATABASE_URL=postgresql://localhost/mydb
"""
    mock_open = mock.mock_open(read_data=env_content)
    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version(".env", "VERSION")
    assert version is None


def test_env_handler_update_version_not_found(monkeypatch, capsys):
    """Test updating a non-existent environment variable."""
    handler = EnvVersionHandler()
    env_content = """DEBUG=true
DATABASE_URL=postgresql://localhost/mydb
"""
    mock_open = mock.mock_open(read_data=env_content)
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version(".env", "VERSION", "2025-08-01-001")
    assert result is False

    captured = capsys.readouterr()
    assert "Environment variable 'VERSION' not found in .env" in captured.out


def test_env_handler_read_version_exception(monkeypatch, capsys):
    """Test exception handling during read operation."""
    handler = EnvVersionHandler()

    def mock_open(*args, **kwargs):
        raise IOError("Unable to open file")

    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version(".env", "VERSION")
    assert version is None

    captured = capsys.readouterr()
    assert "Error reading .env: Unable to open file" in captured.out


def test_env_handler_update_version_exception(monkeypatch, capsys):
    """Test exception handling during update operation."""
    handler = EnvVersionHandler()

    def mock_open(*args, **kwargs):
        raise IOError("Unable to open file")

    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version(".env", "VERSION", "2025-08-01-001")
    assert result is False

    captured = capsys.readouterr()
    assert "Error updating .env: Unable to open file" in captured.out


# Tests for SetupCfgVersionHandler
def test_setup_cfg_handler_read_version(monkeypatch):
    """Test reading version from a setup.cfg file."""
    handler = SetupCfgVersionHandler()

    # Mock configparser
    mock_config = mock.Mock()
    mock_config.sections.return_value = ["metadata", "options"]
    mock_config.__contains__ = lambda self, key: key == "metadata"
    mock_config.__getitem__ = lambda self, key: {"version": "0.1.0"} if key == "metadata" else {}

    mock_configparser = mock.Mock()
    mock_configparser.ConfigParser.return_value = mock_config

    monkeypatch.setattr("configparser.ConfigParser", mock_configparser.ConfigParser)

    version = handler.read_version("setup.cfg", "metadata.version")
    assert version == "0.1.0"


def test_setup_cfg_handler_read_version_simple_key(monkeypatch):
    """Test reading version from setup.cfg using simple key (no dot notation)."""
    handler = SetupCfgVersionHandler()

    # Mock configparser
    mock_section = {"version": "0.1.0", "name": "test"}
    mock_config = mock.Mock()
    mock_config.sections.return_value = ["metadata"]
    mock_config.__getitem__ = lambda self, key: mock_section if key == "metadata" else {}

    mock_configparser = mock.Mock()
    mock_configparser.ConfigParser.return_value = mock_config

    monkeypatch.setattr("configparser.ConfigParser", mock_configparser.ConfigParser)

    version = handler.read_version("setup.cfg", "version")
    assert version == "0.1.0"


def test_setup_cfg_handler_update_version(monkeypatch):
    """Test updating version in a setup.cfg file."""
    handler = SetupCfgVersionHandler()

    # Mock configparser
    mock_section = {"version": "0.1.0"}
    mock_config = mock.Mock()
    mock_config.sections.return_value = ["metadata"]
    mock_config.__contains__ = lambda self, key: key == "metadata"
    mock_config.__getitem__ = lambda self, key: mock_section if key == "metadata" else {}
    mock_config.read = mock.Mock()
    mock_config.write = mock.Mock()

    mock_configparser = mock.Mock()
    mock_configparser.ConfigParser.return_value = mock_config

    monkeypatch.setattr("configparser.ConfigParser", mock_configparser.ConfigParser)

    mock_open = mock.mock_open()
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("setup.cfg", "metadata.version", "2025-08-01-001")
    assert result is True

    # Verify the version was set
    assert mock_section["version"] == "2025-08-01-001"
    mock_config.write.assert_called_once()


def test_setup_cfg_handler_read_version_not_found(monkeypatch):
    """Test reading a non-existent configuration key."""
    handler = SetupCfgVersionHandler()

    # Mock configparser
    mock_config = mock.Mock()
    mock_config.sections.return_value = ["metadata"]
    mock_config.__contains__ = lambda self, key: False
    mock_config.__getitem__ = lambda self, key: {}

    mock_configparser = mock.Mock()
    mock_configparser.ConfigParser.return_value = mock_config

    monkeypatch.setattr("configparser.ConfigParser", mock_configparser.ConfigParser)

    version = handler.read_version("setup.cfg", "metadata.version")
    assert version is None


def test_setup_cfg_handler_update_version_create_section(monkeypatch):
    """Test updating version when section doesn't exist."""
    handler = SetupCfgVersionHandler()

    # Mock configparser
    mock_config = mock.Mock()
    mock_config.sections.return_value = []
    mock_config.__contains__ = lambda self, key: False
    mock_config.add_section = mock.Mock()
    mock_config.__getitem__ = lambda self, key: {}
    mock_config.read = mock.Mock()
    mock_config.write = mock.Mock()

    mock_configparser = mock.Mock()
    mock_configparser.ConfigParser.return_value = mock_config

    monkeypatch.setattr("configparser.ConfigParser", mock_configparser.ConfigParser)

    mock_open = mock.mock_open()
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("setup.cfg", "metadata.version", "2025-08-01-001")
    assert result is True

    mock_config.add_section.assert_called_with("metadata")


def test_setup_cfg_handler_read_version_exception(monkeypatch, capsys):
    """Test exception handling during read operation."""
    handler = SetupCfgVersionHandler()

    def mock_configparser():
        raise ImportError("configparser not available")

    monkeypatch.setattr("configparser.ConfigParser", mock_configparser)

    version = handler.read_version("setup.cfg", "metadata.version")
    assert version is None

    captured = capsys.readouterr()
    assert "Error reading setup.cfg:" in captured.out


def test_setup_cfg_handler_update_version_exception(monkeypatch, capsys):
    """Test exception handling during update operation."""
    handler = SetupCfgVersionHandler()

    def mock_configparser():
        raise ImportError("configparser not available")

    monkeypatch.setattr("configparser.ConfigParser", mock_configparser)

    result = handler.update_version("setup.cfg", "metadata.version", "2025-08-01-001")
    assert result is False

    captured = capsys.readouterr()
    assert "Error updating setup.cfg:" in captured.out


def test_setup_cfg_handler_update_version_simple_key_found(monkeypatch):
    """Test updating version using simple key that exists in a section."""
    handler = SetupCfgVersionHandler()

    # Mock configparser - version exists in metadata section
    mock_section = {"version": "0.1.0", "name": "test"}
    mock_config = mock.Mock()
    mock_config.sections.return_value = ["metadata", "options"]
    mock_config.__contains__ = lambda self, key: False  # No dot notation
    mock_config.__getitem__ = lambda self, key: mock_section if key == "metadata" else {}
    mock_config.read = mock.Mock()
    mock_config.write = mock.Mock()

    mock_configparser = mock.Mock()
    mock_configparser.ConfigParser.return_value = mock_config

    monkeypatch.setattr("configparser.ConfigParser", mock_configparser.ConfigParser)

    mock_open = mock.mock_open()
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("setup.cfg", "version", "2025-08-01-001")
    assert result is True

    # Verify the version was set
    assert mock_section["version"] == "2025-08-01-001"
    mock_config.write.assert_called_once()


def test_setup_cfg_handler_update_version_simple_key_not_found_add_to_metadata(monkeypatch):
    """Test updating version using simple key that doesn't exist - add to metadata section."""
    handler = SetupCfgVersionHandler()

    # Mock configparser - version doesn't exist in any section, metadata section exists
    mock_metadata_section = {"name": "test"}
    mock_config = mock.Mock()
    mock_config.sections.return_value = ["metadata", "options"]
    mock_config.__contains__ = lambda self, key: key == "metadata"  # metadata exists
    mock_config.__getitem__ = lambda self, key: mock_metadata_section if key == "metadata" else {}
    mock_config.read = mock.Mock()
    mock_config.write = mock.Mock()

    mock_configparser = mock.Mock()
    mock_configparser.ConfigParser.return_value = mock_config

    monkeypatch.setattr("configparser.ConfigParser", mock_configparser.ConfigParser)

    mock_open = mock.mock_open()
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("setup.cfg", "version", "2025-08-01-001")
    assert result is True

    # Verify the version was added to metadata section
    assert mock_metadata_section["version"] == "2025-08-01-001"
    mock_config.write.assert_called_once()


def test_setup_cfg_handler_update_version_simple_key_no_metadata_section(monkeypatch):
    """Test updating version using simple key when metadata section doesn't exist."""
    handler = SetupCfgVersionHandler()

    # Mock configparser - no metadata section exists
    mock_metadata_section = {}
    mock_config = mock.Mock()
    mock_config.sections.return_value = ["options"]
    mock_config.__contains__ = lambda self, key: False  # metadata doesn't exist
    mock_config.__getitem__ = lambda self, key: mock_metadata_section if key == "metadata" else {}
    mock_config.add_section = mock.Mock()
    mock_config.read = mock.Mock()
    mock_config.write = mock.Mock()

    mock_configparser = mock.Mock()
    mock_configparser.ConfigParser.return_value = mock_config

    monkeypatch.setattr("configparser.ConfigParser", mock_configparser.ConfigParser)

    mock_open = mock.mock_open()
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version("setup.cfg", "version", "2025-08-01-001")
    assert result is True

    # Verify metadata section was created and version was added
    mock_config.add_section.assert_called_with("metadata")
    assert mock_metadata_section["version"] == "2025-08-01-001"
    mock_config.write.assert_called_once()


def test_setup_cfg_handler_update_dot_notation_variable():
    """Test _update_dot_notation_variable helper method."""
    import configparser

    from src.bumpcalver.handlers import SetupCfgVersionHandler

    handler = SetupCfgVersionHandler()
    config = configparser.ConfigParser()

    # Test with existing section
    config.add_section("metadata")
    result = handler._update_dot_notation_variable(config, "metadata.version", "1.0.0")
    assert result is True
    assert config["metadata"]["version"] == "1.0.0"

    # Test with non-existing section
    result = handler._update_dot_notation_variable(config, "tool.version", "2.0.0")
    assert result is True
    assert config["tool"]["version"] == "2.0.0"


def test_setup_cfg_handler_update_simple_variable():
    """Test _update_simple_variable helper method."""
    import configparser

    from src.bumpcalver.handlers import SetupCfgVersionHandler

    handler = SetupCfgVersionHandler()
    config = configparser.ConfigParser()

    # Test with existing variable in existing section - should return True
    config.add_section("metadata")
    config["metadata"]["version"] = "0.1.0"
    result = handler._update_simple_variable(config, "version", "1.0.0")
    assert result is True  # Found and updated existing variable
    assert config["metadata"]["version"] == "1.0.0"

    # Test with non-existing variable - should return False but still create the variable
    config2 = configparser.ConfigParser()
    config2.add_section("options")
    result = handler._update_simple_variable(config2, "version", "2.0.0")
    assert result is False  # Variable was not found, so it was created
    assert config2["metadata"]["version"] == "2.0.0"  # But variable was still created


def test_get_version_handler_properties():
    """Test getting properties version handler."""
    handler = get_version_handler("properties")
    assert isinstance(handler, PropertiesVersionHandler)


def test_get_version_handler_env():
    """Test getting env version handler."""
    handler = get_version_handler("env")
    assert isinstance(handler, EnvVersionHandler)


def test_get_version_handler_setup_cfg():
    """Test getting setup.cfg version handler."""
    handler = get_version_handler("setup.cfg")
    assert isinstance(handler, SetupCfgVersionHandler)


def test_get_version_handler_toml():
    """Test getting toml version handler."""
    handler = get_version_handler("toml")
    assert isinstance(handler, TomlVersionHandler)


def test_get_version_handler_yaml():
    """Test getting yaml version handler."""
    handler = get_version_handler("yaml")
    assert isinstance(handler, YamlVersionHandler)


def test_get_version_handler_json():
    """Test getting json version handler."""
    handler = get_version_handler("json")
    assert isinstance(handler, JsonVersionHandler)


def test_get_version_handler_xml():
    """Test getting xml version handler."""
    handler = get_version_handler("xml")
    assert isinstance(handler, XmlVersionHandler)


def test_get_version_handler_dockerfile():
    """Test getting dockerfile version handler."""
    handler = get_version_handler("dockerfile")
    assert isinstance(handler, DockerfileVersionHandler)


def test_get_version_handler_makefile():
    """Test getting makefile version handler."""
    handler = get_version_handler("makefile")
    assert isinstance(handler, MakefileVersionHandler)


def test_get_version_handler_text():
    """Test getting text version handler."""
    handler = get_version_handler("text")
    assert isinstance(handler, TextVersionHandler)


def test_get_version_handler_regex():
    """Test getting regex version handler."""
    handler = get_version_handler("regex")
    assert isinstance(handler, RegexVersionHandler)


# Tests for VersionHandler helper methods
def test_version_handler_read_file_safe_success(monkeypatch):
    """Test _read_file_safe method with successful file read."""
    from src.bumpcalver.handlers import VersionHandler

    # Create a concrete implementation for testing
    class TestHandler(VersionHandler):
        def read_version(self, file_path: str, variable: str, **kwargs):
            pass

        def update_version(self, file_path: str, variable: str, new_version: str, **kwargs):
            pass

    handler = TestHandler()
    file_content = "test content"
    mock_open = mock.mock_open(read_data=file_content)
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler._read_file_safe("test_file.txt")
    assert result == "test content"


def test_version_handler_read_file_safe_exception(monkeypatch, capsys):
    """Test _read_file_safe method with file read exception."""
    from src.bumpcalver.handlers import VersionHandler

    # Create a concrete implementation for testing
    class TestHandler(VersionHandler):
        def read_version(self, file_path: str, variable: str, **kwargs):
            pass

        def update_version(self, file_path: str, variable: str, new_version: str, **kwargs):
            pass

    handler = TestHandler()

    def mock_open(*args, **kwargs):
        raise IOError("Unable to open file")

    monkeypatch.setattr("builtins.open", mock_open)

    result = handler._read_file_safe("nonexistent_file.txt")
    assert result is None

    captured = capsys.readouterr()
    assert "Error reading version from nonexistent_file.txt: Unable to open file" in captured.out


def test_version_handler_write_file_safe_success(monkeypatch, capsys):
    """Test _write_file_safe method with successful file write."""
    from src.bumpcalver.handlers import VersionHandler

    # Create a concrete implementation for testing
    class TestHandler(VersionHandler):
        def read_version(self, file_path: str, variable: str, **kwargs):
            pass

        def update_version(self, file_path: str, variable: str, new_version: str, **kwargs):
            pass

    handler = TestHandler()
    mock_open = mock.mock_open()
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler._write_file_safe("test_file.txt", "test content")
    assert result is True

    mock_open.assert_called_once_with("test_file.txt", "w", encoding="utf-8")
    handle = mock_open()
    handle.write.assert_called_once_with("test content")

    captured = capsys.readouterr()
    assert "Updated test_file.txt" in captured.out


def test_version_handler_write_file_safe_exception(monkeypatch, capsys):
    """Test _write_file_safe method with file write exception."""
    from src.bumpcalver.handlers import VersionHandler

    # Create a concrete implementation for testing
    class TestHandler(VersionHandler):
        def read_version(self, file_path: str, variable: str, **kwargs):
            pass

        def update_version(self, file_path: str, variable: str, new_version: str, **kwargs):
            pass

    handler = TestHandler()

    def mock_open(*args, **kwargs):
        raise IOError("Unable to write file")

    monkeypatch.setattr("builtins.open", mock_open)

    result = handler._write_file_safe("readonly_file.txt", "test content")
    assert result is False

    captured = capsys.readouterr()
    assert "Error updating readonly_file.txt: Unable to write file" in captured.out


def test_version_handler_format_version_with_standard():
    """Test _format_version_with_standard method."""
    from src.bumpcalver.handlers import VersionHandler

    # Create a concrete implementation for testing
    class TestHandler(VersionHandler):
        def read_version(self, file_path: str, variable: str, **kwargs):
            pass

        def update_version(self, file_path: str, variable: str, new_version: str, **kwargs):
            pass

    handler = TestHandler()

    # Test default standard
    result = handler._format_version_with_standard("2024-01-15")
    assert result == "2024-01-15"

    # Test python standard
    result = handler._format_version_with_standard("2024-01-15", version_standard="python")
    assert result == "2024.1.15"  # PEP 440 format

    # Test with custom kwargs
    result = handler._format_version_with_standard(
        "2024-01-15", version_standard="default", other_param="test"
    )
    assert result == "2024-01-15"


def test_version_handler_find_key_value_in_lines():
    """Test _find_key_value_in_lines method."""
    from src.bumpcalver.handlers import VersionHandler

    # Create a concrete implementation for testing
    class TestHandler(VersionHandler):
        def read_version(self, file_path: str, variable: str, **kwargs):
            pass

        def update_version(self, file_path: str, variable: str, new_version: str, **kwargs):
            pass

    handler = TestHandler()

    lines = [
        "# Comment line",
        "DEBUG=true",
        "VERSION=1.0.0",
        "",
        "DATABASE_URL=postgresql://localhost/mydb",
        "# Another comment",
    ]

    # Test finding existing variable
    result = handler._find_key_value_in_lines(lines, "VERSION")
    assert result == 2

    # Test finding first variable
    result = handler._find_key_value_in_lines(lines, "DEBUG")
    assert result == 1

    # Test finding last variable
    result = handler._find_key_value_in_lines(lines, "DATABASE_URL")
    assert result == 4

    # Test non-existent variable
    result = handler._find_key_value_in_lines(lines, "NONEXISTENT")
    assert result is None

    # Test empty lines
    result = handler._find_key_value_in_lines([], "VERSION")
    assert result is None


def test_version_handler_log_variable_not_found(capsys):
    """Test _log_variable_not_found method."""
    from src.bumpcalver.handlers import VersionHandler

    # Create a concrete implementation for testing
    class TestHandler(VersionHandler):
        def read_version(self, file_path: str, variable: str, **kwargs):
            pass

        def update_version(self, file_path: str, variable: str, new_version: str, **kwargs):
            pass

    handler = TestHandler()

    # Test without prefix
    handler._log_variable_not_found("VERSION", "test_file.txt")
    captured = capsys.readouterr()
    assert "Variable 'VERSION' not found in test_file.txt" in captured.out

    # Test with prefix
    handler._log_variable_not_found("VERSION", "test_file.txt", "ARG")
    captured = capsys.readouterr()
    assert "ARG Variable 'VERSION' not found in test_file.txt" in captured.out


def test_version_handler_log_success_update(capsys):
    """Test _log_success_update method."""
    from src.bumpcalver.handlers import VersionHandler

    # Create a concrete implementation for testing
    class TestHandler(VersionHandler):
        def read_version(self, file_path: str, variable: str, **kwargs):
            pass

        def update_version(self, file_path: str, variable: str, new_version: str, **kwargs):
            pass

    handler = TestHandler()

    # Test without extra info
    handler._log_success_update("test_file.txt")
    captured = capsys.readouterr()
    assert "Updated test_file.txt" in captured.out

    # Test with extra info
    handler._log_success_update("test_file.txt", "VERSION variable")
    captured = capsys.readouterr()
    assert "Updated VERSION variable in test_file.txt" in captured.out


def test_version_handler_handle_read_operation_success():
    """Test _handle_read_operation method with successful operation."""
    from src.bumpcalver.handlers import VersionHandler

    # Create a concrete implementation for testing
    class TestHandler(VersionHandler):
        def read_version(self, file_path: str, variable: str, **kwargs):
            pass

        def update_version(self, file_path: str, variable: str, new_version: str, **kwargs):
            pass

    handler = TestHandler()

    def operation_func():
        return "1.0.0"

    result = handler._handle_read_operation("test_file.txt", operation_func)
    assert result == "1.0.0"


def test_version_handler_handle_read_operation_exception(capsys):
    """Test _handle_read_operation method with exception."""
    from src.bumpcalver.handlers import VersionHandler

    # Create a concrete implementation for testing
    class TestHandler(VersionHandler):
        def read_version(self, file_path: str, variable: str, **kwargs):
            pass

        def update_version(self, file_path: str, variable: str, new_version: str, **kwargs):
            pass

    handler = TestHandler()

    def operation_func():
        raise IOError("File operation failed")

    result = handler._handle_read_operation("test_file.txt", operation_func)
    assert result is None

    captured = capsys.readouterr()
    assert "Error reading version from test_file.txt: File operation failed" in captured.out


def test_version_handler_handle_regex_update_success(monkeypatch, capsys):
    """Test _handle_regex_update method with successful update."""
    import re

    from src.bumpcalver.handlers import VersionHandler

    # Create a concrete implementation for testing
    class TestHandler(VersionHandler):
        def read_version(self, file_path: str, variable: str, **kwargs):
            pass

        def update_version(self, file_path: str, variable: str, new_version: str, **kwargs):
            pass

    handler = TestHandler()
    file_content = "VERSION=1.0.0"
    mock_open = mock.mock_open(read_data=file_content)
    monkeypatch.setattr("builtins.open", mock_open)

    pattern = re.compile(r"VERSION=(.+)")

    def replacement_func(match):
        return "VERSION=2.0.0"

    result = handler._handle_regex_update(
        "test_file.txt", pattern, replacement_func, "2.0.0", "VERSION"
    )
    assert result is True

    captured = capsys.readouterr()
    assert "Updated test_file.txt" in captured.out


def test_version_handler_handle_regex_update_no_match(monkeypatch, capsys):
    """Test _handle_regex_update method with no pattern match."""
    import re

    from src.bumpcalver.handlers import VersionHandler

    # Create a concrete implementation for testing
    class TestHandler(VersionHandler):
        def read_version(self, file_path: str, variable: str, **kwargs):
            pass

        def update_version(self, file_path: str, variable: str, new_version: str, **kwargs):
            pass

    handler = TestHandler()
    file_content = "DEBUG=true"
    mock_open = mock.mock_open(read_data=file_content)
    monkeypatch.setattr("builtins.open", mock_open)

    pattern = re.compile(r"VERSION=(.+)")

    def replacement_func(match):
        return "VERSION=2.0.0"

    result = handler._handle_regex_update(
        "test_file.txt", pattern, replacement_func, "2.0.0", "VERSION"
    )
    assert result is False

    captured = capsys.readouterr()
    assert "Variable 'VERSION' not found in test_file.txt" in captured.out


def test_version_handler_handle_regex_update_custom_message(monkeypatch, capsys):
    """Test _handle_regex_update method with custom not found message."""
    import re

    from src.bumpcalver.handlers import VersionHandler

    # Create a concrete implementation for testing
    class TestHandler(VersionHandler):
        def read_version(self, file_path: str, variable: str, **kwargs):
            pass

        def update_version(self, file_path: str, variable: str, new_version: str, **kwargs):
            pass

    handler = TestHandler()
    file_content = "DEBUG=true"
    mock_open = mock.mock_open(read_data=file_content)
    monkeypatch.setattr("builtins.open", mock_open)

    pattern = re.compile(r"VERSION=(.+)")

    def replacement_func(match):
        return "VERSION=2.0.0"

    custom_message = "Custom variable not found message"
    result = handler._handle_regex_update(
        "test_file.txt", pattern, replacement_func, "2.0.0", "VERSION", custom_message
    )
    assert result is False

    captured = capsys.readouterr()
    assert custom_message in captured.out


def test_version_handler_handle_regex_update_read_exception(monkeypatch, capsys):
    """Test _handle_regex_update method with file read exception."""
    import re

    from src.bumpcalver.handlers import VersionHandler

    # Create a concrete implementation for testing
    class TestHandler(VersionHandler):
        def read_version(self, file_path: str, variable: str, **kwargs):
            pass

        def update_version(self, file_path: str, variable: str, new_version: str, **kwargs):
            pass

    handler = TestHandler()

    def mock_open(*args, **kwargs):
        raise IOError("Unable to read file")

    monkeypatch.setattr("builtins.open", mock_open)

    pattern = re.compile(r"VERSION=(.+)")

    def replacement_func(match):
        return "VERSION=2.0.0"

    result = handler._handle_regex_update(
        "test_file.txt", pattern, replacement_func, "2.0.0", "VERSION"
    )
    assert result is False

    captured = capsys.readouterr()
    assert "Error updating test_file.txt: Unable to read file" in captured.out


# ---------------------------------------------------------------------------
# TextVersionHandler — bare, whole-file version content (Capability
# Expansion §5.1: e.g. a plain `VERSION` file used by shell release scripts)
# ---------------------------------------------------------------------------


def test_text_handler_read_version(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")

    handler = TextVersionHandler()
    assert handler.read_version(str(version_file), "") == "1.2.3"


def test_text_handler_read_version_strips_surrounding_whitespace(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("  1.2.3  \n\n", encoding="utf-8")

    handler = TextVersionHandler()
    assert handler.read_version(str(version_file), "") == "1.2.3"


def test_text_handler_read_version_missing_file_returns_none(tmp_path, capsys):
    handler = TextVersionHandler()
    missing = tmp_path / "does_not_exist"

    assert handler.read_version(str(missing), "") is None
    captured = capsys.readouterr()
    assert "Error reading version from" in captured.out


def test_text_handler_update_version_overwrites_whole_file(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")

    handler = TextVersionHandler()
    assert handler.update_version(str(version_file), "", "2.0.0") is True
    assert version_file.read_text(encoding="utf-8") == "2.0.0\n"


def test_text_handler_update_version_applies_pep440_standard(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")

    handler = TextVersionHandler()
    assert (
        handler.update_version(str(version_file), "", "2026-01-01", version_standard="python")
        is True
    )
    assert version_file.read_text(encoding="utf-8") == "2026.1.1\n"


def test_text_handler_update_version_write_failure(monkeypatch, capsys):
    handler = TextVersionHandler()

    def mock_open(*args, **kwargs):
        raise IOError("disk full")

    monkeypatch.setattr("builtins.open", mock_open)
    result = handler.update_version("VERSION", "", "2.0.0")
    assert result is False
    captured = capsys.readouterr()
    assert "Error updating VERSION: disk full" in captured.out


# ---------------------------------------------------------------------------
# RegexVersionHandler — generic user-supplied-pattern handler (Capability
# Expansion §5.1: Ruby/Rust/Go/etc. with no dedicated handler)
# ---------------------------------------------------------------------------


def test_regex_handler_read_version_ruby_style(tmp_path):
    # Real-world shape: examples/version.rb in this repo.
    version_file = tmp_path / "version.rb"
    version_file.write_text('module MyGem\n  VERSION = "2026.03.08.001"\nend\n', encoding="utf-8")

    handler = RegexVersionHandler()
    result = handler.read_version(str(version_file), "VERSION", pattern=r'VERSION = "(.+?)"')
    assert result == "2026.03.08.001"


def test_regex_handler_update_version_ruby_style_preserves_surrounding_code(tmp_path):
    version_file = tmp_path / "version.rb"
    version_file.write_text('module MyGem\n  VERSION = "2026.03.08.001"\nend\n', encoding="utf-8")

    handler = RegexVersionHandler()
    assert (
        handler.update_version(
            str(version_file), "VERSION", "2026.99.99.001", pattern=r'VERSION = "(.+?)"'
        )
        is True
    )
    assert version_file.read_text(encoding="utf-8") == (
        'module MyGem\n  VERSION = "2026.99.99.001"\nend\n'
    )


def test_regex_handler_read_update_rust_const_style(tmp_path):
    # A second real-world shape, distinct enough from the key=value handlers
    # to prove the pattern isn't accidentally piggybacking on one of them.
    version_file = tmp_path / "version.rs"
    version_file.write_text('pub const VERSION: &str = "1.0.0";\n', encoding="utf-8")

    handler = RegexVersionHandler()
    pattern = r'VERSION: &str = "(.+?)"'
    assert handler.read_version(str(version_file), "VERSION", pattern=pattern) == "1.0.0"
    assert handler.update_version(str(version_file), "VERSION", "2.0.0", pattern=pattern) is True
    assert version_file.read_text(encoding="utf-8") == 'pub const VERSION: &str = "2.0.0";\n'


def test_regex_handler_read_version_missing_pattern(tmp_path, capsys):
    version_file = tmp_path / "version.rb"
    version_file.write_text('VERSION = "1.0.0"\n', encoding="utf-8")

    handler = RegexVersionHandler()
    assert handler.read_version(str(version_file), "VERSION") is None
    captured = capsys.readouterr()
    assert "No 'pattern' provided" in captured.out


def test_regex_handler_update_version_missing_pattern(tmp_path, capsys):
    version_file = tmp_path / "version.rb"
    version_file.write_text('VERSION = "1.0.0"\n', encoding="utf-8")

    handler = RegexVersionHandler()
    assert handler.update_version(str(version_file), "VERSION", "2.0.0") is False
    captured = capsys.readouterr()
    assert "No 'pattern' provided" in captured.out


def test_regex_handler_read_version_invalid_regex(tmp_path, capsys):
    version_file = tmp_path / "version.rb"
    version_file.write_text('VERSION = "1.0.0"\n', encoding="utf-8")

    handler = RegexVersionHandler()
    result = handler.read_version(str(version_file), "VERSION", pattern="[unclosed")
    assert result is None
    captured = capsys.readouterr()
    assert "Invalid regex pattern" in captured.out


def test_regex_handler_no_capture_group_rejected_for_read_and_update(tmp_path, capsys):
    # Regression test: match.span(1) on a pattern with no capture group raises
    # IndexError (not re.error) — this is caught upfront in _compile_pattern
    # for both read_version and update_version, verified here for both paths.
    version_file = tmp_path / "version.rb"
    version_file.write_text('VERSION = "1.0.0"\n', encoding="utf-8")
    handler = RegexVersionHandler()
    no_group_pattern = r'VERSION = ".+?"'

    assert handler.read_version(str(version_file), "VERSION", pattern=no_group_pattern) is None
    assert (
        handler.update_version(str(version_file), "VERSION", "2.0.0", pattern=no_group_pattern)
        is False
    )

    captured = capsys.readouterr()
    assert captured.out.count("must contain exactly one capture group") == 2


def test_regex_handler_read_version_pattern_does_not_match(tmp_path, capsys):
    version_file = tmp_path / "version.rb"
    version_file.write_text('VERSION = "1.0.0"\n', encoding="utf-8")

    handler = RegexVersionHandler()
    result = handler.read_version(str(version_file), "VERSION", pattern=r'NOPE = "(.+?)"')
    assert result is None
    captured = capsys.readouterr()
    assert "Variable 'VERSION' not found" in captured.out


def test_regex_handler_update_version_applies_pep440_standard(tmp_path):
    version_file = tmp_path / "version.rb"
    version_file.write_text('VERSION = "1.0.0"\n', encoding="utf-8")

    handler = RegexVersionHandler()
    assert (
        handler.update_version(
            str(version_file),
            "VERSION",
            "2026-01-01",
            pattern=r'VERSION = "(.+?)"',
            version_standard="python",
        )
        is True
    )
    assert 'VERSION = "2026.1.1"' in version_file.read_text(encoding="utf-8")


def test_update_version_in_files_passes_pattern_to_regex_handler(tmp_path):
    # End-to-end: confirms update_version_in_files() threads the "pattern"
    # config key through to the handler, not just direct handler calls.
    version_file = tmp_path / "version.rb"
    version_file.write_text('VERSION = "1.0.0"\n', encoding="utf-8")

    file_configs = [
        {
            "path": str(version_file),
            "file_type": "regex",
            "variable": "VERSION",
            "pattern": r'VERSION = "(.+?)"',
        }
    ]
    updated = update_version_in_files("2.0.0", file_configs)
    assert updated == [str(version_file)]
    assert 'VERSION = "2.0.0"' in version_file.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Plugin handlers via the "bumpcalver.handlers" entry-point group
# (Capability Expansion §5.2)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_plugin_handler_cache():
    """Ensure _discover_plugin_handlers()'s cache never leaks between tests.

    Only this test class's tests actually patch _iter_plugin_entry_points, but
    clearing unconditionally before *and* after every test in this module is
    cheap and removes any risk of test order affecting results.
    """
    from src.bumpcalver.handlers import _discover_plugin_handlers

    _discover_plugin_handlers.cache_clear()
    yield
    _discover_plugin_handlers.cache_clear()


class _FakePluginHandler(VersionHandler):
    """A minimal concrete VersionHandler used as a stand-in plugin in tests."""

    def read_version(self, file_path: str, variable: str, **kwargs: Any) -> Optional[str]:
        return "plugin-1.0"

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs: Any
    ) -> bool:
        return True


def _make_fake_entry_point(name: str, value: str, load_result):
    """Build a mock.Mock that behaves like importlib.metadata.EntryPoint."""
    ep = mock.Mock()
    ep.name = name
    ep.value = value
    if isinstance(load_result, Exception):
        ep.load.side_effect = load_result
    else:
        ep.load.return_value = load_result
    return ep


def test_get_version_handler_discovers_plugin(monkeypatch):
    ep = _make_fake_entry_point("myformat", "my_pkg.handlers:MyFormatHandler", _FakePluginHandler)
    monkeypatch.setattr("src.bumpcalver.handlers._iter_plugin_entry_points", lambda: [ep])

    handler = get_version_handler("myformat")
    assert isinstance(handler, _FakePluginHandler)
    assert handler.read_version("x", "y") == "plugin-1.0"


def test_available_file_types_includes_builtins_and_plugins(monkeypatch):
    ep = _make_fake_entry_point("myformat", "my_pkg.handlers:MyFormatHandler", _FakePluginHandler)
    monkeypatch.setattr("src.bumpcalver.handlers._iter_plugin_entry_points", lambda: [ep])

    from src.bumpcalver.handlers import available_file_types

    types = available_file_types()
    assert "myformat" in types
    assert "toml" in types
    assert "python" in types
    assert types == sorted(types)


def test_available_file_types_with_no_plugins_installed(monkeypatch):
    monkeypatch.setattr("src.bumpcalver.handlers._iter_plugin_entry_points", lambda: [])

    from src.bumpcalver.handlers import available_file_types

    types = available_file_types()
    assert "myformat" not in types
    assert "toml" in types


def test_plugin_cannot_override_a_builtin_file_type(monkeypatch, capsys):
    # A plugin claiming "toml" must never shadow the real TomlVersionHandler —
    # this is the core trust/safety property of the whole mechanism: installing
    # some unrelated package can't silently change how your existing files
    # are handled.
    ep = _make_fake_entry_point("toml", "evil_pkg:EvilHandler", _FakePluginHandler)
    monkeypatch.setattr("src.bumpcalver.handlers._iter_plugin_entry_points", lambda: [ep])

    # get_version_handler() short-circuits on a match in the built-in registry
    # without ever consulting plugins, so trigger discovery explicitly via
    # available_file_types() to exercise (and see the warning from) the
    # collision-detection path itself.
    from src.bumpcalver.handlers import available_file_types

    types = available_file_types()
    assert "toml" in types

    captured = capsys.readouterr()
    assert "same name as a built-in file_type" in captured.err

    handler = get_version_handler("toml")
    assert isinstance(handler, TomlVersionHandler)


def test_plugin_that_fails_to_load_is_skipped_not_fatal(monkeypatch, capsys):
    ep = _make_fake_entry_point("broken", "nope.module:Nope", ImportError("No module named 'nope'"))
    monkeypatch.setattr("src.bumpcalver.handlers._iter_plugin_entry_points", lambda: [ep])

    with pytest.raises(ValueError, match="Unsupported file type: broken"):
        get_version_handler("broken")

    captured = capsys.readouterr()
    assert "could not load plugin handler 'broken'" in captured.err
    assert "No module named 'nope'" in captured.err


def test_plugin_entry_point_not_a_version_handler_subclass_is_skipped(monkeypatch, capsys):
    ep = _make_fake_entry_point("notahandler", "some_pkg:NotAHandler", str)
    monkeypatch.setattr("src.bumpcalver.handlers._iter_plugin_entry_points", lambda: [ep])

    with pytest.raises(ValueError, match="Unsupported file type: notahandler"):
        get_version_handler("notahandler")

    captured = capsys.readouterr()
    assert "is not a VersionHandler subclass" in captured.err


def test_two_plugins_registering_same_name_first_one_wins(monkeypatch, capsys):
    class _OtherFakeHandler(VersionHandler):
        def read_version(self, file_path: str, variable: str, **kwargs: Any) -> Optional[str]:
            return "other"

        def update_version(
            self, file_path: str, variable: str, new_version: str, **kwargs: Any
        ) -> bool:
            return True

    ep1 = _make_fake_entry_point("dup", "pkg_one:HandlerOne", _FakePluginHandler)
    ep2 = _make_fake_entry_point("dup", "pkg_two:HandlerTwo", _OtherFakeHandler)
    monkeypatch.setattr("src.bumpcalver.handlers._iter_plugin_entry_points", lambda: [ep1, ep2])

    handler = get_version_handler("dup")
    assert isinstance(handler, _FakePluginHandler)

    captured = capsys.readouterr()
    assert "multiple plugins registered for file_type 'dup'" in captured.err


def test_unknown_file_type_with_no_plugins_still_raises(monkeypatch):
    monkeypatch.setattr("src.bumpcalver.handlers._iter_plugin_entry_points", lambda: [])

    with pytest.raises(ValueError, match="Unsupported file type: nope"):
        get_version_handler("nope")


def test_discover_plugin_handlers_is_cached(monkeypatch):
    from src.bumpcalver.handlers import _discover_plugin_handlers

    call_count = {"n": 0}

    def counting_entry_points():
        call_count["n"] += 1
        return []

    monkeypatch.setattr("src.bumpcalver.handlers._iter_plugin_entry_points", counting_entry_points)

    _discover_plugin_handlers()
    _discover_plugin_handlers()
    _discover_plugin_handlers()

    assert call_count["n"] == 1


def test_iter_plugin_entry_points_python310_plus_select_api():
    from src.bumpcalver.handlers import PLUGIN_ENTRY_POINT_GROUP, _iter_plugin_entry_points

    fake_eps = mock.Mock()
    fake_eps.select.return_value = ["sentinel"]

    with mock.patch("src.bumpcalver.handlers.entry_points", return_value=fake_eps):
        result = _iter_plugin_entry_points()

    assert result == ["sentinel"]
    fake_eps.select.assert_called_once_with(group=PLUGIN_ENTRY_POINT_GROUP)


def test_iter_plugin_entry_points_python39_dict_api():
    from src.bumpcalver.handlers import PLUGIN_ENTRY_POINT_GROUP, _iter_plugin_entry_points

    # Python 3.9's entry_points() returns a plain dict with no .select().
    fake_eps = {PLUGIN_ENTRY_POINT_GROUP: ["sentinel"]}

    with mock.patch("src.bumpcalver.handlers.entry_points", return_value=fake_eps):
        result = _iter_plugin_entry_points()

    assert result == ["sentinel"]
