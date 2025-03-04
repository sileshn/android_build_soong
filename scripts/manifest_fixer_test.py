#!/usr/bin/env python
#
# Copyright (C) 2018 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Unit tests for manifest_fixer.py."""

import io
import sys
import unittest
from xml.dom import minidom
import xml.etree.ElementTree as ElementTree

import manifest_fixer

sys.dont_write_bytecode = True


class CompareVersionGtTest(unittest.TestCase):
  """Unit tests for compare_version_gt function."""

  def test_sdk(self):
    """Test comparing sdk versions."""
    self.assertTrue(manifest_fixer.compare_version_gt('28', '27'))
    self.assertFalse(manifest_fixer.compare_version_gt('27', '28'))
    self.assertFalse(manifest_fixer.compare_version_gt('28', '28'))

  def test_codename(self):
    """Test comparing codenames."""
    self.assertTrue(manifest_fixer.compare_version_gt('Q', 'P'))
    self.assertFalse(manifest_fixer.compare_version_gt('P', 'Q'))
    self.assertFalse(manifest_fixer.compare_version_gt('Q', 'Q'))

  def test_sdk_codename(self):
    """Test comparing sdk versions with codenames."""
    self.assertTrue(manifest_fixer.compare_version_gt('Q', '28'))
    self.assertFalse(manifest_fixer.compare_version_gt('28', 'Q'))

  def test_compare_numeric(self):
    """Test that numbers are compared in numeric and not lexicographic order."""
    self.assertTrue(manifest_fixer.compare_version_gt('18', '8'))


