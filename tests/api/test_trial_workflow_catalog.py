import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from apps.api.app.orchestrators.workflow_catalog import get_civil_trial_workflow


def test_civil_trial_workflow_catalog_contains_fixed_mainline() -> None:
    workflow = get_civil_trial_workflow()

    assert len(workflow.nodes) == 14
    assert [node.node_id for node in workflow.nodes[:6]] == [
        "N01",
        "N02",
        "N03",
        "N04",
        "N05",
        "N06",
    ]
    assert workflow.checkpoint_node_ids == ["N07", "N08", "N10", "N11"]
