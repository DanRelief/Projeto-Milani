import math
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from PySide6.QtCore import QObject, QTimer, Signal

from ...domain.measurement import Measurement

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

        self.ultimo_oxigenio = 98.0
        self.ultima_pressao_arterial = 85.0
        self.ultima_temperatura = 37.5

    def start(self):
        self.generate_measurement()
        self.timer.start(2000)

    def stop(self):
        self.timer.stop()

    def limitar(self, valor, minimo, maximo):
        return max(minimo, min(maximo, valor))

    def generate_measurement(self):
        self.passo += 1

        if random.random() < 0.12:
            self.disturbio = random.choice([-1, 1]) * random.uniform(5, 12)

        self.disturbio *= 0.75

        self.ultimo_oxigenio = self.limitar(
            98.0 - abs(self.disturbio) * 0.1 + random.gauss(0, 0.3), 80.0, 100.0
        )
        self.ultima_pressao_arterial = self.limitar(
            85.0 + 10.0 * math.sin(self.passo / 4.0) + self.disturbio * 0.5 + random.gauss(0, 2.0),
            40.0,
            140.0,
        )
        self.ultima_temperatura = self.limitar(
            37.5 + 0.1 * math.sin(self.passo / 10.0) + random.gauss(0, 0.02),
            35.0,
            41.0,
        )

        measurement = Measurement(
            tempomedicao=self.current_time,
            oxigenio=round(self.ultimo_oxigenio, 1),
            pressao_arterial=round(self.ultima_pressao_arterial, 1),
            temperatura=round(self.ultima_temperatura, 1),
        )

        self.measurement_generated.emit(measurement)
        self.current_time += timedelta(seconds=2)