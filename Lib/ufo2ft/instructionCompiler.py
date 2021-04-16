# -*- coding: utf-8 -*-
import array
import logging

from fontTools import ttLib
from fontTools.pens.hashPointPen import HashPointPen
from fontTools.ttLib.tables._g_l_y_f import (
    OVERLAP_COMPOUND,
    ROUND_XY_TO_GRID,
    USE_MY_METRICS,
)

logger = logging.getLogger(__name__)

TRUETYPE_INSTRUCTIONS_KEY = "public.truetype.instructions"
TRUETYPE_ROUND_KEY = "public.truetype.roundOffsetToGrid"
TRUETYPE_METRICS_KEY = "public.truetype.useMyMetrics"
TRUETYPE_OVERLAP_KEY = "public.truetype.overlap"
OBJECT_LIBS_KEY = "public.objectLibs"


class InstructionCompiler(object):
    def __init__(self, ufo, ttf):
        self.ufo = ufo
        self.font = ttf

    def _compile_program(self, key, table_tag):
        assert table_tag in ("prep", "fpgm")
        ttdata = self.ufo.lib.get(TRUETYPE_INSTRUCTIONS_KEY, None)
        if ttdata:
            formatVersion = ttdata.get("formatVersion", None)
            if int(formatVersion) != 1:
                logger.error(
                    f"Unknown formatVersion {formatVersion} "
                    f"in key '{key}', "
                    f"table '{table_tag}' will be empty in font."
                )
                return
            asm = ttdata.get(key, None)
            if asm is not None:
                self.font[table_tag] = table = ttLib.newTable(table_tag)
                table.program = ttLib.tables.ttProgram.Program()
                table.program.fromAssembly(asm)
                # Roundtrip once, or if the font is dumped to XML before having
                # been saved, the assembly code if will look awful.
                table.program.fromBytecode(table.program.getBytecode())

    def compile_cvt(self):
        cvts = []
        ttdata = self.ufo.lib.get(TRUETYPE_INSTRUCTIONS_KEY, None)
        if ttdata:
            formatVersion = ttdata.get("formatVersion", None)
            if int(formatVersion) != 1:
                logger.error(
                    f"Unknown formatVersion {formatVersion} "
                    f"in key 'controlValue', "
                    f"table 'cvt' will be empty in font."
                )
                return
            cvt_list = ttdata.get("controlValue", None)
            if cvt_list is not None:
                # Convert string keys to int
                cvt_dict = {int(v["id"]): v["value"] for v in cvt_list}
                # Find the maximum cvt index.
                # We can't just use the dict keys because the cvt must be
                # filled consecutively.
                max_cvt = max(cvt_dict.keys())
                # Make value list, filling entries for missing keys with 0
                cvts = [cvt_dict.get(i, 0) for i in range(max_cvt + 1)]

        if cvts:
            # Only write cvt to font if it contains any values
            self.font["cvt "] = cvt = ttLib.newTable("cvt ")
            cvt.values = array.array("h", cvts)

    def compile_fpgm(self):
        self._compile_program("fontProgram", "fpgm")

    def compile_glyf(self):
        for name in sorted(self.ufo.keys()):
            glyph = self.ufo[name]
            ttdata = glyph.lib.get(TRUETYPE_INSTRUCTIONS_KEY, None)
            if name not in self.font["glyf"]:
                if ttdata is not None:
                    logger.warning(
                        f"Glyph '{name}' not found in font, "
                        "skipping compilation of TrueType instructions "
                        "for this glyph."
                    )
                logger.debug(f"UFO keys: {list(self.ufo.keys())}")
                logger.debug(f"glyf keys: {list(self.font['glyf'].keys())}")
                continue

            glyf = self.font["glyf"][name]
            if ttdata is not None:
                formatVersion = ttdata.get("formatVersion", None)
                if int(formatVersion) != 1:
                    logger.error(
                        f"Unknown formatVersion {formatVersion} "
                        "in glyph '{name}', it will have "
                        "no instructions in font."
                    )
                    continue

                # Check if glyph hash matches the current outlines
                hash_pen = HashPointPen(glyph.width, self.ufo)
                glyph.drawPoints(hash_pen)
                glyph_id = ttdata.get("id", None)
                if glyph_id is None or glyph_id != hash_pen.hash:
                    logger.error(
                        f"Glyph hash mismatch, glyph '{name}' will have "
                        "no instructions in font."
                    )
                    continue

                # Compile the glyph program
                asm = ttdata.get("assembly", None)
                if asm is not None:
                    glyf.program = ttLib.tables.ttProgram.Program()
                    glyf.program.fromAssembly(asm)
                    # Roundtrip once, or if the font is dumped to XML before
                    # having been saved, the assembly code if will look awful.
                    glyf.program.fromBytecode(glyf.program.getBytecode())

            # Handle composites
            if glyf.isComposite():
                # Remove empty glyph programs from composite glyphs
                if hasattr(glyf, "program") and not glyf.program:
                    delattr(glyf, "program")

                # Set component flags

                # We need to decide when to set the flags.
                # Let's assume if any lib key is not there, or the component
                # doesn't have an identifier, we should leave the flags alone.
                use_my_metrics_comp = None
                for i, c in enumerate(glyf.components):
                    if i >= len(glyph.components):
                        logger.error(
                            "Number of components differ between UFO and TTF "
                            f"in glyph '{name}' ({len(glyph.components)} vs. "
                            f"{len(glyf.components)}, not setting flags in "
                            "additional components."
                        )
                        break
                    ufo_component_id = glyph.components[i].identifier
                    if (
                        ufo_component_id is not None
                        and OBJECT_LIBS_KEY in glyph.lib
                        and ufo_component_id in glyph.lib[OBJECT_LIBS_KEY]
                        and (
                            TRUETYPE_ROUND_KEY
                            in glyph.lib[OBJECT_LIBS_KEY][ufo_component_id]
                            or TRUETYPE_METRICS_KEY
                            in glyph.lib[OBJECT_LIBS_KEY][ufo_component_id]
                        )
                    ):
                        component_lib = glyph.lib[OBJECT_LIBS_KEY][ufo_component_id]

                        c.flags &= ~ROUND_XY_TO_GRID
                        if component_lib.get(TRUETYPE_ROUND_KEY, False):
                            c.flags |= ROUND_XY_TO_GRID

                        c.flags &= ~USE_MY_METRICS
                        if component_lib.get(TRUETYPE_METRICS_KEY, False):
                            if use_my_metrics_comp:
                                logger.warning(
                                    "Ignoring USE_MY_METRICS flag on component "
                                    f"'{ufo_component_id}' because it has been set on "
                                    f"component '{use_my_metrics_comp}' already."
                                )
                            else:
                                c.flags |= USE_MY_METRICS
                                use_my_metrics_comp = ufo_component_id

                    # We might automatically set the flags if no data is present,
                    # but:
                    # - https://github.com/googlefonts/ufo2ft/pull/425 recommends
                    #   against setting the ROUND_XY_TO_GRID flag
                    # - USE_MY_METRICS has been set already by
                    #   outlineCompiler.OutlineTTFCompiler.autoUseMyMetrics

                    if i == 0 and TRUETYPE_OVERLAP_KEY in glyph.lib:
                        # Set OVERLAP_COMPOUND on the first component only
                        c.flags &= ~OVERLAP_COMPOUND
                        if glyph.lib.get(TRUETYPE_OVERLAP_KEY, False):
                            c.flags |= OVERLAP_COMPOUND

    def compile_maxp(self):
        maxp = self.font["maxp"]
        ttdata = self.ufo.lib.get(TRUETYPE_INSTRUCTIONS_KEY, None)
        if ttdata:
            for name in (
                "maxStorage",
                "maxFunctionDefs",
                "maxInstructionDefs",
                "maxStackElements",
                # "maxSizeOfInstructions",  # Is recalculated below
                "maxZones",
                "maxTwilightPoints",
            ):
                value = ttdata.get(name, None)
                if value is not None:
                    setattr(maxp, name, value)

        # Recalculate maxp.maxSizeOfInstructions
        sizes = [
            len(glyph.program.getBytecode())
            for glyph in self.font["glyf"].glyphs.values()
            if hasattr(glyph, "program")
        ] + [0]
        maxp.maxSizeOfInstructions = max(sizes)

    def compile_prep(self):
        self._compile_program("controlValueProgram", "prep")

    def compile(self):
        self.compile_cvt()
        self.compile_fpgm()
        self.compile_prep()
        self.compile_glyf()
        # maxp depends on the other programs, to it needs to be last
        self.compile_maxp()
