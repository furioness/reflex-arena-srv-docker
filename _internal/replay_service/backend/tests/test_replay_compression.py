import zipfile

from src.db import ReplayDB


def test_rep_is_actually_compressed(aerowalk_db, replay_dir, copy_replay):
    # arrange
    replay_filename = "Aerowalk_Ivan_O__Vigur_24Nov2025_183934_0markers.rep"
    rep_path = copy_replay(replay_filename)
    original_size = rep_path.stat().st_size

    # act: DB init triggers compression
    ReplayDB(aerowalk_db, replay_dir, _chunk_at_count=3)

    zip_path = rep_path.with_suffix(".rep.zip")
    assert zip_path.exists()

    # assert: compressed size is smaller
    compressed_size = zip_path.stat().st_size
    assert compressed_size < original_size, (
        f"Expected compressed replay to be smaller "
        f"(orig={original_size}, zip={compressed_size})"
    )

    # assert: correct archive
    with zipfile.ZipFile(zip_path) as z:
        info = z.infolist()[0]
        assert info.compress_type == zipfile.ZIP_DEFLATED
        assert info.compress_size < info.file_size
