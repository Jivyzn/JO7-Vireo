from vireo.assistant import get_world_time, split_text_into_chunks


def test_split_text_prefers_sentence_boundaries():
    chunks = split_text_into_chunks("One short sentence. Another short sentence.", max_chars=25)
    assert chunks == ["One short sentence.", "Another short sentence."]


def test_unknown_city_is_handled_offline():
    assert "do not have" in get_world_time("Atlantis")
