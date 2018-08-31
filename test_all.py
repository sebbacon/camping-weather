def test_coord_to_decimal():
    from get_data import coord_to_decimal
    # W is negative
    subjects = (
        ("Lat=54-39N Lon=006-13W", (54.65, -6.217)),
        ("Lat=49-55N Lon=006-18W", (49.917, -6.3)),
        ("Lat=52-52N Lon=000-09E Alt=3 m", (52.867, 0.15)),
        ("br>Lat=53-28-29N Lon=000-09-10E", (53.475, 0.153)),
    )
    for in_, expected in subjects:
        lat, lon = coord_to_decimal(in_)
        assert (lat, lon) == expected
