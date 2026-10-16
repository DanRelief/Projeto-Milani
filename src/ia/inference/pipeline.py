class InferencePipeline:

    def process(self, Medicao):

        validar_medicao()

        adicionar_ao_buffer()

        if ainda_nao_tem_dados_suficientes:
            return

        criar_janelas()

        calcular_features()

        calcular_baseline()

        executar_regras()

        calcular_anomalia()

        criar_evidencias()

        avaliar_alerta()

        return resultado