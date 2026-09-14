# Golden samples

Frozen `<main>` fragments for the theme render tests (`test_theme_render.py`),
compared through `conftest.py`'s `assert_golden` fixture.

**Empty on purpose.** A property assertion says what it means ("the signature
is gone", "the turn is in `section.user`") and survives a palette change or a
Hugo minor release; a frozen blob only says "something changed". Samples are
for the case a property honestly cannot express — not the default.

When one is needed:

```
cd tools/others/python && python3 -m pytest --update-golden
```

That writes the file, skips the test, and leaves the sample for you to read
before committing it. Each sample's first line carries the Hugo version that
produced it, so a diff after a Hugo bump says so instead of leaving you to
guess. Building samples needs Hugo on PATH; without one the whole file skips.
