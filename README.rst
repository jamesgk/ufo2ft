|GitHub Actions status| |PyPI Version| |Codecov| |Gitter Chat|

ufo2ft
======

ufo2ft ("UFO to FontTools") is a fork of
`ufo2fdk <https://github.com/typesupply/ufo2fdk>`__ whose goal is to
generate OpenType font binaries from UFOs without the FDK dependency.

The library provides two functions, ``compileOTF`` and ``compileTTF``,
which work exactly the same way:

.. code:: python

    from defcon import Font
    from ufo2ft import compileOTF
    ufo = Font('MyFont-Regular.ufo')
    otf = compileOTF(ufo)
    otf.save('MyFont-Regular.otf')

In most cases, the behavior of ufo2ft should match that of ufo2fdk, whose
documentation is retained further below (and hopefully is still accurate).

Modifying the behavior of ufo2ft
--------------------------------

ufo2ft by default tries to do little more than what the UFO specification
demands. Popular font design applications that came after the specification was
made and specific workflows however may demand more. ufo2ft obeys certain keys
in a UFO's "lib", i.e. key-value pairs in the UFO's ``lib.plist`` file.

Filters (lib key: ``com.github.googlei18n.ufo2ft.filters``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Filters can modify glyphs before ("pre" = True) or after ("pre" = False)
decomposition of composite glyphs. The default is running filters after
decomposition ("pre" = False).

Example
^^^^^^^

You would insert the following into a UFO's ``lib.plist``:

.. code:: xml

    <key>com.github.googlei18n.ufo2ft.filters</key>
    <array>
        <dict>
            <key>name</key>
            <string>propagateAnchors</key>
            <key>pre</key>
            <true />
            <!-- Optionally, specify a list of glyphs to in- or exclude for
                 this filter (the default is to include all glyphs). "include"
                 and "exclude" are mutually exclusive. -->
            <key>include</key>
            <array>
                <string>a</string>
                <string>b</string>
            </array>
        </dict>
    </array>

Or in code:

.. code:: python

    from defcon import Font
    from ufo2ft import compileOTF

    ufo = Font("MyFont-Regular.ufo")
    ufo.lib["com.github.googlei18n.ufo2ft.filters"] = [
        {"name": "propagateAnchors", "pre": True, "include": ["a", "b"]}
    ]
    otf = compileOTF(ufo)
    otf.save("MyFont-Regular.otf")

Using code allows you to define an inclusion function (not available for exclusion), like so:

.. code:: python

    from defcon import Font
    from ufo2ft import compileOTF

    def my_filter_function(glyph):
        """Include all glyphs with a Unicode value between U+007F and U+00FF."""
        if glyph.unicode:
            return 0x007F < glyph.unicode < 0x00FF
        return False

    ufo = Font("MyFont-Regular.ufo")
    ufo.lib["com.github.googlei18n.ufo2ft.filters"] = [
        {"name": "propagateAnchors", "pre": True, "include": my_filter_function}
    ]
    otf = compileOTF(ufo)
    otf.save("MyFont-Regular.otf")

``cubicToQuadratic``
^^^^^^^^^^^^^^^^^^^^

Converts outlines from cubic (PostScript flavor) to quadratic (TrueType flavor).
It is run by default when producing TrueType-flavored OpenType fonts. Honors the
UFO's ``com.github.googlei18n.cu2qu.curve_type`` lib key.

.. code:: xml

    <key>com.github.googlei18n.ufo2ft.filters</key>
    <array>
        <dict>
            <key>name</key>
            <string>cubicToQuadratic</key>
            <!-- Optionally, the filter can save the result of the conversion
                 to the UFO's lib key "com.github.googlei18n.cu2qu.curve_type",
                 which can be either "cubic" or "quadratic". Turn this off if
                 you want to run the filter multiple times. You can also
                 manually set the lib key to "quadratic" if your font is made
                 using quadratic curves, which saves you further explicit
                 configuration. -->
            <key>rememberCurveType</key>
            <true /> <!-- The default. -->
            <!-- The conversion process is necessarily an approximation. Set
                 the acceptable error here, expressed in the maximum distance
                 between the original and converted curve, and it's relative
                 to the UPM of the font (default: 1/1000 or 0.001) -->
            <key>conversionError</key>
            <real>0.001</real> <!-- The default. -->
            <!-- Cubic (PostScript flavored) curves are typically oriented
                 counter-clockwise, quadratic (TrueType flavored) curves are
                 typically oriented clockwise. Reversing the direction is
                 recommended. -->
            <key>reverseDirection</key>
            <true /> <!-- The default. -->
        </dict>
    </array>

When to modify the filter settings: 

* You want fine-grained control over the conversion error.
* Your font is or some glyphs are drawn using quadratic curves and you want to
  prevent contour direction reversal.

``decomposeComponents``
^^^^^^^^^^^^^^^^^^^^^^^

What it does...

Example...

When to use...

When not to use...

``flattenComponents``
^^^^^^^^^^^^^^^^^^^^^

What it does...

Example...

When to use...

When not to use...

``propagateAnchors``
^^^^^^^^^^^^^^^^^^^^

What it does...

Example...

When to use...

When not to use...

``removeOverlaps``
^^^^^^^^^^^^^^^^^^

What it does...

Example...

When to use...

When not to use...

``transformations``
^^^^^^^^^^^^^^^^^^^

What it does...

Example...

When to use...

When not to use...

Naming Data
-----------

As with any OpenType compiler, you have to set the font naming data to a
particular standard for your naming to be set correctly. In ufo2fdk, you
can get away with setting *two* naming attributes in your font.info
object for simple fonts:

-  familyName: The name for your family. For example, "My Garamond".
-  styleName: The style name for this particular font. For example,
   "Display Light Italic"

ufo2fdk will create all of the other naming data based on thse two
fields. If you want to use the fully automatic naming system, all of the
other name attributes should be set to ``None`` in your font. However,
if you want to override the automated system at any level, you can
specify particular naming attributes and ufo2fdk will honor your
settings. You don't have to set *all* of the attributes, just the ones
you don't want to be automated. For example, in the family "My Garamond"
you have eight weights. It would be nice to style map the italics to the
romans for each weight. To do this, in the individual romans and
italics, you need to set the style mapping data. This is done through
the ``styleMapFamilyName`` and ``styleMapStyleName`` attributes. In each
of your roman and italic pairs you would do this:

**My Garamond-Light.ufo**

-  familyName = "My Garamond"
-  styleName = "Light"
-  styleMapFamilyName = "My Garamond Display Light"
-  styleMapStyleName = "regular"

**My Garamond-Light Italic.ufo**

-  familyName = "My Garamond"
-  styleName = "Display Light Italic"
-  styleMapFamilyName = "My Garamond Display Light"
-  styleMapStyleName = "italic"

**My Garamond-Book.ufo**

-  familyName = "My Garamond"
-  styleName = "Book"
-  styleMapFamilyName = "My Garamond Display Book"
-  styleMapStyleName = "regular"

**My Garamond-Book Italic.ufo**

-  familyName = "My Garamond"
-  styleName = "Display Book Italic"
-  styleMapFamilyName = "My Garamond Display Book"
-  styleMapStyleName = "italic"

**etc.**

Additionally, if you have defined any naming data, or any data for that
matter, in table definitions within your font's features that data will
be honored.


Feature generation
------------------

If your font's features do not contain kerning/mark/mkmk features,
ufo2ft will create them based on your font's kerning/anchor data.

In addition to
`Adobe OpenType feature files <http://www.adobe.com/devnet/opentype/afdko/topic_feature_file_syntax.html>`__,
ufo2ft also supports the
`MTI/Monotype format <http://monotype.github.io/OpenType_Table_Source/otl_source.html>`__.
For example, a GPOS table in this format would be stored within the UFO at
``data/com.github.googlei18n.ufo2ft.mtiFeatures/GPOS.mti``.


Fallbacks
---------

Most of the fallbacks have static values. To see what is set for these,
look at ``fontInfoData.py`` in the source code.

In some cases, the fallback values are dynamically generated from other
data in the info object. These are handled internally with functions.

Merging TTX
-----------

If the UFO data directory has a ``com.github.fonttools.ttx`` folder with TTX
files ending with ``.ttx``, these will be merged in the generated font.
The index TTX (generated when using using ``ttx -s``) is not required.

.. |GitHub Actions status| image:: https://github.com/googlefonts/ufo2ft/workflows/Test%20+%20Deploy/badge.svg
.. |PyPI Version| image:: https://img.shields.io/pypi/v/ufo2ft.svg
   :target: https://pypi.org/project/ufo2ft/
.. |Codecov| image:: https://codecov.io/gh/googlefonts/ufo2ft/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/googlefonts/ufo2ft
.. |Gitter Chat| image:: https://badges.gitter.im/fonttools-dev/ufo2ft.svg
   :alt: Join the chat at https://gitter.im/fonttools-dev/ufo2ft
   :target: https://gitter.im/fonttools-dev/ufo2ft?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
