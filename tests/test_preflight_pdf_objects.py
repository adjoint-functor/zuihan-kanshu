"""Real PDF objects: navigation, attachments and parser failures."""

import pathlib
import runpy
import tempfile
import unittest
from unittest import mock

from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject, NameObject, NumberObject, TextStringObject

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "skill/zuihan-kanshu/scripts/preflight-pdf.py"
CHECK = runpy.run_path(str(SCRIPT))["inspect_pdf_objects"]

UUID_TAIL = bytes.fromhex("00110010800000aa00389b71")


def box(kind, payload, *, extended=False, to_eof=False):
    if to_eof:
        return b"\0\0\0\0" + kind + payload
    if extended:
        return b"\0\0\0\1" + kind + (16 + len(payload)).to_bytes(8, "big") + payload
    return (8 + len(payload)).to_bytes(4, "big") + kind + payload


def jumb(kind, label, contents, **framing):
    description = box(b"jumd", kind + UUID_TAIL + b"\3" + label.encode("utf-8") + b"\0")
    return box(b"jumb", description + contents, **framing)


def credential(*manifest_types, extended=False, to_eof=False):
    """Synthetic container fixtures; intentionally no cryptographic validity claim."""
    manifests = b""
    for index, kind in enumerate(manifest_types or (b"c2ma",)):
        claim = jumb(b"cbor", "c2pa.claim.v2", box(b"cbor", b"\xa0"))
        signature = jumb(b"cbor", "c2pa.signature", box(b"cbor", b"\x84\x40\xa0\x40\x40"))
        manifests += jumb(kind, f"urn:c2pa:fixture:{index}", claim + signature)
    return jumb(b"c2pa", "c2pa", manifests, extended=extended, to_eof=to_eof)


