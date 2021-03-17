from ufo2ft.featureWriters import BaseFeatureWriter, ast


class GdefFeatureWriter(BaseFeatureWriter):
    """Generates a GDEF table based on OpenType Category and glyph anchors.

    It skips generating the GDEF if a GDEF is defined in the features.

    It uses the 'public.openTypeCategories' values to create the GDEF ClassDefs
    and the ligature caret anchors to create the GDEF ligature carets.

    """

    tableTag = "GDEF"
    features = frozenset(["GlyphClassDefs", "LigatureCarets"])
    insertFeatureMarker = None

    def setContext(self, font, feaFile, compiler=None):
        ctx = super().setContext(font, feaFile, compiler=compiler)

        ctx.gdefTableBlock = ast.findTable(self.context.feaFile, "GDEF")
        if ctx.gdefTableBlock:
            for fea in ctx.gdefTableBlock.statements:
                if isinstance(fea, ast.GlyphClassDefStatement):
                    ctx.todo.remove("GlyphClassDefs")
                elif isinstance(fea, ast.LigatureCaretByIndexStatement) or isinstance(
                    fea, ast.LigatureCaretByPosStatement
                ):
                    ctx.todo.remove("LigatureCarets")

        ctx.orderedGlyphSet = self.getOrderedGlyphSet()

        if "GlyphClassDefs" in ctx.todo:
            ctx.openTypeCategories = self.getOpenTypeCategories()
        if "LigatureCarets" in ctx.todo:
            ctx.ligatureCarets = self._getLigatureCarets()

        return ctx

    def shouldContinue(self):
        todo = self.context.todo
        if not todo:
            return super().shouldContinue()

        if "LigatureCarets" in todo and not self.context.ligatureCarets:
            todo.remove("LigatureCarets")

        if "GlyphClassDefs" in todo and not any(self.context.openTypeCategories):
            todo.remove("GlyphClassDefs")

        return super().shouldContinue()

    def _getLigatureCarets(self):
        carets = dict()

        for glyphName, glyph in self.context.orderedGlyphSet.items():
            glyphCarets = set()
            for anchor in glyph.anchors:
                if (
                    anchor.name
                    and anchor.name.startswith("caret_")
                    and anchor.x is not None
                ):
                    glyphCarets.add(round(anchor.x))
                elif (
                    anchor.name
                    and anchor.name.startswith("vcaret_")
                    and anchor.y is not None
                ):
                    glyphCarets.add(round(anchor.y))

            if glyphCarets:
                carets[glyphName] = sorted(glyphCarets)

        return carets

    def _sortedGlyphClass(self, glyphNames):
        return sorted(n for n in self.context.orderedGlyphSet if n in glyphNames)

    def _makeGDEF(self):
        gdefTableBlock = self.context.gdefTableBlock
        if not gdefTableBlock:
            gdefTableBlock = ast.TableBlock("GDEF")

        if "GlyphClassDefs" in self.context.todo:
            categories = self.context.openTypeCategories
            glyphClassDefs = ast.GlyphClassDefStatement(
                ast.GlyphClass(self._sortedGlyphClass(categories.base)),
                ast.GlyphClass(self._sortedGlyphClass(categories.mark)),
                ast.GlyphClass(self._sortedGlyphClass(categories.ligature)),
                ast.GlyphClass(self._sortedGlyphClass(categories.component)),
            )
            gdefTableBlock.statements.append(glyphClassDefs)

        if "LigatureCarets" in self.context.todo:
            ligatureCarets = [
                ast.LigatureCaretByPosStatement(ast.GlyphName(glyphName), carets)
                for glyphName, carets in self.context.ligatureCarets.items()
            ]
            gdefTableBlock.statements.extend(ligatureCarets)

        return gdefTableBlock

    def _write(self):
        feaFile = self.context.feaFile
        if self.context.gdefTableBlock:
            self._makeGDEF()
        else:
            feaFile.statements.append(self._makeGDEF())

        return True
