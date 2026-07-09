from src import theme


def test_palette_has_required_keys():
    required = {"bg", "sidebar_bg", "widget_bg", "text", "text_muted", "primary", "border", "hover"}
    assert required <= set(theme.FOREST)


def test_css_is_a_style_block():
    css = theme.build_css()
    assert css.strip().startswith("<style>")
    assert css.strip().endswith("</style>")


def test_css_interpolates_the_palette():
    css = theme.build_css()
    for value in theme.FOREST.values():
        assert value in css


def test_css_loads_both_fonts():
    css = theme.build_css()
    assert "Inter" in css and "Libre+Baskerville" in css
    assert "font-family: 'Libre Baskerville', Georgia, serif" in css


def test_css_leaves_material_icon_font_alone():
    # Setting font-family globally breaks Material icon ligatures.
    assert "[data-testid=\"stIconMaterial\"]" in theme.build_css()


def test_custom_palette_is_used():
    css = theme.build_css({**theme.FOREST, "primary": "#ff0000"})
    assert "#ff0000" in css
