"""Integration-style tests for CLI commands using Typer's test runner."""

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from airtable_cli.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_token(monkeypatch):
    """Ensure a token is always available during tests."""
    monkeypatch.setenv("AIRTABLE_PAT", "patTEST1234567890")


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_auth_show_with_token(monkeypatch):
    monkeypatch.setenv("AIRTABLE_PAT", "patTEST1234567890")
    result = runner.invoke(app, ["auth", "show"])
    assert result.exit_code == 0
    assert "patT" in result.output


def test_bases_list(monkeypatch):
    monkeypatch.setenv("AIRTABLE_PAT", "patTEST")
    mock_response = {"bases": [{"id": "appABC", "name": "My Base", "permissionLevel": "create"}]}
    with patch("airtable_cli.commands.bases.get", return_value=mock_response):
        result = runner.invoke(app, ["--output", "json", "bases", "list"])
    assert result.exit_code == 0
    assert "appABC" in result.output


def test_tables_list(monkeypatch):
    monkeypatch.setenv("AIRTABLE_PAT", "patTEST")
    mock_response = {
        "tables": [
            {"id": "tblXYZ", "name": "Contacts", "fields": [{"id": "fldA", "name": "Name", "type": "singleLineText"}], "views": []}
        ]
    }
    with patch("airtable_cli.commands.tables.get", return_value=mock_response):
        result = runner.invoke(app, ["--output", "json", "--base", "appABC", "tables", "list"])
    assert result.exit_code == 0
    assert "tblXYZ" in result.output


def test_records_list(monkeypatch):
    monkeypatch.setenv("AIRTABLE_PAT", "patTEST")
    mock_response = {
        "records": [
            {"id": "recABC", "fields": {"Name": "Foo"}, "createdTime": "2024-01-01T00:00:00.000Z"}
        ]
    }
    with patch("airtable_cli.commands.records.get", return_value=mock_response):
        result = runner.invoke(app, ["--output", "json", "--base", "appABC", "records", "list", "--table", "tblXYZ"])
    assert result.exit_code == 0
    assert "recABC" in result.output


def test_records_create_fields_json(monkeypatch):
    monkeypatch.setenv("AIRTABLE_PAT", "patTEST")
    mock_response = {"records": [{"id": "recNEW", "fields": {"Name": "Test"}, "createdTime": "2024-01-01"}]}
    with patch("airtable_cli.commands.records.post", return_value=mock_response):
        result = runner.invoke(app, [
            "--no-interactive", "--base", "appABC",
            "records", "create",
            "--table", "tblXYZ",
            "--fields", '{"Name": "Test"}',
        ])
    assert result.exit_code == 0
    assert "recNEW" in result.output


def test_no_token_exits_with_error(monkeypatch):
    monkeypatch.delenv("AIRTABLE_PAT", raising=False)
    monkeypatch.setattr("airtable_cli.config.CONFIG_FILE", "/nonexistent/path/config.toml")
    result = runner.invoke(app, ["--no-interactive", "bases", "list"])
    assert result.exit_code != 0 or "No token" in result.output


def test_records_list_no_base_non_interactive(monkeypatch):
    monkeypatch.setenv("AIRTABLE_PAT", "patTEST")
    result = runner.invoke(app, ["--no-interactive", "records", "list", "--table", "tblXYZ"])
    assert "required" in result.output.lower() or result.exit_code != 0