class RaiseMinSdkVersionTest(unittest.TestCase):
  """Unit tests for raise_min_sdk_version function."""

  def raise_min_sdk_version_test(self, input_manifest, min_sdk_version,
                                 target_sdk_version, library):
    doc = minidom.parseString(input_manifest)
    manifest_fixer.raise_min_sdk_version(doc, min_sdk_version,
                                         target_sdk_version, library)
    output = io.StringIO()
    manifest_fixer.write_xml(output, doc)
    return output.getvalue()

  manifest_tmpl = (
      '<?xml version="1.0" encoding="utf-8"?>\n'
      '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n'
      '%s'
      '</manifest>\n')

  def uses_sdk(self, min_sdk=None, target_sdk=None, extra=''):
    attrs = ''
    if min_sdk:
      attrs += ' android:minSdkVersion="%s"' % min_sdk
    if target_sdk:
      attrs += ' android:targetSdkVersion="%s"' % target_sdk
    if extra:
      attrs += ' ' + extra
    return '    <uses-sdk%s/>\n' % attrs

  def assert_xml_equal(self, output, expected):
    self.assertEqual(ElementTree.canonicalize(output), ElementTree.canonicalize(expected))

  def test_no_uses_sdk(self):
    """Tests inserting a uses-sdk element into a manifest."""

    manifest_input = self.manifest_tmpl % ''
    expected = self.manifest_tmpl % self.uses_sdk(min_sdk='28', target_sdk='28')
    output = self.raise_min_sdk_version_test(manifest_input, '28', '28', False)
    self.assert_xml_equal(output, expected)

  def test_no_min(self):
    """Tests inserting a minSdkVersion attribute into a uses-sdk element."""

    manifest_input = self.manifest_tmpl % '    <uses-sdk extra="foo"/>\n'
    expected = self.manifest_tmpl % self.uses_sdk(min_sdk='28', target_sdk='28',
                                                  extra='extra="foo"')
    output = self.raise_min_sdk_version_test(manifest_input, '28', '28', False)
    self.assert_xml_equal(output, expected)

  def test_raise_min(self):
    """Tests inserting a minSdkVersion attribute into a uses-sdk element."""

    manifest_input = self.manifest_tmpl % self.uses_sdk(min_sdk='27')
    expected = self.manifest_tmpl % self.uses_sdk(min_sdk='28', target_sdk='28')
    output = self.raise_min_sdk_version_test(manifest_input, '28', '28', False)
    self.assert_xml_equal(output, expected)

  def test_raise(self):
    """Tests raising a minSdkVersion attribute."""

    manifest_input = self.manifest_tmpl % self.uses_sdk(min_sdk='27')
    expected = self.manifest_tmpl % self.uses_sdk(min_sdk='28', target_sdk='28')
    output = self.raise_min_sdk_version_test(manifest_input, '28', '28', False)
    self.assert_xml_equal(output, expected)

  def test_no_raise_min(self):
    """Tests a minSdkVersion that doesn't need raising."""

    manifest_input = self.manifest_tmpl % self.uses_sdk(min_sdk='28')
    expected = self.manifest_tmpl % self.uses_sdk(min_sdk='28', target_sdk='27')
    output = self.raise_min_sdk_version_test(manifest_input, '27', '27', False)
    self.assert_xml_equal(output, expected)

  def test_raise_codename(self):
    """Tests raising a minSdkVersion attribute to a codename."""

    manifest_input = self.manifest_tmpl % self.uses_sdk(min_sdk='28')
    expected = self.manifest_tmpl % self.uses_sdk(min_sdk='P', target_sdk='P')
    output = self.raise_min_sdk_version_test(manifest_input, 'P', 'P', False)
    self.assert_xml_equal(output, expected)

  def test_no_raise_codename(self):
    """Tests a minSdkVersion codename that doesn't need raising."""

    manifest_input = self.manifest_tmpl % self.uses_sdk(min_sdk='P')
    expected = self.manifest_tmpl % self.uses_sdk(min_sdk='P', target_sdk='28')
    output = self.raise_min_sdk_version_test(manifest_input, '28', '28', False)
    self.assert_xml_equal(output, expected)

  def test_target(self):
    """Tests an existing targetSdkVersion is preserved."""

    manifest_input = self.manifest_tmpl % self.uses_sdk(min_sdk='26', target_sdk='27')
    expected = self.manifest_tmpl % self.uses_sdk(min_sdk='28', target_sdk='27')
    output = self.raise_min_sdk_version_test(manifest_input, '28', '29', False)
    self.assert_xml_equal(output, expected)

  def test_no_target(self):
    """Tests inserting targetSdkVersion when minSdkVersion exists."""

    manifest_input = self.manifest_tmpl % self.uses_sdk(min_sdk='27')
    expected = self.manifest_tmpl % self.uses_sdk(min_sdk='28', target_sdk='29')
    output = self.raise_min_sdk_version_test(manifest_input, '28', '29', False)
    self.assert_xml_equal(output, expected)

  def test_target_no_min(self):
    """"Tests inserting targetSdkVersion when minSdkVersion exists."""

    manifest_input = self.manifest_tmpl % self.uses_sdk(target_sdk='27')
    expected = self.manifest_tmpl % self.uses_sdk(min_sdk='28', target_sdk='27')
    output = self.raise_min_sdk_version_test(manifest_input, '28', '29', False)
    self.assert_xml_equal(output, expected)

  def test_no_target_no_min(self):
    """Tests inserting targetSdkVersion when minSdkVersion does not exist."""

    manifest_input = self.manifest_tmpl % ''
    expected = self.manifest_tmpl % self.uses_sdk(min_sdk='28', target_sdk='29')
    output = self.raise_min_sdk_version_test(manifest_input, '28', '29', False)
    self.assert_xml_equal(output, expected)

  def test_library_no_target(self):
    """Tests inserting targetSdkVersion when minSdkVersion exists."""

    manifest_input = self.manifest_tmpl % self.uses_sdk(min_sdk='27')
    expected = self.manifest_tmpl % self.uses_sdk(min_sdk='28', target_sdk='16')
    output = self.raise_min_sdk_version_test(manifest_input, '28', '29', True)
    self.assert_xml_equal(output, expected)

  def test_library_target_no_min(self):
    """Tests inserting targetSdkVersion when minSdkVersion exists."""

    manifest_input = self.manifest_tmpl % self.uses_sdk(target_sdk='27')
    expected = self.manifest_tmpl % self.uses_sdk(min_sdk='28', target_sdk='27')
    output = self.raise_min_sdk_version_test(manifest_input, '28', '29', True)
    self.assert_xml_equal(output, expected)

  def test_library_no_target_no_min(self):
    """Tests inserting targetSdkVersion when minSdkVersion does not exist."""

    manifest_input = self.manifest_tmpl % ''
    expected = self.manifest_tmpl % self.uses_sdk(min_sdk='28', target_sdk='16')
    output = self.raise_min_sdk_version_test(manifest_input, '28', '29', True)
    self.assert_xml_equal(output, expected)

  def test_extra(self):
    """Tests that extra attributes and elements are maintained."""

    manifest_input = self.manifest_tmpl % (
        '    <!-- comment -->\n'
        '    <uses-sdk android:minSdkVersion="27" extra="foo"/>\n'
        '    <application/>\n')

    # pylint: disable=line-too-long
    expected = self.manifest_tmpl % (
        '    <!-- comment -->\n'
        '    <uses-sdk android:minSdkVersion="28" extra="foo" android:targetSdkVersion="29"/>\n'
        '    <application/>\n')

    output = self.raise_min_sdk_version_test(manifest_input, '28', '29', False)

    self.assert_xml_equal(output, expected)

  def test_indent(self):
    """Tests that an inserted element copies the existing indentation."""

    manifest_input = self.manifest_tmpl % '  <!-- comment -->\n'

    # pylint: disable=line-too-long
    expected = self.manifest_tmpl % (
        '  <uses-sdk android:minSdkVersion="28" android:targetSdkVersion="29"/>\n'
        '  <!-- comment -->\n')

    output = self.raise_min_sdk_version_test(manifest_input, '28', '29', False)

    self.assert_xml_equal(output, expected)

  def test_multiple_uses_sdks(self):
    """Tests a manifest that contains multiple uses_sdks elements."""

    manifest_input = self.manifest_tmpl % (
        '    <uses-sdk android:featureFlag="foo" android:minSdkVersion="21" />\n'
        '    <uses-sdk android:featureFlag="!foo" android:minSdkVersion="22" />\n')
    expected = self.manifest_tmpl % (
      '    <uses-sdk android:featureFlag="foo" android:minSdkVersion="28" android:targetSdkVersion="28" />\n'
      '    <uses-sdk android:featureFlag="!foo" android:minSdkVersion="28" android:targetSdkVersion="28" />\n')

    output = self.raise_min_sdk_version_test(manifest_input, '28', '28', False)
    self.assert_xml_equal(output, expected)

