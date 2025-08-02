# tests/test_handlers.py
import json
import xml.etree.ElementTree as ET
from unittest import mock

import pytest
import toml
import yaml
from src.bumpcalver.handlers import (
    DockerfileVersionHandler,
    JsonVersionHandler,
    MakefileVersionHandler,
    PythonVersionHandler,
    TomlVersionHandler,
    XmlVersionHandler,
    YamlVersionHandler,
    PropertiesVersionHandler,
    EnvVersionHandler,
    SetupCfgVersionHandler,
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
    assert (
        "Error updating dummy_file.py: Unable to open file for writing" in captured.out
    )


def test_toml_handler_read_version(monkeypatch):
    handler = TomlVersionHandler()
    toml_content = """
[tool.poetry]
version = "2023-10-10"
"""
    mock_open = mock.mock_open(read_data=toml_content)
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr(
        toml, "load", lambda f: {"tool": {"poetry": {"version": "2023-10-10"}}}
    )

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
    monkeypatch.setattr(toml, "load", lambda f: toml_data)
    dump_mock = mock.Mock()
    monkeypatch.setattr(toml, "dump", dump_mock)

    result = handler.update_version(
        "pyproject.toml", "tool.poetry.version", "2023-10-11"
    )
    assert result is True

    expected_data = {"tool": {"poetry": {"version": "2023-10-11"}}}
    dump_mock.assert_called_once()
    args, kwargs = dump_mock.call_args
    assert args[0] == expected_data


def test_yaml_handler_read_version(monkeypatch):
    handler = YamlVersionHandler()
    yaml_content = """
version: "2023-10-10"
"""
    mock_open = mock.mock_open(read_data=yaml_content)
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr(yaml, "safe_load", lambda f: {"version": "2023-10-10"})

    version = handler.read_version("config.yaml", "version")
    assert version == "2023-10-10"


def test_yaml_handler_update_version(monkeypatch):
    handler = YamlVersionHandler()
    yaml_content = """
version: "2023-10-10"
"""
    mock_open = mock.mock_open(read_data=yaml_content)
    monkeypatch.setattr("builtins.open", mock_open)
    yaml_data = {"version": "2023-10-10"}
    monkeypatch.setattr(yaml, "safe_load", lambda f: yaml_data)
    dump_mock = mock.Mock()
    monkeypatch.setattr(yaml, "safe_dump", dump_mock)

    result = handler.update_version("config.yaml", "version", "2023-10-11")
    assert result is True

    expected_data = {"version": "2023-10-11"}
    dump_mock.assert_called_once_with(expected_data, mock.ANY)


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
    handler = YamlVersionHandler()

    # Simulate an exception during yaml.safe_load
    def mock_yaml_load(f):
        raise yaml.YAMLError("Malformed YAML")

    monkeypatch.setattr("yaml.safe_load", mock_yaml_load)
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
    monkeypatch.setattr(ET, "parse", lambda f: mock_tree)

    result = handler.update_version("config.xml", "version", "2023-10-11")
    assert result is True

    assert mock_element.text == "2023-10-11"
    mock_tree.write.assert_called_once_with("config.xml")


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
    def mock_et_parse(file):
        raise ET.ParseError("Malformed XML")

    monkeypatch.setattr("xml.etree.ElementTree.parse", mock_et_parse)

    result = handler.update_version("config.xml", "version", "2023-10-11")
    assert result is False

    captured = capsys.readouterr()
    assert "Error updating config.xml: Malformed XML" in captured.out


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

    result = handler.update_version(
        "Dockerfile", "VERSION", "2023-10-11", directive="ARG"
    )
    assert result is True

    handle = mock_open()
    handle.write.assert_called_once()
    written_content = handle.write.call_args[0][0]
    assert "ARG VERSION=2023-10-11" in written_content


def test_dockerfile_handler_update_version_invalid_directive(capsys):
    handler = DockerfileVersionHandler()

    result = handler.update_version(
        "Dockerfile", "VERSION", "2023-10-11", directive="INVALID"
    )
    assert result is False

    captured = capsys.readouterr()
    assert (
        "Invalid or missing directive for variable 'VERSION' in Dockerfile."
        in captured.out
    )


def test_dockerfile_handler_read_version_invalid_directive(capsys):
    handler = DockerfileVersionHandler()

    version = handler.read_version("Dockerfile", "VERSION", directive="INVALID")
    assert version is None

    captured = capsys.readouterr()
    assert (
        "Invalid or missing directive for variable 'VERSION' in Dockerfile."
        in captured.out
    )


def test_dockerfile_handler_update_version_exception(monkeypatch, capsys):
    handler = DockerfileVersionHandler()

    # Simulate an exception during file reading
    def mock_open(*args, **kwargs):
        raise IOError("Unable to open file")

    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version(
        "Dockerfile", "VERSION", "2023-10-11", directive="ARG"
    )
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
    assert (
        "Error reading version from nonexistent_file.py: Unable to open file"
        in captured.out
    )


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
        raise handlers.toml.TomlDecodeError("Malformed TOML", "", 0)

    # Monkeypatch the 'toml.load' function in the handlers module
    monkeypatch.setattr(handlers.toml, "load", mock_toml_load)

    mock_open = mock.mock_open()
    monkeypatch.setattr("builtins.open", mock_open)

    version = handler.read_version("pyproject.toml", "tool.poetry.version")
    assert version is None

    captured = capsys.readouterr()
    assert "Error reading version from pyproject.toml: Malformed TOML" in captured.out


def test_toml_handler_update_version_exception(monkeypatch, capsys):
    from src.bumpcalver import handlers

    handler = handlers.TomlVersionHandler()

    # Simulate an exception during toml.load
    def mock_toml_load(f):
        raise handlers.toml.TomlDecodeError("Malformed TOML", "", 0)

    monkeypatch.setattr(handlers.toml, "load", mock_toml_load)
    mock_open = mock.mock_open()
    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.update_version(
        "pyproject.toml", "tool.poetry.version", "2023-10-11"
    )
    assert result is False

    captured = capsys.readouterr()
    assert "Error updating pyproject.toml: Malformed TOML" in captured.out


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
    monkeypatch.setattr(
        toml, "load", lambda f: {"tool": {"poetry": {"name": "example"}}}
    )

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
    monkeypatch.setattr(toml, "load", lambda f: toml_data)
    dump_mock = mock.Mock()
    monkeypatch.setattr(toml, "dump", dump_mock)

    result = handler.update_version(
        "pyproject.toml", "tool.poetry.version", "2023-10-11"
    )
    assert result is False

    captured = capsys.readouterr()
    assert "Variable 'tool.poetry.version' not found in pyproject.toml" in captured.out


def test_yaml_handler_read_version_variable_not_found(monkeypatch, capsys):
    handler = YamlVersionHandler()
    yaml_content = """
version: "2023-10-10"
"""
    mock_open = mock.mock_open(read_data=yaml_content)
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr(yaml, "safe_load", lambda f: {"version": "2023-10-10"})

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
        ET, "parse", lambda f: ET.ElementTree(ET.fromstring(xml_content))
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

    result = handler.update_version(
        "Dockerfile", "VERSION", "2023-10-11", directive="ARG"
    )
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

    result = handler.update_version("sonar-project.properties", "sonar.projectVersion", "2025-08-01-001")
    assert result is True

    handle = mock_open()
    handle.writelines.assert_called_once()
    written_lines = handle.writelines.call_args[0][0]
    # Check that the version line was updated
    version_line_found = any("sonar.projectVersion=2025-08-01-001" in line for line in written_lines)
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

    result = handler.update_version("sonar-project.properties", "sonar.projectVersion", "2025-08-01-001")
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

    result = handler.update_version("sonar-project.properties", "sonar.projectVersion", "2025-08-01-001")
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
    mock_config.sections.return_value = ['metadata', 'options']
    mock_config.__contains__ = lambda self, key: key == 'metadata'
    mock_config.__getitem__ = lambda self, key: {'version': '0.1.0'} if key == 'metadata' else {}

    mock_configparser = mock.Mock()
    mock_configparser.ConfigParser.return_value = mock_config

    monkeypatch.setattr("configparser.ConfigParser", mock_configparser.ConfigParser)

    version = handler.read_version("setup.cfg", "metadata.version")
    assert version == "0.1.0"


def test_setup_cfg_handler_read_version_simple_key(monkeypatch):
    """Test reading version from setup.cfg using simple key (no dot notation)."""
    handler = SetupCfgVersionHandler()

    # Mock configparser
    mock_section = {'version': '0.1.0', 'name': 'test'}
    mock_config = mock.Mock()
    mock_config.sections.return_value = ['metadata']
    mock_config.__getitem__ = lambda self, key: mock_section if key == 'metadata' else {}

    mock_configparser = mock.Mock()
    mock_configparser.ConfigParser.return_value = mock_config

    monkeypatch.setattr("configparser.ConfigParser", mock_configparser.ConfigParser)

    version = handler.read_version("setup.cfg", "version")
    assert version == "0.1.0"


def test_setup_cfg_handler_update_version(monkeypatch):
    """Test updating version in a setup.cfg file."""
    handler = SetupCfgVersionHandler()

    # Mock configparser
    mock_section = {'version': '0.1.0'}
    mock_config = mock.Mock()
    mock_config.sections.return_value = ['metadata']
    mock_config.__contains__ = lambda self, key: key == 'metadata'
    mock_config.__getitem__ = lambda self, key: mock_section if key == 'metadata' else {}
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
    assert mock_section['version'] == "2025-08-01-001"
    mock_config.write.assert_called_once()


def test_setup_cfg_handler_read_version_not_found(monkeypatch):
    """Test reading a non-existent configuration key."""
    handler = SetupCfgVersionHandler()

    # Mock configparser
    mock_config = mock.Mock()
    mock_config.sections.return_value = ['metadata']
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

    mock_config.add_section.assert_called_with('metadata')


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
    mock_section = {'version': '0.1.0', 'name': 'test'}
    mock_config = mock.Mock()
    mock_config.sections.return_value = ['metadata', 'options']
    mock_config.__contains__ = lambda self, key: False  # No dot notation
    mock_config.__getitem__ = lambda self, key: mock_section if key == 'metadata' else {}
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
    assert mock_section['version'] == "2025-08-01-001"
    mock_config.write.assert_called_once()


def test_setup_cfg_handler_update_version_simple_key_not_found_add_to_metadata(monkeypatch):
    """Test updating version using simple key that doesn't exist - add to metadata section."""
    handler = SetupCfgVersionHandler()

    # Mock configparser - version doesn't exist in any section, metadata section exists
    mock_metadata_section = {'name': 'test'}
    mock_config = mock.Mock()
    mock_config.sections.return_value = ['metadata', 'options']
    mock_config.__contains__ = lambda self, key: key == 'metadata'  # metadata exists
    mock_config.__getitem__ = lambda self, key: mock_metadata_section if key == 'metadata' else {}
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
    assert mock_metadata_section['version'] == "2025-08-01-001"
    mock_config.write.assert_called_once()


def test_setup_cfg_handler_update_version_simple_key_no_metadata_section(monkeypatch):
    """Test updating version using simple key when metadata section doesn't exist."""
    handler = SetupCfgVersionHandler()

    # Mock configparser - no metadata section exists
    mock_metadata_section = {}
    mock_config = mock.Mock()
    mock_config.sections.return_value = ['options']
    mock_config.__contains__ = lambda self, key: False  # metadata doesn't exist
    mock_config.__getitem__ = lambda self, key: mock_metadata_section if key == 'metadata' else {}
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
    mock_config.add_section.assert_called_with('metadata')
    assert mock_metadata_section['version'] == "2025-08-01-001"
    mock_config.write.assert_called_once()


def test_setup_cfg_handler_update_dot_notation_variable():
    """Test _update_dot_notation_variable helper method."""
    import configparser
    from src.bumpcalver.handlers import SetupCfgVersionHandler

    handler = SetupCfgVersionHandler()
    config = configparser.ConfigParser()

    # Test with existing section
    config.add_section('metadata')
    result = handler._update_dot_notation_variable(config, "metadata.version", "1.0.0")
    assert result is True
    assert config['metadata']['version'] == "1.0.0"

    # Test with non-existing section
    result = handler._update_dot_notation_variable(config, "tool.version", "2.0.0")
    assert result is True
    assert config['tool']['version'] == "2.0.0"


def test_setup_cfg_handler_update_simple_variable():
    """Test _update_simple_variable helper method."""
    import configparser
    from src.bumpcalver.handlers import SetupCfgVersionHandler

    handler = SetupCfgVersionHandler()
    config = configparser.ConfigParser()

    # Test with existing variable in existing section - should return True
    config.add_section('metadata')
    config['metadata']['version'] = "0.1.0"
    result = handler._update_simple_variable(config, "version", "1.0.0")
    assert result is True  # Found and updated existing variable
    assert config['metadata']['version'] == "1.0.0"

    # Test with non-existing variable - should return False but still create the variable
    config2 = configparser.ConfigParser()
    config2.add_section('options')
    result = handler._update_simple_variable(config2, "version", "2.0.0")
    assert result is False  # Variable was not found, so it was created
    assert config2['metadata']['version'] == "2.0.0"  # But variable was still created
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
    result = handler._format_version_with_standard("2024-01-15", version_standard="default", other_param="test")
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
        "# Another comment"
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

    result = handler._handle_read_operation("test_file.txt", operation_func, "VERSION")
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

    result = handler._handle_read_operation("test_file.txt", operation_func, "VERSION")
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

    pattern = re.compile(r'VERSION=(.+)')

    def replacement_func(match):
        return "VERSION=2.0.0"

    result = handler._handle_regex_update("test_file.txt", pattern, replacement_func, "2.0.0", "VERSION")
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

    pattern = re.compile(r'VERSION=(.+)')

    def replacement_func(match):
        return "VERSION=2.0.0"

    result = handler._handle_regex_update("test_file.txt", pattern, replacement_func, "2.0.0", "VERSION")
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

    pattern = re.compile(r'VERSION=(.+)')

    def replacement_func(match):
        return "VERSION=2.0.0"

    custom_message = "Custom variable not found message"
    result = handler._handle_regex_update("test_file.txt", pattern, replacement_func, "2.0.0", "VERSION", custom_message)
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

    pattern = re.compile(r'VERSION=(.+)')

    def replacement_func(match):
        return "VERSION=2.0.0"

    result = handler._handle_regex_update("test_file.txt", pattern, replacement_func, "2.0.0", "VERSION")
    assert result is False

    captured = capsys.readouterr()
    assert "Error updating test_file.txt: Unable to read file" in captured.out
