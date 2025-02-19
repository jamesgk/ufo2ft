from ufo2ft.filters import BaseFilter


class ScaleUPMFilter(BaseFilter):

    """ This filter scales the font to a new upm value. Set the target upm in
    an UFO like this:
    <key>com.github.googlei18n.ufo2ft.filters</key>
    <array>
        <dict>
            <key>name</key>
            <string>scaleUPM</string>
            <key>kwargs</key>
            <dict>
                <key>unitsPerEm</key>
                <string>2048</string>
            </dict>
        </dict>
    </array>
    """

    _kwargs = {
        "unitsPerEm": 1000,
    }

    def _scaleGlyph(self, glyph):
        """
        Scale a glyph
        """
        for contour in glyph:
            for point in contour.points:
                point.x *= self.factor
                point.y *= self.factor

        for anchor in glyph.anchors:
            anchor.x *= self.factor
            anchor.y *= self.factor

        glyph.width *= self.factor

    def _scaleList(self, obj, name):
        """
        Scale a font info property that is a list, i.e. scale each value.
        """
        lst = getattr(obj, name)
        if lst is None:
            return

        lst = [self.factor * v for v in lst]
        setattr(obj, name, lst)

    def _scaleProperty(self, obj, name):
        prop = getattr(obj, name)
        if prop is None:
            return

        setattr(obj, name, self.factor * prop)

    def __call__(self, font, glyphSet=None):
        newUnitsPerEm = int(self.options.unitsPerEm)
        if font.info.unitsPerEm == newUnitsPerEm:
            return False

        self.factor = newUnitsPerEm / font.info.unitsPerEm

        # Scale glyphs
        super(ScaleUPMFilter, self).__call__(font, glyphSet)

        # Scale kerning
        for pair, value in font.kerning.items():
            font.kerning[pair] = value * self.factor

        # TODO: Change positioning feature code

        # Scale info values
        for prop in (
            "descender",
            "xHeight",
            "capHeight",
            "ascender",
            "openTypeHheaAscender",
            "openTypeHheaDescender",
            "openTypeHheaLineGap",
            "openTypeHheaCaretOffset",
            "openTypeOS2TypoAscender",
            "openTypeOS2TypoDescender",
            "openTypeOS2TypoLineGap",
            "openTypeOS2WinAscent",
            "openTypeOS2WinDescent",
            "openTypeOS2SubscriptXSize",
            "openTypeOS2SubscriptYSize",
            "openTypeOS2SubscriptXOffset",
            "openTypeOS2SubscriptYOffset",
            "openTypeOS2SuperscriptXSize",
            "openTypeOS2SuperscriptYSize",
            "openTypeOS2SuperscriptXOffset",
            "openTypeOS2SuperscriptYOffset",
            "openTypeOS2StrikeoutSize",
            "openTypeOS2StrikeoutPosition",
            "openTypeVheaVertTypoAscender",
            "openTypeVheaVertTypoDescender",
            "openTypeVheaVertTypoLineGap",
            "openTypeVheaCaretOffset",
            "postscriptUnderlineThickness",
            "postscriptUnderlinePosition",
        ):
            self._scaleProperty(font.info, prop)

        for prop in (
            "postscriptBlueValues",
            "postscriptOtherBlues",
            "postscriptFamilyOtherBlues",
            "postscriptStemSnapH",
            "postscriptStemSnapV",
            "postscriptBlueFuzz",
            "postscriptBlueShift",
            "postscriptBlueScale",
            "postscriptDefaultWidthX",
            "postscriptNominalWidthX",
        ):
            self._scaleList(font.info, prop)

        # Finally set new UPM
        font.info.unitsPerEm = newUnitsPerEm

        return True

    def filter(self, glyph):
        if getattr(self.context, "skipCurrentFont", False):
            return False

        # Scale glyph
        self._scaleGlyph(glyph)

        # scale component offsets
        for i in range(len(glyph.components)):
            comp = glyph.components[i]
            xS, xyS, yxS, yS, xOff, yOff = comp.transformation
            comp.transformation = (
                xS,
                xyS,
                yxS,
                yS,
                xOff * self.factor,
                yOff * self.factor,
            )