class AddLoggingParentTest(unittest.TestCase):
  """Unit tests for add_logging_parent function."""

  def assert_xml_equal(self, output, expected):
    self.assertEqual(ElementTree.canonicalize(output), ElementTree.canonicalize(expected))

  def add_logging_parent_test(self, input_manifest, logging_parent=None):
    doc = minidom.parseString(input_manifest)
    if logging_parent:
      manifest_fixer.add_logging_parent(doc, logging_parent)
    output = io.StringIO()
    manifest_fixer.write_xml(output, doc)
    return output.getvalue()

  manifest_tmpl = (
      '<?xml version="1.0" encoding="utf-8"?>\n'
      '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n'
      '%s'
      '</manifest>\n')

  def uses_logging_parent(self, logging_parent=None):
    attrs = ''
    if logging_parent:
      meta_text = ('<meta-data android:name="android.content.pm.LOGGING_PARENT" '
                   'android:value="%s"/>\n') % logging_parent
      attrs += '    <application>\n        %s    </application>\n' % meta_text

    return attrs

  def test_no_logging_parent(self):
    """Tests manifest_fixer with no logging_parent."""
    manifest_input = self.manifest_tmpl % ''
    expected = self.manifest_tmpl % self.uses_logging_parent()
    output = self.add_logging_parent_test(manifest_input)
    self.assert_xml_equal(output, expected)

  def test_logging_parent(self):
    """Tests manifest_fixer with no logging_parent."""
    manifest_input = self.manifest_tmpl % ''
    expected = self.manifest_tmpl % self.uses_logging_parent('FOO')
    output = self.add_logging_parent_test(manifest_input, 'FOO')
    self.assert_xml_equal(output, expected)


