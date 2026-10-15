import math
import random
from datetime import datetime, timedelta

from src.misa_ia.domain.measurement import (
    DataSource,
    Measurement,
    VitalParameter,
)


class SimuladorSinaisVitais:

    def __init__(
        self,
        patient_id: str,
        session_id: str,
        seed: int | None = None
    ):
        self.patient_id = patient_id
        self.session_id = session_id

        self.random = random.Random(seed)

        # Valores-base exclusivamente para simulação.
        self.baseline = {
            VitalParameter.HEART_RATE: 95.0,
            VitalParameter.RESPIRATORY_RATE: 20.0,
            VitalParameter.SPO2: 98.0,
            VitalParameter.TEMPERATURE: 38.2,
            VitalParameter.MEAN_ARTERIAL_PRESSURE: 80.0,
        }

        # Estado atual da simulação.
        self.current_values = self.baseline.copy()

        # Intensidade das pequenas variações sintéticas.
        self.noise = {
            VitalParameter.HEART_RATE: 1.2,
            VitalParameter.RESPIRATORY_RATE: 0.5,
            VitalParameter.SPO2: 0.2,
            VitalParameter.TEMPERATURE: 0.03,
            VitalParameter.MEAN_ARTERIAL_PRESSURE: 0.8,
        }

        self.units = {
            VitalParameter.HEART_RATE: "bpm",
            VitalParameter.RESPIRATORY_RATE: "rpm",
            VitalParameter.SPO2: "%",
            VitalParameter.TEMPERATURE: "°C",
            VitalParameter.MEAN_ARTERIAL_PRESSURE: "mmHg",
        }

        def _next_value(self,parameter: VitalParameter) -> float:
            current = self.current_values[parameter]
            baseline = self.baseline[parameter]
            noise = self.noise[parameter]

            random_variation = self.random.gauss(0, noise)

            # Faz o valor tender suavemente de volta ao baseline.
            mean_reversion = (baseline - current) * 0.10

            new_value = (
                current
                + random_variation
                + mean_reversion
            )

            # Limite físico simples para SpO2.
            if parameter == VitalParameter.SPO2:
                new_value = max(0.0, min(100.0, new_value))

            self.current_values[parameter] = new_value

            return round(new_value, 2)

        def generate_snapshot(self,timestamp: datetime | None = None) -> list[Measurement]:

            if timestamp is None:
                timestamp = datetime.now()

            measurements = []

            for parameter in self.baseline:
                value = self._next_value(parameter)

                measurement = Measurement(
                    patient_id=self.patient_id,
                    session_id=self.session_id,
                    timestamp=timestamp,
                    parameter=parameter,
                    value=value,
                    unit=self.units[parameter],
                    source=DataSource.SIMULATOR,
                    signal_quality=round(
                        self.random.uniform(0.95, 1.0),
                        2
                    ),
                )

                measurements.append(measurement)

            return measurements

        def generate_series(
        self,
        duration_minutes: int,
        interval_seconds: int = 5,
        start_time: datetime | None = None
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
                start_time = datetime.now()

            measurements = []

            total_seconds = duration_minutes * 60

            for elapsed_seconds in range(
                0,
                total_seconds,
                interval_seconds
            ):
                timestamp = (
                    start_time
                    + timedelta(seconds=elapsed_seconds)
                )

                snapshot = self.generate_snapshot(timestamp)

                measurements.extend(snapshot)

            return measurements
from zoneinfo import ZoneInfo
from PySide6.QtCore import QObject, QTimer, Signal

from ..domain.measurement import Measurement

HORARIO_BRASIL = ZoneInfo("America/Sao_Paulo")

class SinalVitalSimulacao(QObject):
    measurement_generated = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_time = datetime.now(HORARIO_BRASIL)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.generate_measurement)

        self.passo = 0
        self.disturbio = 0.0

        # Valores base/iniciais dos parâmetros
        self.fluxo_o2_ar = 2.0         # L/min
        self.iso_sevo = 1.5            # %
        self.etco2 = 38.0              # mmHg
        self.spo2 = 98.0               # %
        self.temperatura = 37.5        # °C
        self.freq_respiratoria = 15.0  # rpm
        self.freq_cardiaca = 80.0      # bpm
        self.pressao_arterial = 85.0   # mmHg

    def start(self):
        self.generate_measurement()
        self.timer.start(2000)  # Atualiza a cada 2 segundos para simular tempo real

    def stop(self):
        self.timer.stop()

    def limitar(self, valor, minimo, maximo):
        return max(minimo, min(maximo, valor))

    def generate_measurement(self):
        self.passo += 1

        if random.random() < 0.12:
            self.disturbio = random.choice([-1, 1]) * random.uniform(5, 12)

        self.disturbio *= 0.75

        # Variação contínua dos 8 parâmetros
        self.fluxo_o2_ar = self.limitar(2.0 + random.gauss(0, 0.1), 0.5, 10.0)
        self.iso_sevo = self.limitar(1.5 + 0.2 * math.sin(self.passo / 5.0) + random.gauss(0, 0.05), 0.0, 5.0)
        self.etco2 = self.limitar(38.0 + 3.0 * math.sin(self.passo / 3.0) + self.disturbio * 0.3 + random.gauss(0, 0.8), 20.0, 60.0)
        self.spo2 = self.limitar(98.0 - abs(self.disturbio) * 0.1 + random.gauss(0, 0.3), 80.0, 100.0)
        self.temperatura = self.limitar(37.5 + 0.1 * math.sin(self.passo / 10.0) + random.gauss(0, 0.02), 35.0, 41.0)
        self.freq_respiratoria = self.limitar(15.0 + 2.0 * math.sin(self.passo / 4.0) + random.gauss(0, 0.5), 6.0, 40.0)
        self.freq_cardiaca = self.limitar(80.0 + 12.0 * math.sin(self.passo / 3.0) + self.disturbio + random.gauss(0, 2.0), 40.0, 180.0)
        self.pressao_arterial = self.limitar(85.0 + 10.0 * math.sin(self.passo / 4.0) + self.disturbio * 0.5 + random.gauss(0, 2.0), 40.0, 140.0)

        measurement = Measurement(
            tempomedicao=self.current_time,
            fluxo_o2_ar=round(self.fluxo_o2_ar, 1),
            iso_sevo=round(self.iso_sevo, 2),
            etco2=round(self.etco2, 1),
            spo2=round(self.spo2, 1),
            temperatura=round(self.temperatura, 1),
            freq_respiratoria=round(self.freq_respiratoria, 1),
            freq_cardiaca=round(self.freq_cardiaca, 1),
            pressao_arterial=round(self.pressao_arterial, 1)
        )

        self.measurement_generated.emit(measurement)
        self.current_time += timedelta(seconds=2)