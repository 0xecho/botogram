"""
    Tests for botogram/objects/__init__.py

    Copyright (c) 2015 Pietro Albini <pietro@pietroalbini.io>
    Released under the MIT license
"""

import pytest

import botogram.objects


def test_user_avatar(api, mock_req):
    mock_req({
        "getUserProfilePhotos": {
            "ok": True,
            "result": {
                "total_count": 1,
                "photos": [
                    [
                        {
                            "file_id": "aaaaaa",
                            "width": 50,
                            "height": 50,
                            "file_size": 128,
                        },
                        {
                            "file_id": "bbbbbb",
                            "width": 25,
                            "height": 25,
                            "file_size": 64,
                        },
                    ],
                ],
            },
        },
    })

    # First of all, make sure the API wrapper is required to fetch avatars
    user = botogram.objects.User({"id": 123, "first_name": "Bob"})
    with pytest.raises(RuntimeError):
        user.avatar  # Access the avatar without an API wrapper

    # Now use an API
    user = botogram.objects.User({"id": 123, "first_name": "Bob"}, api)

    # Be sure the avatar isn't loaded yet
    assert not hasattr(user, "_avatar")

    # Now fetch the avatar
    avatar = user.avatar
    assert avatar.file_id == "aaaaaa"

    # And be sure it's cached
    assert hasattr(user, "_avatar")
    assert user._avatar == avatar


def test_user_avatar_with_no_photos(api, mock_req):
    mock_req({
        "getUserProfilePhotos": {
            "ok": True,
            "result": {
                "total_count": 0,
                "photos": [],
            },
        },
    })

    user = botogram.objects.User({"id": 123, "first_name": "Bob"}, api)
    assert user.avatar is None


def test_user_avatar_history(api, mock_req):
    mock_req({
        "getUserProfilePhotos": {
            "ok": True,
            "result": {
                "total_count": 3,
                "photos": [
                    [
                        {
                            "file_id": "aaaaaa",
                            "width": 50,
                            "height": 50,
                            "file_size": 128,
                        },
                    ],
                    [
                        {
                            "file_id": "bbbbbb",
                            "width": 50,
                            "height": 50,
                            "file_size": 128,
                        },
                    ],
                    [
                        {
                            "file_id": "cccccc",
                            "width": 50,
                            "height": 50,
                            "file_size": 128,
                        },
                    ],
                ],
            },
        },
    })

    # First of all, make sure the API wrapper is required to fetch avatars
    user = botogram.objects.User({"id": 123, "first_name": "Bob"})
    with pytest.raises(RuntimeError):
        user.avatar_history()  # Access the avatar without an API wrapper

    # Now use an API
    user = botogram.objects.User({"id": 123, "first_name": "Bob"}, api)

    files = [avatar.file_id for avatar in user.avatar_history()]
    assert files == ["aaaaaa", "bbbbbb", "cccccc"]


def test_user_avatar_history_multiple_requests(api, mock_req):
    mock_req({
        "getUserProfilePhotos": {
            "ok": True,
            "result": {
                # This is the double of the avatars provided with this request
                # This simulates if the user has more than 100 avatars
                "total_count": 4,
                "photos": [
                    [
                        {
                            "file_id": "aaaaaa",
                            "width": 50,
                            "height": 50,
                            "file_size": 128,
                        },
                    ],
                    [
                        {
                            "file_id": "bbbbbb",
                            "width": 50,
                            "height": 50,
                            "file_size": 128,
                        },
                    ],
                ],
            },
        },
    })

    user = botogram.objects.User({"id": 123, "first_name": "Bob"}, api)

    files = [avatar.file_id for avatar in user.avatar_history()]
    assert files == ["aaaaaa", "bbbbbb", "aaaaaa", "bbbbbb"]


def test_user_avatar_history_no_photos(api, mock_req):
    mock_req({
        "getUserProfilePhotos": {
            "ok": True,
            "result": {
                "total_count": 0,
                "photos": [],
            },
        },
    })

    user = botogram.objects.User({"id": 123, "first_name": "Bob"}, api)
    assert user.avatar_history() == []


def test_photo_object():
    # The Photo object is custom-made, so it's better to ensure all it's
    # working as expected
    data = [
        {"file_id": "aaaaaa", "width": 10, "height": 10, "file_size": 48},
        {"file_id": "aaaaaa", "width": 20, "height": 20, "file_size": 148},
        {"file_id": "aaaaaa", "width": 30, "height": 30, "file_size": 248},
    ]

    # Let's create a valid Photo object
    photo = botogram.objects.Photo(data)
    assert len(photo.sizes) == len(data)
    assert photo.sizes[0].file_id == data[0]["file_id"]
    assert photo.smallest.file_id == data[0]["file_id"]
    assert photo.biggest.file_id == data[-1]["file_id"]
    assert photo.biggest.file_id == photo.file_id
    assert photo.serialize() == data

    # Test if set_api is working
    photo2 = botogram.objects.Photo(data, "testapi")
    assert photo2._api == "testapi"
    assert photo2.sizes[0]._api == "testapi"
    photo2.set_api("anotherapi")
    assert photo2._api == "anotherapi"
    assert photo2.sizes[0]._api == "anotherapi"

    # Empty PhotoSize not supported, sorry
    with pytest.raises(ValueError):
        botogram.objects.Photo([])

    # The data provided must be a list
    with pytest.raises(ValueError):
        botogram.objects.Photo("I'm not a list (doh)")

    # And the items inside a list must be PhotoSize
    with pytest.raises(ValueError):
        botogram.objects.Photo([{"This": "isn't", "a": "PhotoSize"}])