class AddUsesLibrariesTest(unittest.TestCase):
  """Unit tests for add_uses_libraries function."""

  def assert_xml_equal(self, output, expected):
    self.assertEqual(ElementTree.canonicalize(output), ElementTree.canonicalize(expected))

  def run_test(self, input_manifest, new_uses_libraries):
    doc = minidom.parseString(input_manifest)
    manifest_fixer.add_uses_libraries(doc, new_uses_libraries, True)
    output = io.StringIO()
    manifest_fixer.write_xml(output, doc)
    return output.getvalue()

  manifest_tmpl = (
      '<?xml version="1.0" encoding="utf-8"?>\n'
      '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n'
      '%s'
      '</manifest>\n')

  def uses_libraries(self, name_required_pairs):
    ret = '    <application>\n'
    for name, required in name_required_pairs:
      ret += (
          '        <uses-library android:name="%s" android:required="%s"/>\n'
      ) % (name, required)
    ret += '    </application>\n'
    return ret

  def test_empty(self):
    """Empty new_uses_libraries must not touch the manifest."""
    manifest_input = self.manifest_tmpl % self.uses_libraries([
        ('foo', 'true'),
        ('bar', 'false')])
    expected = manifest_input
    output = self.run_test(manifest_input, [])
    self.assert_xml_equal(output, expected)

  def test_not_overwrite(self):
    """new_uses_libraries must not overwrite existing tags."""
    manifest_input = self.manifest_tmpl % self.uses_libraries([
        ('foo', 'true'),
        ('bar', 'false')])
    expected = manifest_input
    output = self.run_test(manifest_input, ['foo', 'bar'])
    self.assert_xml_equal(output, expected)

  def test_add(self):
    """New names are added with 'required:true'."""
    manifest_input = self.manifest_tmpl % self.uses_libraries([
        ('foo', 'true'),
        ('bar', 'false')])
    expected = self.manifest_tmpl % self.uses_libraries([
        ('foo', 'true'),
        ('bar', 'false'),
        ('baz', 'true'),
        ('qux', 'true')])
    output = self.run_test(manifest_input, ['bar', 'baz', 'qux'])
    self.assert_xml_equal(output, expected)

  def test_no_application(self):
    """When there is no <application> tag, the tag is added."""
    manifest_input = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<manifest xmlns:android='
        '"http://schemas.android.com/apk/res/android">\n'
        '</manifest>\n')
    expected = self.manifest_tmpl % self.uses_libraries([
        ('foo', 'true'),
        ('bar', 'true')])
    output = self.run_test(manifest_input, ['foo', 'bar'])
    self.assert_xml_equal(output, expected)

  def test_empty_application(self):
    """Even when here is an empty <application/> tag, the libs are added."""
    manifest_input = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<manifest xmlns:android='
        '"http://schemas.android.com/apk/res/android">\n'
        '    <application/>\n'
        '</manifest>\n')
    expected = self.manifest_tmpl % self.uses_libraries([
        ('foo', 'true'),
        ('bar', 'true')])
    output = self.run_test(manifest_input, ['foo', 'bar'])
    self.assert_xml_equal(output, expected)

  def test_multiple_application(self):
    """When there are multiple applications, the libs are added to each."""
    manifest_input = self.manifest_tmpl % (
            self.uses_libraries([('foo', 'false')]) +
            self.uses_libraries([('bar', 'false')]))
    expected = self.manifest_tmpl % (
            self.uses_libraries([('foo', 'false'), ('bar', 'true')]) +
            self.uses_libraries([('bar', 'false'), ('foo', 'true')]))
    output = self.run_test(manifest_input, ['foo', 'bar'])
    self.assert_xml_equal(output, expected)


class AddUsesNonSdkApiTest(unittest.TestCase):
  """Unit tests for add_uses_libraries function."""

  def assert_xml_equal(self, output, expected):
    self.assertEqual(ElementTree.canonicalize(output), ElementTree.canonicalize(expected))

  def run_test(self, input_manifest):
    doc = minidom.parseString(input_manifest)
    manifest_fixer.add_uses_non_sdk_api(doc)
    output = io.StringIO()
    manifest_fixer.write_xml(output, doc)
    return output.getvalue()

  manifest_tmpl = (
      '<?xml version="1.0" encoding="utf-8"?>\n'
      '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n'
      '    %s\n'
      '</manifest>\n')

  def uses_non_sdk_api(self, value):
    return '<application %s/>' % ('android:usesNonSdkApi="true"' if value else '')

  def test_set_true(self):
    """Empty new_uses_libraries must not touch the manifest."""
    manifest_input = self.manifest_tmpl % self.uses_non_sdk_api(False)
    expected = self.manifest_tmpl % self.uses_non_sdk_api(True)
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, expected)

  def test_already_set(self):
    """new_uses_libraries must not overwrite existing tags."""
    manifest_input = self.manifest_tmpl % self.uses_non_sdk_api(True)
    expected = manifest_input
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, expected)

  def test_multiple_applications(self):
    """new_uses_libraries must be added to all applications."""
    manifest_input = self.manifest_tmpl % (self.uses_non_sdk_api(True) +  self.uses_non_sdk_api(False))
    expected = self.manifest_tmpl % (self.uses_non_sdk_api(True) +  self.uses_non_sdk_api(True))
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, expected)


