import runpy
from pathlib import Path


def test_run_all_prints_key_numbers(capsys):
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "run_all.py"), run_name="__main__")
    out = capsys.readouterr().out
    for s in ("с кошельком 181 ₽", "с кошельком 198 ₽", "с кошельком 856 ₽",
              "красивая 189 ₽", "красивая 199 ₽", "красивая 849 ₽", "= 194,4 ₽", "1 226,4"):
        assert s in out
