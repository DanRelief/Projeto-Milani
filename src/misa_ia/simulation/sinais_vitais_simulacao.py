import math
import random
from datetime import datetime, timedelta
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