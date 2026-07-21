import pytest

from recordkit import myname


def test_save_writes_note_and_pointer(tmp_path):
    r = myname.save("Ada Lovelace", memory_dir=tmp_path)
    assert r == {"name": "Ada Lovelace", "memory_dir": str(tmp_path)}
    assert "The user's name is Ada Lovelace." in (tmp_path / "user-name.md").read_text()
    assert (tmp_path / "MEMORY.md").read_text().count("user-name.md") == 1


def test_save_pointer_is_idempotent(tmp_path):
    myname.save("Ada", memory_dir=tmp_path)
    myname.save("Grace", memory_dir=tmp_path)
    ptr = (tmp_path / "MEMORY.md").read_text()
    assert ptr.count("[User's name](user-name.md)") == 1
    assert "the user is Grace" in ptr


def test_empty_name_rejected(tmp_path):
    with pytest.raises(ValueError):
        myname.save("   ", memory_dir=tmp_path)