class PdfObjectsTests(unittest.TestCase):
    def inspect(self, writer, patterns=()):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "sample.pdf"
            writer.write(path)
            issues = []
            # The checks must actually run without either optional executable.
            with mock.patch("shutil.which", return_value=None):
                report = CHECK(path, list(patterns), issues)
            return report, issues

    def writer(self):
        writer = PdfWriter()
        writer.add_blank_page(200, 200)
        writer.add_blank_page(200, 200)
        return writer

    def attach_credential(self, writer, payload=None, *, name="credential.c2pa"):
        attached = writer.add_attachment(name, credential() if payload is None else payload)
        spec = attached.pdf_object
        spec[NameObject("/AFRelationship")] = NameObject("/C2PA_Manifest")
        stream = spec["/EF"]["/F"].get_object()
        stream[NameObject("/Subtype")] = NameObject("/application/c2pa")
        return spec, stream

    def assert_ordinary(self, writer):
        report, issues = self.inspect(writer)
        self.assertTrue(report["complete"])
        self.assertEqual(0, report["content_credentials"])
        self.assertEqual(1, report["ordinary_attachments"])
        self.assertTrue(any(issue.check == "attachments" and issue.severity == "ERROR" for issue in issues))
        return report

    def test_c2pa_is_separate_and_duplicate_filespec_references_keep_raw_counts(self):
        writer = self.writer()
        spec, _stream = self.attach_credential(writer)
        reference = writer._add_object(spec)
        writer.root_object[NameObject("/AF")] = ArrayObject([reference, reference])
        writer.pages[0][NameObject("/AF")] = ArrayObject([reference])
        annotation = DictionaryObject({NameObject("/Subtype"): NameObject("/FileAttachment"), NameObject("/FS"): reference})
        writer.pages[0][NameObject("/Annots")] = ArrayObject([writer._add_object(annotation)])
        report, issues = self.inspect(writer)
        self.assertTrue(report["complete"])
        self.assertEqual((1, 3, 1), (report["embedded_files"], report["associated_files"], report["file_attachment_annotations"]))
        self.assertEqual((1, 1, 0), (report["attachment_filespecs"], report["content_credentials"], report["ordinary_attachments"]))
        self.assertEqual(4, len(report["attachment_details"][0]["sources"]))
        self.assertFalse(any(issue.severity in ("ERROR", "WARN") for issue in issues))
        self.assertTrue(any(issue.check == "content-credentials" and issue.severity == "INFO" for issue in issues))
        self.assertIn("unchecked", report["credential_validation"])

    def test_multiple_manifests_and_multiple_credentials_are_not_restricted_to_one(self):
        for framing in ({}, {"extended": True}, {"to_eof": True}):
            with self.subTest(framing=framing):
                writer = self.writer()
                self.attach_credential(writer, credential(b"c2ma", b"c2um", b"c2md", **framing))
                self.attach_credential(writer, name="second.c2pa")
                report, issues = self.inspect(writer)
                self.assertEqual((2, 0), (report["content_credentials"], report["ordinary_attachments"]))
                self.assertFalse(any(issue.severity == "ERROR" for issue in issues))

    def test_ordinary_file_alongside_a_credential_is_still_an_error(self):
        writer = self.writer()
        self.attach_credential(writer)
        writer.add_attachment("notes.txt", b"ordinary notes")
        report, issues = self.inspect(writer)
        self.assertEqual((2, 1, 1), (report["embedded_files"], report["content_credentials"], report["ordinary_attachments"]))
        self.assertTrue(any(issue.check == "attachments" and issue.severity == "ERROR" for issue in issues))

    def test_filename_or_filespec_mime_cannot_spoof_an_embedded_stream(self):
        for mode in ("name", "relationship-string", "filespec-mime", "wrong-mime", "stream-mime-string"):
            with self.subTest(mode=mode):
                writer = self.writer()
                spec, stream = self.attach_credential(writer, name="Content Credentials")
                if mode == "name":
                    del spec["/AFRelationship"]
                elif mode == "relationship-string":
                    spec[NameObject("/AFRelationship")] = TextStringObject("/C2PA_Manifest")
                elif mode == "filespec-mime":
                    del stream["/Subtype"]
                    spec[NameObject("/Subtype")] = NameObject("/application/c2pa")
                elif mode == "wrong-mime":
                    stream[NameObject("/Subtype")] = NameObject("/text/plain")
                else:
                    stream[NameObject("/Subtype")] = TextStringObject("/application/c2pa")
                self.assert_ordinary(writer)

    def test_every_distinct_ef_stream_is_checked_but_aliases_are_not_double_counted(self):
        writer = self.writer()
        spec, _stream = self.attach_credential(writer)
        embedded = spec["/EF"]
        embedded[NameObject("/UF")] = embedded.raw_get("/F")
        report, issues = self.inspect(writer)
        self.assertEqual(1, report["content_credentials"])
        self.assertFalse(any(issue.severity == "ERROR" for issue in issues))
        ordinary = DecodedStreamObject()
        ordinary.set_data(b"not a JUMBF container")
        ordinary[NameObject("/Subtype")] = NameObject("/application/c2pa")
        embedded[NameObject("/UF")] = writer._add_object(ordinary)
        self.assert_ordinary(writer)

    def test_different_filespecs_sharing_the_same_stream_are_not_merged(self):
        writer = self.writer()
        spec, _stream = self.attach_credential(writer)
        other = DictionaryObject(dict(spec))
        writer.root_object[NameObject("/AF")] = ArrayObject([writer._add_object(spec), writer._add_object(other)])
        report, issues = self.inspect(writer)
        self.assertEqual((2, 2), (report["attachment_filespecs"], report["content_credentials"]))
        self.assertFalse(any(issue.severity == "ERROR" for issue in issues))

    def test_malformed_or_mislabeled_jumbf_remains_an_attachment_error(self):
        description = box(b"jumd", b"c2pa" + UUID_TAIL + b"\3c2pa\0")
        manifest = jumb(b"c2ma", "urn:uuid:legacy-label", box(b"cbor", b"\xa0"))
        invalid = {
            "text": b"Content Credentials c2pa",
            "wrong-store-type": jumb(b"nope", "c2pa", manifest),
            "wrong-store-label": jumb(b"c2pa", "not-c2pa", manifest),
            "no-manifest": jumb(b"c2pa", "c2pa", box(b"xml ", b"extension")),
            "empty-manifest": jumb(b"c2pa", "c2pa", jumb(b"c2ma", "manifest", b"")),
            "truncated": credential()[:-1],
            "trailing-byte": credential() + b"x",
            "reserved-length": b"\0\0\0\7jumb",
            "duplicate-description": box(b"jumb", description + description + manifest),
            "description-not-first": box(b"jumb", manifest + description),
            "unterminated-label": box(b"jumb", box(b"jumd", b"c2pa" + UUID_TAIL + b"\3c2pa") + manifest),
            "zero-child-in-sized-parent": box(b"jumb", description + box(b"jumb", b"payload", to_eof=True)),
        }
        for label, payload in invalid.items():
            with self.subTest(label=label):
                writer = self.writer()
                self.attach_credential(writer, payload)
                self.assert_ordinary(writer)

    def link(self, writer, target):
        annotation = DictionaryObject({
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Link"),
            NameObject("/Rect"): ArrayObject([NumberObject(x) for x in (0, 0, 10, 10)]),
            NameObject("/Dest"): TextStringObject(target) if isinstance(target, str) else target,
        })
        annotations = writer.pages[0].setdefault(NameObject("/Annots"), ArrayObject())
        annotations.append(writer._add_object(annotation))

    def test_nested_outlines_named_link_and_external_link(self):
        writer = self.writer()
        parent = writer.add_outline_item("Chapter", 0)
        writer.add_outline_item("Lemma", 1, parent=parent)
        writer.add_named_destination("lemma", 1)
        self.link(writer, "lemma")
        from pypdf.annotations import Link
        writer.add_annotation(0, Link(rect=(0, 0, 10, 10), url="https://example.org"))
        # Use a real local page reference; pypdf 6.10 Link writes an integer.
        self.link(writer, ArrayObject([writer.pages[1].indirect_reference, NameObject("/Fit")]))
        report, issues = self.inspect(writer)
        self.assertEqual([], issues)
        self.assertTrue(report["complete"])
        self.assertEqual(2, report["outlines"])
        self.assertEqual(2, report["internal_links"])
        self.assertEqual(1, report["named_destinations"])

    def test_unresolved_named_link_is_an_error(self):
        writer = self.writer()
        self.link(writer, "missing")
        report, issues = self.inspect(writer)
        self.assertTrue(report["complete"])
        self.assertTrue(any(x.check == "navigation" and x.severity == "ERROR" and x.pages == [1] for x in issues))

    def test_non_page_reference_in_local_link_is_an_error(self):
        writer = self.writer()
        self.link(writer, ArrayObject([NumberObject(1), NameObject("/Fit")]))
        report, issues = self.inspect(writer)
        self.assertTrue(report["complete"])
        self.assertTrue(any(x.check == "navigation" and x.severity == "ERROR" for x in issues))

    def test_broken_outline_and_residue_are_detected(self):
        writer = self.writer()
        outline = writer.add_outline_item("CONTROL_MARKER", 0).get_object()
        outline[NameObject("/Dest")] = TextStringObject("missing")
        del outline["/A"]
        report, issues = self.inspect(writer, ["CONTROL_MARKER"])
        self.assertTrue(report["complete"])
        self.assertEqual({"navigation", "engineering-residue"}, {x.check for x in issues})

    def test_outline_heading_without_destination_is_valid(self):
        writer = self.writer()
        outline = writer.add_outline_item("Heading", 0).get_object()
        del outline["/A"]
        report, issues = self.inspect(writer)
        self.assertTrue(report["complete"])
        self.assertEqual([], issues)

    def test_embedded_file_is_an_error(self):
        writer = self.writer()
        writer.add_attachment("notes.txt", b"private notes")
        report, issues = self.inspect(writer)
        self.assertEqual(1, report["embedded_files"])
        self.assertTrue(any(x.check == "attachments" and x.severity == "ERROR" for x in issues))

    def test_attachment_annotation_outside_name_tree_is_detected(self):
        writer = self.writer()
        annotation = DictionaryObject({NameObject("/Subtype"): NameObject("/FileAttachment")})
        writer.pages[0][NameObject("/Annots")] = ArrayObject([writer._add_object(annotation)])
        report, issues = self.inspect(writer)
        self.assertEqual(1, report["file_attachment_annotations"])
        self.assertTrue(any(x.check == "attachments" for x in issues))

    def test_unreadable_pdf_does_not_report_completed_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "broken.pdf"
            path.write_bytes(b"not a PDF")
            issues = []
            report = CHECK(path, [], issues)
            self.assertFalse(report["complete"])
            self.assertTrue(any(x.severity == "ERROR" for x in issues))


if __name__ == "__main__":
    unittest.main()
