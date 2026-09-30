import pandas as pd

from energy_assistant.data import minute_data


def test_cleaned_dataset_has_expected_meter_columns():
    frame = minute_data()
    assert isinstance(frame, pd.DataFrame)
    for col in ["Global_active_power", "Global_reactive_power", "Voltage", "Global_intensity", "Sub_metering_1", "Sub_metering_2", "Sub_metering_3"]:
        assert col in frame.columns
    assert frame.index.is_monotonic_increasing
