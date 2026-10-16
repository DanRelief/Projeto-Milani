from collections import defaultdict, deque
from datetime import timedelta

from src.domain.measurement import (
    Medicao,
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
            deque[Medicao]
        ] = defaultdict(deque)

    def add(
        self,
        Medicao: Medicao,
    ) -> None:

        if (
            Medicao.id_paciente
            != self.id_paciente
        ):
            raise ValueError(
                "Medicao pertence a outro paciente."
            )

        if (
            Medicao.id_sessao
            != self.id_sessao
        ):
            raise ValueError(
                "Medicao pertence a outra sessão."
            )

        measurements = self._data[
            Medicao.parametro
        ]

        if measurements:
            last_data_hora = (
                measurements[-1].data_hora
            )

            if (
                Medicao.data_hora
                < last_data_hora
            ):
                raise ValueError(
                    "Medicao fora de ordem temporal."
                )

        measurements.append(
            Medicao
        )

        self._remove_old_measurements(
            Medicao.data_hora
        )

    def add_many(
        self,
        measurements: list[Medicao],
    ) -> None:

        for Medicao in measurements:
            self.add(Medicao)


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
    ) -> list[Medicao]:

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
    ) -> list[Medicao]:

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
            Medicao
            for Medicao in measurements
            if Medicao.data_hora >= cutoff
        ]

    def latest(
        self,
        parametro: Vitalparametro,
    ) -> Medicao | None:

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