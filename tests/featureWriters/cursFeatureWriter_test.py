from textwrap import dedent

import pytest

from ufo2ft.featureWriters.cursFeatureWriter import CursFeatureWriter

from . import FeatureWriterTest


@pytest.fixture
def testufo(FontClass):
    ufo = FontClass()
    ufo.newGlyph("a").appendAnchor({"name": "exit", "x": 100, "y": 200})
    glyph = ufo.newGlyph("b")
    glyph.appendAnchor({"name": "entry", "x": 0, "y": 200})
    glyph.appendAnchor({"name": "exit", "x": 111, "y": 200})
    ufo.newGlyph("c").appendAnchor({"name": "entry", "x": 100, "y": 200})
    return ufo


class CursFeatureWriterTest(FeatureWriterTest):

    FeatureWriter = CursFeatureWriter

    def test_curs_feature(self, testufo):
        generated = self.writeFeatures(testufo)

        assert str(generated) == dedent(
            """\
            feature curs {
                lookup curs {
                    lookupflag RightToLeft IgnoreMarks;
                    pos cursive a <anchor NULL> <anchor 100 200>;
                    pos cursive b <anchor 0 200> <anchor 111 200>;
                    pos cursive c <anchor 100 200> <anchor NULL>;
                } curs;

            } curs;
            """
        )

    def test_curs_feature_LTR(self, testufo):
        testufo["a"].unicode = ord("a")
        testufo["b"].unicode = ord("b")
        testufo["c"].unicode = ord("c")
        generated = self.writeFeatures(testufo)

        assert str(generated) == dedent(
            """\
            feature curs {
                lookup curs_ltr {
                    lookupflag IgnoreMarks;
                    pos cursive a <anchor NULL> <anchor 100 200>;
                    pos cursive b <anchor 0 200> <anchor 111 200>;
                    pos cursive c <anchor 100 200> <anchor NULL>;
                } curs_ltr;

            } curs;
            """
        )

    def test_curs_feature_mixed(self, testufo):
        testufo["a"].unicode = ord("a")
        testufo["b"].unicode = ord("b")
        testufo["c"].unicode = ord("c")
        glyph = testufo.newGlyph("a.swsh")
        glyph.appendAnchor({"name": "entry", "x": 100, "y": 200})
        glyph = testufo.newGlyph("alef")
        glyph.unicode = 0x0627
        glyph = testufo.newGlyph("alef.fina")
        glyph.appendAnchor({"name": "entry", "x": 300, "y": 10})
        glyph = testufo.newGlyph("meem")
        glyph.unicode = 0x0645
        glyph = testufo.newGlyph("meem.init")
        glyph.appendAnchor({"name": "exit", "x": 0, "y": 10})
        glyph = testufo.newGlyph("meem.medi")
        glyph.appendAnchor({"name": "entry", "x": 500, "y": 10})
        glyph.appendAnchor({"name": "exit", "x": 0, "y": 10})
        glyph = testufo.newGlyph("meem.fina")
        glyph.appendAnchor({"name": "entry", "x": 500, "y": 10})
        testufo.features.text = dedent(
            """\
            feature swsh {
                sub a by a.swsh;
            } swsh;
            feature init {
                sub meem by meem.init;
            } init;
            feature medi {
                sub meem by meem.medi;
            } medi;
            feature fina {
                sub alef by alef.fina;
                sub meem by meem.fina;
            } fina;
            """
        )
        testufo.lib["public.glyphOrder"] = [
            "a",
            "b",
            "c",
            "a.swsh",
            "alef",
            "alef.fina",
            "meem",
            "meem.init",
            "meem.medi",
            "meem.fina",
        ]
        generated = self.writeFeatures(testufo)

        assert str(generated) == dedent(
            """\
            feature curs {
                lookup curs_ltr {
                    lookupflag IgnoreMarks;
                    pos cursive a <anchor NULL> <anchor 100 200>;
                    pos cursive b <anchor 0 200> <anchor 111 200>;
                    pos cursive c <anchor 100 200> <anchor NULL>;
                    pos cursive a.swsh <anchor 100 200> <anchor NULL>;
                } curs_ltr;

                lookup curs_rtl {
                    lookupflag RightToLeft IgnoreMarks;
                    pos cursive alef.fina <anchor 300 10> <anchor NULL>;
                    pos cursive meem.init <anchor NULL> <anchor 0 10>;
                    pos cursive meem.medi <anchor 500 10> <anchor 0 10>;
                    pos cursive meem.fina <anchor 500 10> <anchor NULL>;
                } curs_rtl;

            } curs;
            """
        )
