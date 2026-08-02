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
