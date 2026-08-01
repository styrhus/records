from pathlib import Path

from recordkit import export

RECORD = """\
---
title: A conversation
date: 2026-07-06T23:22:00+01:00
tags: [bicycles, repair]
---

## Human (tb4)

Look at **this** and see [the site](https://example.org).

## Assistant

Here is a list:

- one
- two

```python
print("hi")
```

![the whiteboard](image.png)

— mistral:latest
"""


def _repo(tmp_path, records=None):
    hugo = tmp_path / "tools" / "hugo"
    hugo.mkdir(parents=True)
    (hugo / "hugo.yaml").write_text("contentDir: ../../records\n", encoding="utf-8")
    rec = tmp_path / "records"
    rec.mkdir()
    for name, text in (records or {"2026-07-06_23-22.md": RECORD}).items():
        p = rec / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path


def test_turns_become_labelled_plain_text(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "export"
    export.export(repo, out)
    text = (out / "2026-07-06_23-22.txt").read_text()

    assert "HUMAN (TB4) SAID:" in text
    assert "ASSISTANT SAID:" in text
    assert "## Human" not in text and "## Assistant" not in text


def test_no_markdown_syntax_survives(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "export"
    export.export(repo, out)
    text = (out / "2026-07-06_23-22.txt").read_text()

    assert "**this**" not in text and "this" in text
    assert "the site <https://example.org>" in text
    assert "[image: image.png]" in text and "![" not in text
    assert "```" not in text and '    print("hi")' in text
    assert "  * one" in text


def test_signature_says_what_it_is(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "export"
    export.export(repo, out)
    text = (out / "2026-07-06_23-22.txt").read_text()
    assert "[written by the AI model: mistral:latest]" in text
    assert "— mistral:latest" not in text


def test_header_block_carries_title_date_tags(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "export"
    export.export(repo, out)
    text = (out / "2026-07-06_23-22.txt").read_text()
    assert text.startswith("=" * 76 + "\nA conversation\n")
    assert "Date:  2026-07-06T23:22:00+01:00" in text
    assert "Tags:  bicycles, repair" in text
    assert "title: A conversation" not in text  # the frontmatter block itself never appears
    assert "tags: [bicycles" not in text


def test_legacy_user_heading_reads_as_human(tmp_path):
    repo = _repo(tmp_path, {"a.md": "---\ntitle: T\n---\n\n## User\n\nhi\n"})
    out = tmp_path / "export"
    export.export(repo, out)
    assert "HUMAN SAID:" in (out / "a.txt").read_text()


def test_tree_mirrors_the_records_layout(tmp_path):
    repo = _repo(tmp_path, {"3/a.md": "---\ntitle: A\ndate: 2026-01-01\n---\n\nx\n",
                            "b.md": "---\ntitle: B\ndate: 2026-02-01\n---\n\ny\n"})
    out = tmp_path / "export"
    result = export.export(repo, out)
    assert (out / "3" / "a.txt").is_file() and (out / "b.txt").is_file()
    assert result["records"] == 2


def test_bundle_exports_under_its_folder_name(tmp_path):
    repo = _repo(tmp_path, {"2026-07-06_23-30/index.md": "---\ntitle: Bundled\n---\n\nx\n"})
    out = tmp_path / "export"
    export.export(repo, out)
    assert (out / "2026-07-06_23-30.txt").is_file()


def test_single_file_is_chronological_with_contents(tmp_path):
    repo = _repo(tmp_path, {
        "late.md": "---\ntitle: Later\ndate: 2026-05-01\n---\n\nsecond\n",
        "early.md": "---\ntitle: Earlier\ndate: 2026-01-01\n---\n\nfirst\n",
    })
    out = tmp_path / "all.txt"
    result = export.export(repo, out, single=True)
    text = out.read_text()

    assert result["records"] == 2 and result["files"] == [str(out)]
    assert "CONTENTS" in text
    assert text.index("1. Earlier") < text.index("2. Later")
    assert text.index("first") < text.index("second")
    assert "2 conversations, oldest first." in text


def test_single_file_explains_itself_without_the_repo(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "all.txt"
    export.export(repo, out, single=True)
    text = out.read_text()
    assert "Nothing needs to be installed to read this file." in text
    assert "names the model that produced the reply above" in text


def test_drafts_and_special_pages_are_skipped(tmp_path):
    repo = _repo(tmp_path, {
        "a.md": "---\ntitle: A\ndate: 2026-01-01\n---\n\nkeep\n",
        "d.md": "---\ntitle: D\ndraft: true\ndate: 2026-01-02\n---\n\ndrop\n",
        "_index.md": "---\ntitle: Home\n---\n\ndrop\n",
        "LICENSE.md": "---\ntitle: License\n---\n\ndrop\n",
        "404.md": "---\ntitle: Gone\n---\n\ndrop\n",
    })
    out = tmp_path / "export"
    result = export.export(repo, out)
    assert result["records"] == 1
    assert (out / "a.txt").is_file()


def test_filename_timestamp_is_the_date_fallback(tmp_path):
    repo = _repo(tmp_path, {"2026-07-06_23-22.md": "---\ntitle: T\n---\n\nx\n"})
    out = tmp_path / "export"
    export.export(repo, out)
    assert "Date:  2026-07-06 23:22" in (out / "2026-07-06_23-22.txt").read_text()


def test_untitled_record_falls_back_to_its_name(tmp_path):
    repo = _repo(tmp_path, {"2026-07-06_23-22.md": "no frontmatter here\n"})
    out = tmp_path / "export"
    export.export(repo, out)
    text = (out / "2026-07-06_23-22.txt").read_text()
    assert "2026-07-06_23-22" in text and "no frontmatter here" in text
