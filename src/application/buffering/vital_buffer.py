from collections import defaultdict, deque
from datetime import timedelta

from domain.measurement import (
    Measurement,
    Vitalparametro,
)


class VitalBuffer:

    def __init__(
        self,
        id_paciente: str,
        id_sessao: str,
        max_minutes: int = 30,
    ):
        self.id_paciente = id_paciente
        self.id_sessao = id_sessao

        self.max_duration = timedelta(
            minutes=max_minutes
        )

        self._data: dict[
            Vitalparametro,
            deque[Measurement]
        ] = defaultdict(deque)

    def add(
        self,
        measurement: Measurement,
    ) -> None:

        if (
            measurement.id_paciente
            != self.id_paciente
        ):
            raise ValueError(
                "Measurement pertence a outro paciente."
            )

        if (
            measurement.id_sessao
            != self.id_sessao
        ):
            raise ValueError(
                "Measurement pertence a outra sessão."
            )

        measurements = self._data[
            measurement.parametro
        ]

        if measurements:
            last_data_hora = (
                measurements[-1].data_hora
            )

            if (
                measurement.data_hora
                < last_data_hora
            ):
                raise ValueError(
                    "Measurement fora de ordem temporal."
                )

        measurements.append(
            measurement
        )

        self._remove_old_measurements(
            measurement.data_hora
        )

    def add_many(
        self,
        measurements: list[Measurement],
    ) -> None:

        for measurement in measurements:
            self.add(measurement)


    def _remove_old_measurements(
        self,
        reference_data_hora,
    ) -> None:

        cutoff = (
            reference_data_hora
            - self.max_duration
        )

        for measurements in (
            self._data.values()
        ):

            while (
                measurements
                and
                measurements[0].data_hora
                < cutoff
            ):
                measurements.popleft()

    def get_all(
        self,
        parametro: Vitalparametro,
    ) -> list[Measurement]:

        return list(
            self._data.get(
                parametro,
                []
            )
        )

    def get_recent(
        self,
        parametro: Vitalparametro,
        minutes: float,
    ) -> list[Measurement]:

        measurements = self._data.get(
            parametro,
            []
        )

        if not measurements:
            return []

        latest_data_hora = (
            measurements[-1].data_hora
        )

        cutoff = (
            latest_data_hora
            - timedelta(minutes=minutes)
        )

        return [
            measurement
            for measurement in measurements
            if measurement.data_hora >= cutoff
        ]

    def latest(
        self,
        parametro: Vitalparametro,
    ) -> Measurement | None:

        measurements = self._data.get(
            parametro
        )

        if not measurements:
            return None

        return measurements[-1]

    def count(
        self,
        parametro: Vitalparametro,
    ) -> int:

        return len(
            self._data.get(
                parametro,
                []
            )
        )