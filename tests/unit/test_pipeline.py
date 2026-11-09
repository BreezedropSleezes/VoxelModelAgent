from pathlib import Path

from svox.export import export_all
from svox.generate import generate
from svox.normalize import normalize_job
from svox.stylize import stylize
from svox.validate import validate


def test_carrot_produces_nonempty_vox(tmp_path: Path) -> None:
    job = normalize_job(theme="carrot", seed=42, formats=["vox", "qb", "glb"], job_id="t-carrot")
    vol = stylize(generate(job), job)
    assert vol.count_filled() > 0
    written = export_all(vol, job, tmp_path)
    assert written["vox"].stat().st_size > 0
    assert written["vox"].read_bytes()[:4] == b"VOX "
    assert written["qb"].stat().st_size > 0
    assert written["glb"].stat().st_size > 0
    report = validate(vol, job, written)
    assert report.ok


def test_rejects_building_theme() -> None:
    try:
        normalize_job(theme="cottage")
        assert False, "expected ValueError"
    except ValueError as e:
        assert "rejected" in str(e).lower() or "architectural" in str(e).lower()
