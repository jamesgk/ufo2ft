import pytest
from textwrap import dedent

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
                lookupflag RightToLeft IgnoreMarks;
                pos cursive a <anchor NULL> <anchor 100 200>;
                pos cursive b <anchor 0 200> <anchor 111 200>;
                pos cursive c <anchor 100 200> <anchor NULL>;
            } curs;
            """
        )
