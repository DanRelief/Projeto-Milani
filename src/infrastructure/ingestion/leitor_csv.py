import csv
from datetime import datetime
from pathlib import Path
from src.domain.measurement import FonteDados,Medicao,ParametroVital

class LeitorCSV:
    COLUNAS_OBRIGATORIAS = {
        "data_hora",
        "spo2",
        "temperatura",
        "pressao_arterial_media",
    }

    def ler(self,caminho_arquivo: str | Path,id_paciente: str,id_sessao: str,) -> list[Medicao]:
        caminho = Path(caminho_arquivo)

        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo CSV não encontrado: {caminho}")

        with caminho.open("r",encoding="utf-8-sig",newline="",) as arquivo:

            delimitador = (self.detectar_delimitador(arquivo))

            arquivo.seek(0)

            leitor = csv.DictReader(arquivo,delimiter=delimitador,)
            self.validar_colunas(leitor.fieldnames)
            medicoes = []

            for numero_linha, linha in enumerate(leitor,start=2,):
                medicoes_linha = (self.converter_linha(
                        linha=linha,
                        numero_linha=numero_linha,
                        id_paciente=id_paciente,
                        id_sessao=id_sessao,
                    )
                )

                medicoes.extend(medicoes_linha)

        return medicoes

    def detectar_delimitador(self,arquivo,) -> str:
        amostra = arquivo.read(2048)
        try:
            dialecto = csv.Sniffer().sniff(amostra,delimiters=";,",)

            return dialecto.delimiter

        except csv.Error:
            return ";"

    def validar_colunas(self,colunas,) -> None:

        if colunas is None:
            raise ValueError("O CSV não possui cabeçalho.")

        colunas_recebidas = {coluna.strip() for coluna in colunas}

        faltantes = (self.COLUNAS_OBRIGATORIAS - colunas_recebidas)

        if faltantes:
            nomes = ", ".join(sorted(faltantes))

            raise ValueError(f"Colunas obrigatórias ausentes: {nomes}")

    def converter_data_hora(self,valor: str,numero_linha: int,) -> datetime:

        formatos = ["%Y-%m-%d %H:%M:%S","%d/%m/%Y %H:%M:%S",]

        for formato in formatos:

            try:
                return datetime.strptime(valor.strip(),formato,)

            except ValueError:
                continue

        raise ValueError(f"Linha {numero_linha}: "f"data/hora inválida: {valor}")

    def converter_linha(self,linha: dict,numero_linha: int,id_paciente: str,id_sessao: str,) -> list[Medicao]:

        data_hora = self.converter_data_hora(
            linha["data_hora"],
            numero_linha,
        )

        spo2 = self.converter_float_opcional(
            linha["spo2"],
            "spo2",
            numero_linha,
        )

        temperatura = self.converter_float_opcional(
            linha["temperatura"],
            "temperatura",
            numero_linha,
        )

        pressao = self.converter_float_opcional(
            linha["pressao_arterial_media"],
            "pressao_arterial_media",
            numero_linha,
        )

        medicoes = []
        if spo2 is not None:

            medicoes.append(
                Medicao(
                    id_paciente=id_paciente,
                    id_sessao=id_sessao,
                    data_hora=data_hora,

                    parametro=ParametroVital.SPO2,

                    valor=spo2,
                    unidade="%",

                    fonte=FonteDados.CSV,

                    qualidade_sinal=None,
                    valida=True,
                )
            )
        if temperatura is not None:

            medicoes.append(
                Medicao(
                    id_paciente=id_paciente,
                    id_sessao=id_sessao,
                    data_hora=data_hora,

                    parametro=ParametroVital.TEMPERATURA,

                    valor=temperatura,
                    unidade="°C",

                    fonte=FonteDados.CSV,

                    qualidade_sinal=None,
                    valida=True,
                )
            )
        if pressao is not None:

            medicoes.append(
                Medicao(
                    id_paciente=id_paciente,
                    id_sessao=id_sessao,
                    data_hora=data_hora,

                    parametro=(
                        ParametroVital
                        .PRESSAO_ARTERIAL_MEDIA
                    ),

                    valor=pressao,
                    unidade="mmHg",

                    fonte=FonteDados.CSV,

                    qualidade_sinal=None,
                    valida=True,
                )
            )

        return medicoes

    def converter_float_opcional(self,valor: str | None,nome_campo: str,numero_linha: int,) -> float | None:

        if valor is None:
            return None

        valor = valor.strip()

        if not valor:
            return None

        valor = valor.replace(
            ",",
            ".",
        )

        try:
            return float(valor)

        except ValueError as erro:

            raise ValueError(
                f"Linha {numero_linha}: "
                f"valor inválido para "
                f"{nome_campo}: {valor}"
            ) from erro