class UseEmbeddedDexTest(unittest.TestCase):
  """Unit tests for add_use_embedded_dex function."""

  def assert_xml_equal(self, output, expected):
    self.assertEqual(ElementTree.canonicalize(output), ElementTree.canonicalize(expected))

  def run_test(self, input_manifest):
    doc = minidom.parseString(input_manifest)
    manifest_fixer.add_use_embedded_dex(doc)
    output = io.StringIO()
    manifest_fixer.write_xml(output, doc)
    return output.getvalue()

  manifest_tmpl = (
      '<?xml version="1.0" encoding="utf-8"?>\n'
      '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n'
      '    %s\n'
      '</manifest>\n')

  def use_embedded_dex(self, value):
    return '<application android:useEmbeddedDex="%s" />' % value

  def test_manifest_with_undeclared_preference(self):
    manifest_input = self.manifest_tmpl % '<application/>'
    expected = self.manifest_tmpl % self.use_embedded_dex('true')
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, expected)

  def test_manifest_with_use_embedded_dex(self):
    manifest_input = self.manifest_tmpl % self.use_embedded_dex('true')
    expected = manifest_input
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, expected)

  def test_manifest_with_not_use_embedded_dex(self):
    manifest_input = self.manifest_tmpl % self.use_embedded_dex('false')
    self.assertRaises(RuntimeError, self.run_test, manifest_input)

  def test_multiple_applications(self):
    manifest_input = self.manifest_tmpl % (
        self.use_embedded_dex('true') +
        '<application/>'
    )
    expected = self.manifest_tmpl % (
        self.use_embedded_dex('true') +
        self.use_embedded_dex('true')
    )
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, expected)


class AddExtractNativeLibsTest(unittest.TestCase):
  """Unit tests for add_extract_native_libs function."""

  def assert_xml_equal(self, output, expected):
    self.assertEqual(ElementTree.canonicalize(output), ElementTree.canonicalize(expected))

  def run_test(self, input_manifest, value):
    doc = minidom.parseString(input_manifest)
    manifest_fixer.add_extract_native_libs(doc, value)
    output = io.StringIO()
    manifest_fixer.write_xml(output, doc)
    return output.getvalue()

  manifest_tmpl = (
      '<?xml version="1.0" encoding="utf-8"?>\n'
      '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n'
      '    %s\n'
      '</manifest>\n')

  def extract_native_libs(self, value):
    return '<application android:extractNativeLibs="%s" />' % value

  def test_set_true(self):
    manifest_input = self.manifest_tmpl % '<application/>'
    expected = self.manifest_tmpl % self.extract_native_libs('true')
    output = self.run_test(manifest_input, True)
    self.assert_xml_equal(output, expected)

  def test_set_false(self):
    manifest_input = self.manifest_tmpl % '<application/>'
    expected = self.manifest_tmpl % self.extract_native_libs('false')
    output = self.run_test(manifest_input, False)
    self.assert_xml_equal(output, expected)

  def test_match(self):
    manifest_input = self.manifest_tmpl % self.extract_native_libs('true')
    expected = manifest_input
    output = self.run_test(manifest_input, True)
    self.assert_xml_equal(output, expected)

  def test_conflict(self):
    manifest_input = self.manifest_tmpl % self.extract_native_libs('true')
    self.assertRaises(RuntimeError, self.run_test, manifest_input, False)

  def test_multiple_applications(self):
    manifest_input = self.manifest_tmpl % (self.extract_native_libs('true') + '<application/>')
    expected = self.manifest_tmpl % (self.extract_native_libs('true') + self.extract_native_libs('true'))
    output = self.run_test(manifest_input, True)
    self.assert_xml_equal(output, expected)


