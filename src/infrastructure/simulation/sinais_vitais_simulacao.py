import math
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from PySide6.QtCore import QObject, QTimer, Signal

from src.domain.measurement import (
    FonteDados,
    Medicao,
    ParametroVital,
)


HORARIO_BRASIL = ZoneInfo(
    "America/Sao_Paulo"
)


class SimuladorSinaisVitais:

    def __init__(self,id_paciente: str,id_sessao: str,seed: int | None = None,baseline_spo2: float = 98.0,amplitude_spo2: float = 0.25,desvio_ruido_spo2: float = 0.15,tendencia_spo2_por_minuto: float = 0.0,):

        self.id_paciente = id_paciente
        self.id_sessao = id_sessao

        self.random = random.Random(seed)

        self.passo = 0

        self.baseline = {
            ParametroVital.SPO2: baseline_spo2,
            ParametroVital.TEMPERATURA: 37.5,
            ParametroVital.PRESSAO_ARTERIAL_MEDIA: 85.0,
        }

        self.baseline_inicial = dict(self.baseline)

        self.amplitude_spo2 = amplitude_spo2
        self.desvio_ruido_spo2 = desvio_ruido_spo2
        self.tendencia_spo2_por_minuto = tendencia_spo2_por_minuto
        self.data_hora_inicio = None
        self.units = {
            ParametroVital.SPO2: "%",
            ParametroVital.TEMPERATURA: "°C",
            ParametroVital.PRESSAO_ARTERIAL_MEDIA: "mmHg",
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

    def _generate_spo2(self,data_hora: datetime,) -> float:

        baseline = self.baseline[ParametroVital.SPO2]

        if self.data_hora_inicio is None:
            minutos_decorridos = 0.0
        else:
            minutos_decorridos = ((data_hora - self.data_hora_inicio).total_seconds()/ 60.0)

        tendencia = (self.tendencia_spo2_por_minuto * minutos_decorridos)

        valor = (baseline + self.amplitude_spo2 * math.sin(self.passo / 8.0)+ self.random.gauss(0,self.desvio_ruido_spo2,) + tendencia)

        valor = self._limit( valor, 0.0, 100.0,)

        return round(valor,2,)

    def _generate_temperature(self) -> float:

        baseline = self.baseline[
            ParametroVital.TEMPERATURA
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
            ParametroVital.PRESSAO_ARTERIAL_MEDIA
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

    def generate_snapshot(self,data_hora: datetime | None = None,) -> list[Medicao]:

        if data_hora is None:
            data_hora = datetime.now(
                HORARIO_BRASIL
            )

        if self.data_hora_inicio is None:
            self.data_hora_inicio = (
                data_hora
            )

        self.passo += 1

        valors = {
            ParametroVital.SPO2:
                self._generate_spo2(data_hora),

            ParametroVital.TEMPERATURA:
                self._generate_temperature(),

            ParametroVital.PRESSAO_ARTERIAL_MEDIA:
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

    def reduzir_spo2_teste(
        self,
        quantidade: float = 3.0,
    ) -> None:
    
            baseline_atual = self.baseline[
                ParametroVital.SPO2
            ]
    
            self.baseline[
                ParametroVital.SPO2
            ] = self._limit(
                baseline_atual - quantidade,
                0.0,
                100.0,
            )
    
    
    def restaurar_spo2_teste(
        self,
    ) -> None:

        self.baseline[
            ParametroVital.SPO2
        ] = 98.0


    def simular_queda_spo2(
        self,
        quantidade: float = 3.0,
    ) -> None:

        parametro = ParametroVital.SPO2

        self.baseline[parametro] = (
            self._limit(
                self.baseline[parametro]
                - quantidade,
                0.0,
                100.0,
            )
        )


    def simular_queda_pam(
        self,
        quantidade: float = 15.0,
    ) -> None:

        parametro = (
            ParametroVital
            .PRESSAO_ARTERIAL_MEDIA
        )

        self.baseline[parametro] = (
            self._limit(
                self.baseline[parametro]
                - quantidade,
                20.0,
                200.0,
            )
        )


    def simular_aumento_temperatura(
        self,
        quantidade: float = 0.8,
    ) -> None:

        parametro = (
            ParametroVital.TEMPERATURA
        )

        self.baseline[parametro] += (
            quantidade
        )


    def restaurar_sinais_teste(
        self,
    ) -> None:

        self.baseline = dict(
            self.baseline_inicial
        )
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

    
    def simular_queda_spo2(
    self,
    quantidade: float = 3.0,
) -> None:

        self.simulator.reduzir_spo2_teste(
            quantidade
        )


    def restaurar_spo2(
        self,
    ) -> None:

        self.simulator.restaurar_spo2_teste()

    def simular_queda_spo2(
        self,
        quantidade: float = 3.0,
    ) -> None:

        self.simulator.simular_queda_spo2(
            quantidade
        )


    def simular_queda_pam(
        self,
        quantidade: float = 15.0,
    ) -> None:

        self.simulator.simular_queda_pam(
            quantidade
        )


    def simular_aumento_temperatura(
        self,
        quantidade: float = 0.8,
    ) -> None:

        self.simulator.simular_aumento_temperatura(
            quantidade
        )


    def restaurar_sinais_teste(
        self,
    ) -> None:

        self.simulator.restaurar_sinais_teste()
