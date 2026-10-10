import os
from uuid import uuid4

import pytest
from app import media, photo_storage
from app.models import AlbumPhoto, Base, MediaAsset, PhotoAlbum, User
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


class FakeStorage:
    enabled = True
    configured = True

    def __init__(self):
        self.deleted: list[str] = []

    def delete(self, key: str) -> None:
        self.deleted.append(key)


@pytest.fixture
def storage(monkeypatch):
    store = FakeStorage()
    monkeypatch.setattr(photo_storage, "get_storage", lambda: store)
    return store


@pytest.fixture
def db(tmp_path):
    url = os.environ.get("TEST_DATABASE_URL")
    engine = create_engine(url or f"sqlite:///{tmp_path}/albums.db")
    if url:
        assert engine.url.database.endswith("_test")
    else:
        Base.metadata.create_all(engine)
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(connection, join_transaction_mode="create_savepoint") as session:
            yield session
        transaction.rollback()
    engine.dispose()


@pytest.fixture
def admin(db):
    user = User(
        id=uuid4(),
        normalized_email=f"{uuid4()}@example.com",
        password_hash="unused",
        role="admin",
    )
    db.add(user)
    db.commit()
    return user


def add_album(db, admin, title, *, enabled=False):
    album = PhotoAlbum(
        title=title,
        created_by=admin.id,
        background_enabled=enabled,
    )
    db.add(album)
    db.commit()
    return album


def add_photo(db, admin, album, key="media/photo"):
    asset = MediaAsset(
        uploaded_by=admin.id,
        content_type="image/jpeg",
        size_bytes=12,
        storage_key=key,
        status="visible",
    )
    db.add(asset)
    db.flush()
    db.add(AlbumPhoto(album_id=album.id, media_id=asset.id))
    db.commit()
    return asset


def test_enabling_album_disables_previous_background_album(db, admin):
    previous = add_album(db, admin, "Previous", enabled=True)
    current = add_album(db, admin, "Current")

    result = media.update_album(
        current.id,
        media.AlbumUpdate(
            background_enabled=True,
            background_interval_seconds=12,
            background_transition="zoom",
        ),
        db,
        admin,
    )

    db.refresh(previous)
    assert previous.background_enabled is False
    assert result.background_enabled is True
    assert result.background_interval_seconds == 12
    assert result.background_transition == "zoom"


def test_selected_album_photo_is_returned_as_background(db, admin):
    album = add_album(db, admin, "Team", enabled=True)
    photo = add_photo(db, admin, album)

    media.update_album_photo(
        album.id,
        photo.id,
        media.AlbumPhotoUpdate(use_as_background=True),
        db,
        admin,
    )

    result = media.backgrounds(db)
    assert result.album_id == album.id
    assert [item.id for item in result.photos] == [photo.id]
    assert result.photos[0].use_as_background is True


def test_deleting_album_removes_unshared_photo_and_storage_object(db, admin, storage):
    album = add_album(db, admin, "Disposable")
    photo = add_photo(db, admin, album, key="media/disposable")

    media.delete_album(album.id, db, admin)

    assert db.get(PhotoAlbum, album.id) is None
    assert db.get(MediaAsset, photo.id) is None
    assert storage.deleted == ["media/disposable"]


def test_deleting_album_preserves_photo_shared_with_another_album(db, admin, storage):
    first = add_album(db, admin, "First")
    second = add_album(db, admin, "Second")
    photo = add_photo(db, admin, first, key="media/shared")
    db.add(AlbumPhoto(album_id=second.id, media_id=photo.id))
    db.commit()

    media.delete_album(first.id, db, admin)

    assert db.get(MediaAsset, photo.id) is not None
    assert db.scalar(select(AlbumPhoto).where(AlbumPhoto.album_id == second.id)) is not None
    assert storage.deleted == []
