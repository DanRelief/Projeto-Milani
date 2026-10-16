import math
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from PySide6.QtCore import QObject, QTimer, Signal

from src.domain.measurement import (
    FonteDados,
    Medicao,
    Vitalparametro,
)


HORARIO_BRASIL = ZoneInfo(
    "America/Sao_Paulo"
)


class SimuladorSinaisVitais:

    def __init__(
        self,
        id_paciente: str,
        id_sessao: str,
        seed: int | None = None,
    ):
        self.id_paciente = id_paciente
        self.id_sessao = id_sessao

        self.random = random.Random(seed)

        self.passo = 0

        self.baseline = {
            Vitalparametro.SPO2: 98.0,
            Vitalparametro.TEMPERATURA: 37.5,
            Vitalparametro.PRESSAO_ARTERIAL_MEDIA: 85.0,
        }

        self.units = {
            Vitalparametro.SPO2: "%",
            Vitalparametro.TEMPERATURA: "°C",
            Vitalparametro.PRESSAO_ARTERIAL_MEDIA: "mmHg",
        }

    @staticmethod
    def _limit(
        valor: float,
        minimo: float,
        maximo: float,
    ) -> float:

        return max(
            minimo,
            min(maximo, valor),
        )

    def _generate_spo2(self) -> float:

        baseline = self.baseline[
            Vitalparametro.SPO2
        ]

        valor = (
            baseline
            + 0.25 * math.sin(
                self.passo / 8.0
            )
            + self.random.gauss(
                0,
                0.15,
            )
        )

        valor = self._limit(
            valor,
            0.0,
            100.0,
        )

        return round(valor, 2)

    def _generate_temperature(self) -> float:

        baseline = self.baseline[
            Vitalparametro.TEMPERATURA
        ]

        valor = (
            baseline
            + 0.08 * math.sin(
                self.passo / 15.0
            )
            + self.random.gauss(
                0,
                0.02,
            )
        )

        return round(valor, 2)

    def _generate_pressure(self) -> float:

        baseline = self.baseline[
            Vitalparametro.PRESSAO_ARTERIAL_MEDIA
        ]

        valor = (
            baseline
            + 2.0 * math.sin(
                self.passo / 7.0
            )
            + self.random.gauss(
                0,
                0.8,
            )
        )

        valor = self._limit(
            valor,
            20.0,
            200.0,
        )

        return round(valor, 2)

    def generate_snapshot(
        self,
        data_hora: datetime | None = None,
    ) -> list[Medicao]:

        if data_hora is None:
            data_hora = datetime.now(
                HORARIO_BRASIL
            )

        self.passo += 1

        valors = {
            Vitalparametro.SPO2:
                self._generate_spo2(),

            Vitalparametro.TEMPERATURA:
                self._generate_temperature(),

            Vitalparametro.PRESSAO_ARTERIAL_MEDIA:
                self._generate_pressure(),
        }

        measurements = []

        for parametro, valor in valors.items():

            medicao = Medicao(
                id_paciente=self.id_paciente,
                id_sessao=self.id_sessao,
                data_hora=data_hora,
                parametro=parametro,
                valor=valor,
                unidade=self.units[parametro],
                fonte=FonteDados.SIMULADOR,
                qualidade_sinal=round(self.random.uniform(0.95,1.0,),2),
            )

            measurements.append(medicao)

        return measurements

    def generate_series(
        self,
        duration_minutes: int,
        interval_seconds: int = 5,
        start_time: datetime | None = None,
    ) -> list[Medicao]:

        if duration_minutes <= 0:
            raise ValueError(
                "duration_minutes deve ser maior que zero."
            )

        if interval_seconds <= 0:
            raise ValueError(
                "interval_seconds deve ser maior que zero."
            )

        if start_time is None:
            start_time = datetime.now(
                HORARIO_BRASIL
            )

        measurements = []

        total_seconds = (
            duration_minutes * 60
        )

        for elapsed_seconds in range(
            0,
            total_seconds,
            interval_seconds,
        ):

            data_hora = (
                start_time
                + timedelta(
                    seconds=elapsed_seconds
                )
            )

            snapshot = self.generate_snapshot(
                data_hora
            )

            measurements.extend(
                snapshot
            )

        return measurements

class SinalVitalSimulacao(QObject):

    measurement_generated = Signal(object)

    def __init__(
        self,
        id_paciente: str,
        id_sessao: str,
        parent=None,
        seed: int | None = None,
    ):
        super().__init__(parent)

        self.simulator = SimuladorSinaisVitais(
            id_paciente=id_paciente,
            id_sessao=id_sessao,
            seed=seed,
        )

        self.valor_atual_time = datetime.now(
            HORARIO_BRASIL
        )

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.generate_measurement
        )

    def start(self):
        self.generate_measurement()
        self.timer.start(2000)

    def stop(self):
        self.timer.stop()

    def generate_measurement(self):

        measurements = (
            self.simulator.generate_snapshot(
                self.valor_atual_time
            )
        )

        self.measurement_generated.emit(
            measurements
        )

        self.valor_atual_time += timedelta(
            seconds=2
        )
