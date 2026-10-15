import math
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from PySide6.QtCore import QObject, QTimer, Signal

from src.misa_ia.domain.measurement import (
    DataSource,
    Measurement,
    VitalParameter,
)


HORARIO_BRASIL = ZoneInfo(
    "America/Sao_Paulo"
)


class SimuladorSinaisVitais:

    def __init__(
        self,
        patient_id: str,
        session_id: str,
        seed: int | None = None,
    ):
        self.patient_id = patient_id
        self.session_id = session_id

        self.random = random.Random(seed)

        self.passo = 0

        self.baseline = {
            VitalParameter.SPO2: 98.0,
            VitalParameter.TEMPERATURE: 37.5,
            VitalParameter.MEAN_ARTERIAL_PRESSURE: 85.0,
        }

        self.units = {
            VitalParameter.SPO2: "%",
            VitalParameter.TEMPERATURE: "°C",
            VitalParameter.MEAN_ARTERIAL_PRESSURE: "mmHg",
        }

    @staticmethod
    def _limit(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:

        return max(
            minimum,
            min(maximum, value),
        )

    def _generate_spo2(self) -> float:

        baseline = self.baseline[
            VitalParameter.SPO2
        ]

        value = (
            baseline
            + 0.25 * math.sin(
                self.passo / 8.0
            )
            + self.random.gauss(
                0,
                0.15,
            )
        )

        value = self._limit(
            value,
            0.0,
            100.0,
        )

        return round(value, 2)

    def _generate_temperature(self) -> float:

        baseline = self.baseline[
            VitalParameter.TEMPERATURE
        ]

        value = (
            baseline
            + 0.08 * math.sin(
                self.passo / 15.0
            )
            + self.random.gauss(
                0,
                0.02,
            )
        )

        return round(value, 2)

    def _generate_pressure(self) -> float:

        baseline = self.baseline[
            VitalParameter.MEAN_ARTERIAL_PRESSURE
        ]

        value = (
            baseline
            + 2.0 * math.sin(
                self.passo / 7.0
            )
            + self.random.gauss(
                0,
                0.8,
            )
        )

        value = self._limit(
            value,
            20.0,
            200.0,
        )

        return round(value, 2)

    def generate_snapshot(
        self,
        timestamp: datetime | None = None,
    ) -> list[Measurement]:

        if timestamp is None:
            timestamp = datetime.now(
                HORARIO_BRASIL
            )

        self.passo += 1

        values = {
            VitalParameter.SPO2:
                self._generate_spo2(),

            VitalParameter.TEMPERATURE:
                self._generate_temperature(),

            VitalParameter.MEAN_ARTERIAL_PRESSURE:
                self._generate_pressure(),
        }

        measurements = []

        for parameter, value in values.items():

            measurement = Measurement(
                patient_id=self.patient_id,
                session_id=self.session_id,
                timestamp=timestamp,
                parameter=parameter,
                value=value,
                unit=self.units[parameter],
                source=DataSource.SIMULATOR,
                signal_quality=round(
                    self.random.uniform(
                        0.95,
                        1.0,
                    ),
                    2,
                ),
            )

            measurements.append(
                measurement
            )

        return measurements

    def generate_series(
        self,
        duration_minutes: int,
        interval_seconds: int = 5,
        start_time: datetime | None = None,
    ) -> list[Measurement]:

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

            timestamp = (
                start_time
                + timedelta(
                    seconds=elapsed_seconds
                )
            )

            snapshot = self.generate_snapshot(
                timestamp
            )

            measurements.extend(
                snapshot
            )

        return measurements

class SinalVitalSimulacao(QObject):

    measurement_generated = Signal(object)

    def __init__(
        self,
        patient_id: str,
        session_id: str,
        parent=None,
        seed: int | None = None,
    ):
        super().__init__(parent)

        self.simulator = SimuladorSinaisVitais(
            patient_id=patient_id,
            session_id=session_id,
            seed=seed,
        )

        self.current_time = datetime.now(
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
                self.current_time
            )
        )

        self.measurement_generated.emit(
            measurements
        )

        self.current_time += timedelta(
            seconds=2
        )