class AddNoCodeApplicationTest(unittest.TestCase):
  """Unit tests for set_has_code_to_false function."""

  def assert_xml_equal(self, output, expected):
    self.assertEqual(ElementTree.canonicalize(output), ElementTree.canonicalize(expected))

  def run_test(self, input_manifest):
    doc = minidom.parseString(input_manifest)
    manifest_fixer.set_has_code_to_false(doc)
    output = io.StringIO()
    manifest_fixer.write_xml(output, doc)
    return output.getvalue()

  manifest_tmpl = (
      '<?xml version="1.0" encoding="utf-8"?>\n'
      '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n'
      '%s'
      '</manifest>\n')

  def test_no_application(self):
    manifest_input = self.manifest_tmpl % ''
    expected = self.manifest_tmpl % '    <application android:hasCode="false"/>\n'
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, expected)

  def test_has_application_no_has_code(self):
    manifest_input = self.manifest_tmpl % '    <application/>\n'
    expected = self.manifest_tmpl % '    <application android:hasCode="false"/>\n'
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, expected)

  def test_has_application_has_code_false(self):
    """ Do nothing if there's already an application element. """
    manifest_input = self.manifest_tmpl % '    <application android:hasCode="false"/>\n'
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, manifest_input)

  def test_has_application_has_code_true(self):
    """ Do nothing if there's already an application element even if its
     hasCode attribute is true. """
    manifest_input = self.manifest_tmpl % '    <application android:hasCode="true"/>\n'
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, manifest_input)

  def test_multiple_applications(self):
    """ Apply to all applications  """
    manifest_input = self.manifest_tmpl % (
        '    <application android:hasCode="true" />\n' +
        '    <application android:hasCode="false" />\n' +
        '    <application/>\n')
    expected = self.manifest_tmpl % (
        '    <application android:hasCode="true" />\n' +
        '    <application android:hasCode="false" />\n' +
        '    <application android:hasCode="false" />\n')
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, expected)


class AddTestOnlyApplicationTest(unittest.TestCase):
  """Unit tests for set_test_only_flag_to_true function."""

  def assert_xml_equal(self, output, expected):
    self.assertEqual(ElementTree.canonicalize(output), ElementTree.canonicalize(expected))

  def run_test(self, input_manifest):
    doc = minidom.parseString(input_manifest)
    manifest_fixer.set_test_only_flag_to_true(doc)
    output = io.StringIO()
    manifest_fixer.write_xml(output, doc)
    return output.getvalue()

  manifest_tmpl = (
      '<?xml version="1.0" encoding="utf-8"?>\n'
      '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n'
      '%s'
      '</manifest>\n')

  def test_no_application(self):
    manifest_input = self.manifest_tmpl % ''
    expected = self.manifest_tmpl % '    <application android:testOnly="true"/>\n'
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, expected)

  def test_has_application_no_test_only(self):
    manifest_input = self.manifest_tmpl % '    <application/>\n'
    expected = self.manifest_tmpl % '    <application android:testOnly="true"/>\n'
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, expected)

  def test_has_application_test_only_true(self):
    """ If there's already an application element."""
    manifest_input = self.manifest_tmpl % '    <application android:testOnly="true"/>\n'
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, manifest_input)

  def test_has_application_test_only_false(self):
    """ If there's already an application element with the testOnly attribute as false."""
    manifest_input = self.manifest_tmpl % '    <application android:testOnly="false"/>\n'
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, manifest_input)

  def test_multiple_applications(self):
    manifest_input = self.manifest_tmpl % (
        '    <application android:testOnly="true" />\n' +
        '    <application android:testOnly="false" />\n' +
        '    <application/>\n'
    )
    expected = self.manifest_tmpl % (
        '    <application android:testOnly="true" />\n' +
        '    <application android:testOnly="false" />\n' +
        '    <application android:testOnly="true" />\n'
    )
    output = self.run_test(manifest_input)
    self.assert_xml_equal(output, expected)


