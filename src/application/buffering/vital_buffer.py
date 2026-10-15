from collections import defaultdict, deque
from datetime import timedelta

from domain.measurement import (
    Measurement,
    VitalParameter,
)


class VitalBuffer:

    def __init__(
        self,
        patient_id: str,
        session_id: str,
        max_minutes: int = 30,
    ):
        self.patient_id = patient_id
        self.session_id = session_id

        self.max_duration = timedelta(
            minutes=max_minutes
        )

        self._data: dict[
            VitalParameter,
            deque[Measurement]
        ] = defaultdict(deque)

    def add(
        self,
        measurement: Measurement,
    ) -> None:

        if (
            measurement.patient_id
            != self.patient_id
        ):
            raise ValueError(
                "Measurement pertence a outro paciente."
            )

        if (
            measurement.session_id
            != self.session_id
        ):
            raise ValueError(
                "Measurement pertence a outra sessão."
            )

        measurements = self._data[
            measurement.parameter
        ]

        if measurements:
            last_timestamp = (
                measurements[-1].timestamp
            )

            if (
                measurement.timestamp
                < last_timestamp
            ):
                raise ValueError(
                    "Measurement fora de ordem temporal."
                )

        measurements.append(
            measurement
        )

        self._remove_old_measurements(
            measurement.timestamp
        )

    def add_many(
        self,
        measurements: list[Measurement],
    ) -> None:

        for measurement in measurements:
            self.add(measurement)


    def _remove_old_measurements(
        self,
        reference_timestamp,
    ) -> None:

        cutoff = (
            reference_timestamp
            - self.max_duration
        )

        for measurements in (
            self._data.values()
        ):

            while (
                measurements
                and
                measurements[0].timestamp
                < cutoff
            ):
                measurements.popleft()

    def get_all(
        self,
        parameter: VitalParameter,
    ) -> list[Measurement]:

        return list(
            self._data.get(
                parameter,
                []
            )
        )

    def get_recent(
        self,
        parameter: VitalParameter,
        minutes: float,
    ) -> list[Measurement]:

        measurements = self._data.get(
            parameter,
            []
        )

        if not measurements:
            return []

        latest_timestamp = (
            measurements[-1].timestamp
        )

        cutoff = (
            latest_timestamp
            - timedelta(minutes=minutes)
        )

        return [
            measurement
            for measurement in measurements
            if measurement.timestamp >= cutoff
        ]

    def latest(
        self,
        parameter: VitalParameter,
    ) -> Measurement | None:

        measurements = self._data.get(
            parameter
        )

        if not measurements:
            return None

        return measurements[-1]

    def count(
        self,
        parameter: VitalParameter,
    ) -> int:

        return len(
            self._data.get(
                parameter,
                []
            )
        )