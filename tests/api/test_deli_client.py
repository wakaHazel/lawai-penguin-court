import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from apps.api.app.services import deli_client
from apps.api.app.services.deli_client import DeliClient


def test_deli_client_reads_credentials_from_workflow_export_when_env_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    workflow_path = tmp_path / "demo_workflow.json"
    workflow_path.write_text(
        """
        {
          "Nodes": [
            {
              "PluginNodeData": {
                "ToolInputs": {
                  "API": {
                    "URL": "https://openapi.delilegal.com/api/qa/v3/search/queryListLaw"
                  },
                  "Header": [
                    {
                      "ParamName": "appid",
                      "Input": {
                        "UserInputValue": {
                          "Values": ["workflow-app-id"]
                        }
                      }
                    },
                    {
                      "ParamName": "secret",
                      "Input": {
                        "UserInputValue": {
                          "Values": ["workflow-secret"]
                        }
                      }
                    }
                  ]
                }
              }
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    monkeypatch.delenv("DELILEGAL_APP_ID", raising=False)
    monkeypatch.delenv("DELILEGAL_SECRET", raising=False)
    monkeypatch.setenv("DELILEGAL_WORKFLOW_EXPORT_ROOT", str(tmp_path))
    deli_client._discover_deli_credentials.cache_clear()

    client = DeliClient.from_env()

    assert client.app_id == "workflow-app-id"
    assert client.secret == "workflow-secret"
    assert client.is_enabled() is True


def test_deli_client_prefers_env_credentials_over_workflow_export(
    monkeypatch,
    tmp_path: Path,
) -> None:
    workflow_path = tmp_path / "demo_workflow.json"
    workflow_path.write_text(
        """
        {
          "Nodes": [
            {
              "PluginNodeData": {
                "ToolInputs": {
                  "API": {
                    "URL": "https://openapi.delilegal.com/api/qa/v3/search/queryListCase"
                  },
                  "Header": [
                    {
                      "ParamName": "appid",
                      "Input": {
                        "UserInputValue": {
                          "Values": ["workflow-app-id"]
                        }
                      }
                    },
                    {
                      "ParamName": "secret",
                      "Input": {
                        "UserInputValue": {
                          "Values": ["workflow-secret"]
                        }
                      }
                    }
                  ]
                }
              }
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    monkeypatch.setenv("DELILEGAL_APP_ID", "env-app-id")
    monkeypatch.setenv("DELILEGAL_SECRET", "env-secret")
    monkeypatch.setenv("DELILEGAL_WORKFLOW_EXPORT_ROOT", str(tmp_path))
    deli_client._discover_deli_credentials.cache_clear()

    client = DeliClient.from_env()

    assert client.app_id == "env-app-id"
    assert client.secret == "env-secret"
    assert client.is_enabled() is True
