from recordkit import config


def _mk(p):
    p.mkdir(parents=True, exist_ok=True)


def test_resolve_from_hugo_config(tmp_path):
    hugo = tmp_path / "site" / "hugo"
    _mk(hugo)
    (hugo / "hugo.yaml").write_text("contentDir: ../records\n")
    assert config.resolve_records_dir(tmp_path) == (tmp_path / "site" / "records").resolve()


def test_content_dir_default_when_absent(tmp_path):
    hugo = tmp_path / "hugo"
    _mk(hugo)
    (hugo / "hugo.yaml").write_text("baseURL: /\n")
    assert config.resolve_records_dir(tmp_path) == (tmp_path / "records").resolve()


def test_resolve_nested_tools_hugo_layout(tmp_path):
    hugo = tmp_path / "project" / "site" / "tools" / "hugo"
    _mk(hugo)
    (hugo / "hugo.yaml").write_text("contentDir: ../../records\n")
    assert config.resolve_records_dir(tmp_path) == \
        (tmp_path / "project" / "site" / "records").resolve()


def test_fallback_records_dir(tmp_path):
    _mk(tmp_path / "records")
    assert config.resolve_records_dir(tmp_path) == (tmp_path / "records").resolve()


def test_fallback_docs(tmp_path):
    _mk(tmp_path / "docs")
    assert config.resolve_records_dir(tmp_path) == (tmp_path / "docs" / "records").resolve()


def test_none_defaults_to_records(tmp_path):
    assert config.resolve_records_dir(tmp_path) == (tmp_path / "records").resolve()


def test_shallowest_config_wins(tmp_path):
    top = tmp_path / "hugo"
    _mk(top)
    (top / "hugo.yaml").write_text("contentDir: ../records\n")
    deep = tmp_path / "sub" / "hugo"
    _mk(deep)
    (deep / "hugo.yaml").write_text("contentDir: ../content\n")
    assert config.resolve_records_dir(tmp_path) == (tmp_path / "records").resolve()


def test_read_theme_default_when_absent(tmp_path):
    p = tmp_path / "hugo.yaml"
    p.write_text("contentDir: ../records\n")
    assert config.read_theme(p) == "Fuglekasse"


def test_read_theme_reads_the_value(tmp_path):
    p = tmp_path / "hugo.yaml"
    p.write_text("theme: Postkasse\n")
    assert config.read_theme(p) == "Postkasse"
    p.write_text('theme: "Postkasse"\n')
    assert config.read_theme(p) == "Postkasse"
    p.write_text("theme: Postkasse  # growth\n")
    assert config.read_theme(p) == "Postkasse"


def test_read_theme_ignores_commented_lines(tmp_path):
    """The shipped hugo.yaml shape: active Fuglekasse, commented Postkasse."""
    p = tmp_path / "hugo.yaml"
    p.write_text("# theme: Postkasse\ntheme: Fuglekasse\n")
    assert config.read_theme(p) == "Fuglekasse"
    p.write_text("# theme: Postkasse\n")
    assert config.read_theme(p) == "Fuglekasse"


def test_read_theme_default_parameter(tmp_path):
    p = tmp_path / "hugo.yaml"
    p.write_text("baseURL: /\n")
    assert config.read_theme(p, default="") == ""


# --- gap 8: the last rung is an assumption, and says so -----------------------
#
# resolve_records_dir returns `<start>/records` whether or not it exists, which is
# correct for a fresh clone about to create it and a lie everywhere else. The path
# does not change; what is new is that a caller can ask which answer it got.

def test_discovery_reports_a_contentdir_as_found(tmp_path):
    hugo = tmp_path / "site" / "hugo"
    hugo.mkdir(parents=True)
    (hugo / "hugo.yaml").write_text("contentDir: ../records\n", encoding="utf-8")
    assert config.discover_records_dir(tmp_path) == ((tmp_path / "site" / "records").resolve(), True)


def test_discovery_reports_a_records_dir_on_disk_as_found(tmp_path):
    (tmp_path / "records").mkdir()
    assert config.discover_records_dir(tmp_path) == ((tmp_path / "records").resolve(), True)


def test_discovery_reports_a_docs_dir_on_disk_as_found(tmp_path):
    """The docs/ rung is a discovery even though docs/records/ itself need not exist yet."""
    (tmp_path / "docs").mkdir()
    assert config.discover_records_dir(tmp_path) == \
        ((tmp_path / "docs" / "records").resolve(), True)


def test_discovery_admits_the_last_rung_is_an_assumption(tmp_path):
    """Nothing in the checkout points anywhere: the path is the convention, not a finding."""
    path, discovered = config.discover_records_dir(tmp_path)
    assert path == (tmp_path / "records").resolve()
    assert discovered is False
    assert not path.exists()


def test_resolve_records_dir_is_unchanged_by_the_split(tmp_path):
    """Every existing caller keeps the old one-value answer, assumption included."""
    assert config.resolve_records_dir(tmp_path) == config.discover_records_dir(tmp_path)[0]
    (tmp_path / "records").mkdir()
    assert config.resolve_records_dir(tmp_path) == config.discover_records_dir(tmp_path)[0]
