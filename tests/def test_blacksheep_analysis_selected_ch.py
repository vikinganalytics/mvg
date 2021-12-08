def test_blacksheep_analysis_selected_channels(
    session,
    waveform_source_multiaxial_001,
    waveform_source_multiaxial_002,
    waveform_source_multiaxial_003,
):
    source_id_001, _ = waveform_source_multiaxial_001
    source_id_002, _ = waveform_source_multiaxial_002
    source_id_003, _ = waveform_source_multiaxial_003
    source_info_001 = session.get_source(source_id_001)
    channels = source_info_001["properties"]["channels"]

    def assert_results(selected_channels):
        print(selected_channels)
        req = session.request_population_analysis(
            [source_id_001, source_id_002, source_id_003],
            "BlackSheep",
            {},
            selected_channels=selected_channels,
        )
        session.wait_for_analyses([req["request_id"]])
        results = session.get_analysis_results(req["request_id"])
        print(results)
        # assert results["inputs"]["selected_channels"] == (selected_channels or [])

    # Test with defined selected_channels
    assert_results(channels[:2])

    # Test with defined selected_channels
    # assert_results(None)
