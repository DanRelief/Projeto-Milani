M.I.S.A. (Monitor Inteligente de Saúde Animal)



\- Desenvolvimento em Aplicação (executável localmente)

* Banco de dados: MySQL
* Backend: Python
* IA: Gemini Plus
* Front: PySide, Gooey
* Levantamento de pesquisa de transmissão de dados 





Regras de negócio:

1. Interface de Login (RA + Senha em caso de Aluno, email + Senha em caso de Docente). O aluno receberá permissão de User, o Docente receberá permissão de Admin. Só o admin pode cadastrar animais e subir os dados no monitoramento. O aluno fica encarregado da visualização apenas e download de arquivos. Ao fechar a aplica
2. Dados coletados pela máquina e enviado (wifi ou bluetooth) para a máquina com o script local que irá executar a aplicação. Para início de coleta, será feito uma planilha na mão que irá alimentar os dados. A IA irá consumir e plotar em tempos real os dados analisados, salvando também em um banco de dados.
3. Na segunda etapa, será levantado uma ferramenta adicional de anotação que pode ser aplicado pelo aluno, para deixar gravado horário de ministração de medicamento ou análise de algum sinal não convencional nos batimentos dos animais.



Primeiro Passos:

* Levantar material de estudo e viabilidade
* Fazer plots iniciais, decidir gráficos para plots e testar consumindo de um csv
* Gravar os dados em um banco após os plots para testar permanência.

