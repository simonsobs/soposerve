from hipposerve.service import versioning


def test_version_revision():
    starting = "2.1.3"

    assert (
        versioning.revise_version(starting, versioning.VersionRevision.MAJOR) == "3.0.0"
    )
    assert (
        versioning.revise_version(starting, versioning.VersionRevision.MINOR) == "2.2.0"
    )
    assert (
        versioning.revise_version(starting, versioning.VersionRevision.PATCH) == "2.1.4"
    )
