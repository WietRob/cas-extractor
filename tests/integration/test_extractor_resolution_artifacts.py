"""
Artifact-Level Integration Tests

Runs extract_python.py against fixtures and validates YAML evidence output.
Tests that the resolution engine works correctly in the full extraction pipeline.
"""

import subprocess
import shutil
from pathlib import Path

import pytest
import yaml


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "extractor"


def run_extractor(
    fixture_dir: Path, out_dir: Path, extra_args: list[str] | None = None
) -> subprocess.CompletedProcess:
    args = [
        "python3",
        "extract_python.py",
        "--repo-root",
        str(fixture_dir),
        "--repo-name",
        "test://fixture",
        "--revision",
        "test:HEAD",
        "--out",
        str(out_dir),
        "--enable-v050-resolution-engine",
        "true",
        "--enable-h25-self-attr-noninit",
        "true",
        "--enable-h26-self-attr-intermethod",
        "true",
        "--enable-h27-self-attr-transitive",
        "true",
        "--enable-h28-factory-return",
        "true",
        "--v050-emit-resolution-trace",
        "true",
    ]
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(args, capture_output=True, text=True)


def load_callgraph_yaml(out_dir: Path) -> list[dict]:
    yaml_files = list(out_dir.glob("EVID-py.callgraph-*.yaml"))
    if not yaml_files:
        return []
    edges = []
    for yf in yaml_files:
        with open(yf) as f:
            data = yaml.safe_load(f)
        edges.extend(data.get("payload", {}).get("edges", []))
    return edges


class TestExtractorGateAH27:
    """Gate A: H2.6/H2.7 Inter-Method Self-Attr Propagation"""

    @pytest.fixture
    def extractor_output(self, tmp_path):
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        shutil.copy(FIXTURES_DIR / "gate_a_h27.py", fixture_dir / "gate_a_h27.py")

        result = run_extractor(fixture_dir, tmp_path)
        assert result.returncode == 0, f"Extractor failed: {result.stderr}"
        yield tmp_path

    def test_extractor_produces_yaml_output(self, extractor_output):
        yaml_files = list(extractor_output.glob("EVID-py.callgraph-*.yaml"))
        assert len(yaml_files) > 0, "No callgraph YAML produced"

    def test_h27_resolves_client_send(self, extractor_output):
        edges = load_callgraph_yaml(extractor_output)
        client_send_edges = [e for e in edges if "send" in e.get("to", "")]
        assert len(client_send_edges) > 0, "No edges to Client.send found"

        send_edge = client_send_edges[0]
        assert "Client" in send_edge.get("to", ""), (
            f"Expected Client.send, got {send_edge.get('to')}"
        )

    def test_h27_resolves_client_close(self, extractor_output):
        edges = load_callgraph_yaml(extractor_output)
        close_edges = [e for e in edges if "close" in e.get("to", "")]
        assert len(close_edges) > 0, "No edges to Client.close found"


class TestExtractorGateBH28:
    """Gate B: H2.8 Factory Return Inference"""

    @pytest.fixture
    def extractor_output(self, tmp_path):
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        shutil.copy(FIXTURES_DIR / "gate_b_h28.py", fixture_dir / "gate_b_h28.py")

        result = run_extractor(fixture_dir, tmp_path)
        assert result.returncode == 0, f"Extractor failed: {result.stderr}"
        yield tmp_path

    def test_extractor_produces_yaml_output(self, extractor_output):
        yaml_files = list(extractor_output.glob("EVID-py.callgraph-*.yaml"))
        assert len(yaml_files) > 0, "No callgraph YAML produced"

    def test_h28_resolves_factory_return(self, extractor_output):
        edges = load_callgraph_yaml(extractor_output)
        build_edges = [e for e in edges if "build" in e.get("to", "")]
        assert len(build_edges) > 0, "No edges to Builder.build found"


class TestExtractorGateCQualified:
    """Gate C: qualified_attr Resolution"""

    @pytest.fixture
    def extractor_output(self, tmp_path):
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        shutil.copy(
            FIXTURES_DIR / "gate_c_qualified.py", fixture_dir / "gate_c_qualified.py"
        )

        result = run_extractor(fixture_dir, tmp_path)
        assert result.returncode == 0, f"Extractor failed: {result.stderr}"
        yield tmp_path

    def test_extractor_produces_yaml_output(self, extractor_output):
        yaml_files = list(extractor_output.glob("EVID-py.callgraph-*.yaml"))
        assert len(yaml_files) > 0, "No callgraph YAML produced"

    def test_qualified_attr_resolves_ast_walk(self, extractor_output):
        edges = load_callgraph_yaml(extractor_output)
        ast_walk_edges = [
            e
            for e in edges
            if "ast.walk" in e.get("to", "") or "walk" in e.get("to", "")
        ]
        assert len(ast_walk_edges) > 0, "No edges to ast.walk found"


class TestExtractorDeterminism:
    """Tests for deterministic extractor output"""

    def test_same_fixture_same_edge_count(self, tmp_path):
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        shutil.copy(FIXTURES_DIR / "gate_a_h27.py", fixture_dir / "gate_a_h27.py")

        out1 = tmp_path / "run1"
        out2 = tmp_path / "run2"
        out1.mkdir()
        out2.mkdir()

        run_extractor(fixture_dir, out1)
        run_extractor(fixture_dir, out2)

        edges1 = load_callgraph_yaml(out1)
        edges2 = load_callgraph_yaml(out2)

        assert len(edges1) == len(edges2), (
            f"Edge count differs: {len(edges1)} vs {len(edges2)}"
        )

    def test_same_fixture_same_targets(self, tmp_path):
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        shutil.copy(FIXTURES_DIR / "gate_b_h28.py", fixture_dir / "gate_b_h28.py")

        out1 = tmp_path / "run1"
        out2 = tmp_path / "run2"
        out1.mkdir()
        out2.mkdir()

        run_extractor(fixture_dir, out1)
        run_extractor(fixture_dir, out2)

        edges1 = load_callgraph_yaml(out1)
        edges2 = load_callgraph_yaml(out2)

        targets1 = sorted(e.get("to", "") for e in edges1)
        targets2 = sorted(e.get("to", "") for e in edges2)

        assert targets1 == targets2, f"Targets differ: {targets1} vs {targets2}"
