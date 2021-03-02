from fontTools.misc.fixedTools import otRound

from ufo2ft.featureWriters import BaseFeatureWriter, ast


class CursFeatureWriter(BaseFeatureWriter):
    """Generate a curs feature base on glyph anchors.

    The default mode is 'skip': i.e. if the 'curs' feature is already present in
    the feature file, it is not generated again.

    The optional 'append' mode will add extra lookups to an already existing
    features, if any.

    By default, anchors names 'entry' and 'exit' will be used to connect the
    'entry' anchor of a glyph with the 'exit' anchor of the preceding glyph.
    """

    tableTag = "GPOS"
    features = frozenset(["curs"])

    entryAnchorNames = {"entry"}
    exitAnchorNames = {"exit"}

    def _write(self):
        feaFile = self.context.feaFile
        feature = None

        cursiveAnchors = dict()
        for glyphName, glyph in self.getOrderedGlyphSet().items():
            entryAnchor = exitAnchor = None
            for anchor in glyph.anchors:
                if entryAnchor and exitAnchor:
                    break
                if anchor.name in self.entryAnchorNames:
                    entryAnchor = ast.Anchor(x=otRound(anchor.x), y=otRound(anchor.y))
                elif anchor.name in self.exitAnchorNames:
                    exitAnchor = ast.Anchor(x=otRound(anchor.x), y=otRound(anchor.y))

            if entryAnchor or exitAnchor:
                cursiveAnchors[ast.GlyphName(glyphName)] = (entryAnchor, exitAnchor)

        if cursiveAnchors:
            feature = ast.FeatureBlock("curs")
            feature.statements.append(
                ast.makeLookupFlag(flags=("IgnoreMarks", "RightToLeft"))
            )
            for glyphName, anchors in cursiveAnchors.items():
                statement = ast.CursivePosStatement(glyphName, *anchors)
                feature.statements.append(statement)

        if not feature:
            return False

        self._insert(feaFile=feaFile, features=[feature])
        return True
