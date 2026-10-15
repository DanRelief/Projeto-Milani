from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class VitalParameter(str, Enum):
    HEART_RATE = "heart_rate"
    RESPIRATORY_RATE = "respiratory_rate"
    SPO2 = "spo2"
    TEMPERATURE = "temperature"
    MEAN_ARTERIAL_PRESSURE = "mean_arterial_pressure"


class DataSource(str, Enum):
    SIMULATOR = "simulator"
    CSV = "csv"
    MONITOR = "monitor"
    WIFI = "wifi"
    BLUETOOTH = "bluetooth"


@dataclass(init=False)
class Measurement:
    """Representa uma medição individual ou um snapshot dos sinais vitais.

    O simulador utilizado pela tela inicial entrega um snapshot com vários
    sinais ao mesmo tempo. O simulador de domínio mais novo entrega uma
    medição individual, identificada por ``parameter`` e ``value``. Os dois
    formatos são mantidos para permitir a integração gradual entre eles.
    """

    # Formato novo: uma medição por parâmetro.
    patient_id: str | None
    session_id: str | None
    timestamp: datetime | None
    parameter: VitalParameter | None
    value: float | None
    unit: str | None
    source: DataSource | None
    signal_quality: float | None
    is_valid: bool

    # Formato do snapshot usado pela tela de monitoramento.
    tempomedicao: datetime | None
    fluxo_o2_ar: float | None
    iso_sevo: float | None
    etco2: float | None
    spo2: float | None
    temperatura: float | None
    freq_respiratoria: float | None
    freq_cardiaca: float | None
    pressao_arterial: float | None

    def __init__(
        self,
        patient_id: str | None = None,
        session_id: str | None = None,
        timestamp: datetime | None = None,
        parameter: VitalParameter | None = None,
        value: float | None = None,
        unit: str | None = None,
        source: DataSource | None = None,
        signal_quality: float | None = None,
        is_valid: bool = True,
        *,
        tempomedicao: datetime | None = None,
        fluxo_o2_ar: float | None = None,
        iso_sevo: float | None = None,
        etco2: float | None = None,
        spo2: float | None = None,
        temperatura: float | None = None,
        freq_respiratoria: float | None = None,
        freq_cardiaca: float | None = None,
        pressao_arterial: float | None = None,
    ) -> None:
        snapshot_values = (
            tempomedicao,
            fluxo_o2_ar,
            iso_sevo,
            etco2,
            spo2,
            temperatura,
            freq_respiratoria,
            freq_cardiaca,
            pressao_arterial,
        )
        is_snapshot = any(value is not None for value in snapshot_values)

        if is_snapshot:
            if tempomedicao is None:
                raise ValueError("tempomedicao não pode ser vazia.")

            snapshot_fields = {
                "fluxo_o2_ar": fluxo_o2_ar,
                "iso_sevo": iso_sevo,
                "etco2": etco2,
                "spo2": spo2,
                "temperatura": temperatura,
                "freq_respiratoria": freq_respiratoria,
                "freq_cardiaca": freq_cardiaca,
                "pressao_arterial": pressao_arterial,
            }
            missing_fields = [
                name for name, field_value in snapshot_fields.items()
                if field_value is None
            ]
            if missing_fields:
                raise ValueError(
                    "Snapshot incompleto; campos ausentes: "
                    + ", ".join(missing_fields)
                )

            self.patient_id = patient_id
            self.session_id = session_id
            self.timestamp = timestamp or tempomedicao
            self.parameter = parameter
            self.value = value
            self.unit = unit
            self.source = source
            self.signal_quality = signal_quality
            self.is_valid = is_valid
            self.tempomedicao = tempomedicao
            self.fluxo_o2_ar = fluxo_o2_ar
            self.iso_sevo = iso_sevo
            self.etco2 = etco2
            self.spo2 = spo2
            self.temperatura = temperatura
            self.freq_respiratoria = freq_respiratoria
            self.freq_cardiaca = freq_cardiaca
            self.pressao_arterial = pressao_arterial
            self._validate_signal_quality()
            return

        self.patient_id = patient_id
        self.session_id = session_id
        self.timestamp = timestamp
        self.parameter = parameter
        self.value = value
        self.unit = unit
        self.source = source
        self.signal_quality = signal_quality
        self.is_valid = is_valid
        self.tempomedicao = timestamp
        self.fluxo_o2_ar = None
        self.iso_sevo = None
        self.etco2 = None
        self.spo2 = None
        self.temperatura = None
        self.freq_respiratoria = None
        self.freq_cardiaca = None
        self.pressao_arterial = None
        self.__post_init__()

    def __post_init__(self) -> None:
        if not isinstance(self.patient_id, str) or not self.patient_id.strip():
            raise ValueError("patient_id não pode ser vazio.")

        if not isinstance(self.session_id, str) or not self.session_id.strip():
            raise ValueError("session_id não pode ser vazio.")

        if self.timestamp is None:
            raise ValueError("timestamp não pode ser vazio.")

        if self.parameter is None:
            raise ValueError("parameter não pode ser vazio.")

        if self.value is None or self.unit is None or self.source is None:
            raise ValueError("value, unit e source são obrigatórios.")

        self._validate_signal_quality()

    def _validate_signal_quality(self) -> None:
        if self.signal_quality is not None:
            if not 0.0 <= self.signal_quality <= 1.0:
                raise ValueError(
                    "signal_quality deve estar entre 0.0 e 1.0."
                )