class SetMaxSdkVersionTest(unittest.TestCase):
  """Unit tests for set_max_sdk_version function."""

  def assert_xml_equal(self, output, expected):
    self.assertEqual(ElementTree.canonicalize(output), ElementTree.canonicalize(expected))

  def run_test(self, input_manifest, max_sdk_version):
    doc = minidom.parseString(input_manifest)
    manifest_fixer.set_max_sdk_version(doc, max_sdk_version)
    output = io.StringIO()
    manifest_fixer.write_xml(output, doc)
    return output.getvalue()

  manifest_tmpl = (
      '<?xml version="1.0" encoding="utf-8"?>\n'
      '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n'
      '%s'
      '</manifest>\n')

  def permission(self, max_sdk=None):
    if max_sdk is None:
      return '   <permission/>'
    return '    <permission android:maxSdkVersion="%s"/>\n' % max_sdk

  def uses_permission(self, max_sdk=None):
    if max_sdk is None:
      return '   <uses-permission/>'
    return '    <uses-permission android:maxSdkVersion="%s"/>\n' % max_sdk

  def test_permission_no_max_sdk_version(self):
    """Tests if permission has no maxSdkVersion attribute"""
    manifest_input = self.manifest_tmpl % self.permission()
    expected = self.manifest_tmpl % self.permission()
    output = self.run_test(manifest_input, '9000')
    self.assert_xml_equal(output, expected)

  def test_permission_max_sdk_version_changed(self):
    """Tests if permission maxSdkVersion attribute is set to current"""
    manifest_input = self.manifest_tmpl % self.permission('current')
    expected = self.manifest_tmpl % self.permission(9000)
    output = self.run_test(manifest_input, '9000')
    self.assert_xml_equal(output, expected)

  def test_permission_max_sdk_version_not_changed(self):
    """Tests if permission maxSdkVersion attribute is not set to current"""
    manifest_input = self.manifest_tmpl % self.permission(30)
    expected = self.manifest_tmpl % self.permission(30)
    output = self.run_test(manifest_input, '9000')
    self.assert_xml_equal(output, expected)

  def test_uses_permission_no_max_sdk_version(self):
    """Tests if uses-permission has no maxSdkVersion attribute"""
    manifest_input = self.manifest_tmpl % self.uses_permission()
    expected = self.manifest_tmpl % self.uses_permission()
    output = self.run_test(manifest_input, '9000')
    self.assert_xml_equal(output, expected)

  def test_uses_permission_max_sdk_version_changed(self):
    """Tests if uses-permission maxSdkVersion attribute is set to current"""
    manifest_input = self.manifest_tmpl % self.uses_permission('current')
    expected = self.manifest_tmpl % self.uses_permission(9000)
    output = self.run_test(manifest_input, '9000')
    self.assert_xml_equal(output, expected)

  def test_uses_permission_max_sdk_version_not_changed(self):
    """Tests if uses-permission maxSdkVersion attribute is not set to current"""
    manifest_input = self.manifest_tmpl % self.uses_permission(30)
    expected = self.manifest_tmpl % self.uses_permission(30)
    output = self.run_test(manifest_input, '9000')
    self.assert_xml_equal(output, expected)


class OverrideDefaultVersionTest(unittest.TestCase):
  """Unit tests for override_default_version function."""

  def assert_xml_equal(self, output, expected):
    self.assertEqual(ElementTree.canonicalize(output), ElementTree.canonicalize(expected))

  def run_test(self, input_manifest, version):
    doc = minidom.parseString(input_manifest)
    manifest_fixer.override_placeholder_version(doc, version)
    output = io.StringIO()
    manifest_fixer.write_xml(output, doc)
    return output.getvalue()

  manifest_tmpl = (
      '<?xml version="1.0" encoding="utf-8"?>\n'
      '<manifest xmlns:android="http://schemas.android.com/apk/res/android" '
      'android:versionCode="%s">\n'
      '</manifest>\n')

  def test_doesnt_override_existing_version(self):
    """Tests that an existing version is not overridden"""
    manifest_input = self.manifest_tmpl % '12345'
    expected = manifest_input
    output = self.run_test(manifest_input, '67890')
    self.assert_xml_equal(output, expected)

  def test_overrides_default_version(self):
    """Tests that a default version is overridden"""
    manifest_input = self.manifest_tmpl % '0'
    expected = self.manifest_tmpl % '67890'
    output = self.run_test(manifest_input, '67890')
    self.assert_xml_equal(output, expected)


if __name__ == '__main__':
  unittest.main(verbosity=2)
