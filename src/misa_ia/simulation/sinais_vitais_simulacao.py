import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import math

HORARIO_BRASIL = ZoneInfo("America/Sao_Paulo")

from PySide6.QtCore import QObject, QTimer, Signal

from ..domain.measurement import Measurement


class SinalVitalSimulacao(QObject):
    measurement_generated = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_time = datetime.now(HORARIO_BRASIL)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.generate_measurement)

        self.passo = 0
        self.disturbio = 0.0

        self.ultimo_oxigenio = 96.0
        self.ultimo_batimento_cardiaco = 88.0
        self.ultima_pressao_arterial = 70.0

    def start(self):
        self.generate_measurement()

        self.timer.start(5 * 1000) #tempo, a cada 5 minutos, em milissegundos (5 min seria 5 * 60 * 1000, mas para teste, usei 5 * 1000 por ser mais rápido)

    def stop(self):
        self.timer.stop()

    def generate_measurement(self):
        measurement = Measurement(
        tempomedicao=self.current_time,
        oxigenio=round(self.ultimo_oxigenio, 1),
        batimento_cardiaco=round(self.ultimo_batimento_cardiaco, 1),
        pressao_arterial=round(self.ultima_pressao_arterial, 1),)

        self.measurement_generated.emit(measurement)

        # Avança somente para a próxima medição simulada
        self.current_time += timedelta(minutes=5)
    def limitar(self, valor, minimo, maximo):
        return max(minimo, min(maximo, valor))

    def generate_measurement(self):
        self.passo += 1

        # Eventualmente cria uma alteração temporária
        if random.random() < 0.12:
            self.disturbio = random.choice([-1, 1]) * random.uniform(8, 18)

        # Faz o distúrbio desaparecer gradualmente
        self.disturbio *= 0.75

        self.ultimo_oxigenio = self.limitar(
            96
            + 2.0 * math.sin(self.passo / 2.0)
            - abs(self.disturbio) * 0.08
            + random.gauss(0, 0.7),
            80,
            100,
        )

        self.ultimo_batimento_cardiaco = self.limitar(
            88
            + 18 * math.sin(self.passo / 3.0)
            + self.disturbio
            + random.gauss(0, 4),
            40,
            160,
        )

        self.ultima_pressao_arterial = self.limitar(
            70
            + 14 * math.sin(self.passo / 4.0)
            + self.disturbio * 0.4
            + random.gauss(0, 3),
            40,
            120,
        )

        measurement = Measurement(
            tempomedicao=self.current_time,
            oxigenio=round(self.ultimo_oxigenio, 1),
            batimento_cardiaco=round(self.ultimo_batimento_cardiaco, 1),
            pressao_arterial=round(self.ultima_pressao_arterial, 1),
        )

        self.measurement_generated.emit(measurement)

        self.current_time += timedelta(minutes=5)