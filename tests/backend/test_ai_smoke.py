def test_litellm_importable():
    import litellm
    assert hasattr(litellm, "completion")
    assert hasattr(litellm, "acompletion")
