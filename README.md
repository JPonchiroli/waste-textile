# 📊 Waste Textile: Previsão de Produção e Resíduo Têxtil

Sistema inteligente para **previsão de produção e resíduo em indústrias têxteis**, com base em dados históricos de eficiência, horas operacionais e produção.

O projeto processa um arquivo Excel ou CSV com dados mensais e gera um novo arquivo com **previsões realistas para os próximos 12 meses**, respeitando a lógica de negócio da fábrica.

---

## 🚀 Objetivo

Ajudar indústrias têxteis a:
- Planejar produção futura
- Estimar geração de resíduos
- Otimizar eficiência operacional
- Apoiar decisões de sustentabilidade

---

## 📥 Como Usar

1. Prepare um arquivo Excel ou CSV com dados mensais da produção.
2. Envie o arquivo no sistema web.
3. Aguarde o processamento.
4. Baixe o novo arquivo com as previsões já calculadas.

O sistema retorna um novo arquivo com:
- Dados históricos + previsões
- Colunas adicionais: `Producao_Minima_Esperada` e `Producao_Maxima_Esperada`
- Resíduo calculado como **10% da produção total**

---

## 🧱 Modelo Base Mínimo Necessário

Para o programa funcionar, seu arquivo de entrada **deve conter as seguintes colunas**:

| Coluna | Descrição | Exemplo |
|-------|----------|--------|
| `Mes` | Mês no formato `AAAA-MM` | `2023-01` |
| `Producao_Total_kg` | Produção total do mês em kg | `72720` |
| `Eficiencia_kg_h` | Eficiência em kg por hora | `101` |
| `Horas_Operacionais` | Total de horas operacionais no mês | `720` |

> ✅ Opcional: `Residuo_kg` — será recalculado como 10% da produção, mas pode estar presente.

### ✅ Exemplo de Dados Válidos

| Mes | Producao_Total_kg | Eficiencia_kg_h | Horas_Operacionais | Residuo_kg |
|-----|-------------------|------------------|--------------------|------------|
| 2023-01 | 43554 | 84 | 518.5 | 4355.4 |
| 2023-02 | 57600 | 80 | 720 | 5760 |
| ... | ... | ... | ... | ... |

> 📌 É recomendado ter **pelo menos 6 meses de dados**, mas 12 meses ou mais trazem melhores previsões.

---

## 🔍 Como o Sistema Faz as Previsões?

O sistema não usa médias fixas. Ele entende a **relação entre as variáveis** e faz previsões com base em um modelo estatístico confiável.

### 📐 Lógica de Negócio

Sabemos que:
Produção Total (kg) = Eficiência (kg/h) × Horas Operacionais
Resíduo (kg) = 10% da Produção Total

Ou seja: **a produção depende da eficiência e das horas**, não o contrário.

Por isso, o sistema:
1. Prever a **eficiência** e as **horas operacionais** separadamente
2. Calcular a **produção total** com base nessas previsões
3. Calcular o **resíduo** como 10% da produção prevista

---

### 📈 Modelo Estatístico: Holt (Suavização Exponencial)

O sistema usa o **modelo Holt** para prever tendências ao longo do tempo.

#### O que ele faz?
- Analisa os dados históricos
- Identifica se a eficiência e as horas estão aumentando ou diminuindo
- Projetada essa tendência para os próximos 12 meses

#### Por que Holt?
- É ideal para dados com **tendência clara**
- Mais inteligente que média simples
- Leva em conta mudanças recentes

> Exemplo: se a eficiência vem crescendo 2 kg/h por mês, o modelo projeta esse crescimento.

---

### 📊 Saída do Sistema

O arquivo gerado tem duas abas:

#### 1. `Dados_Completos`
- Todos os dados históricos
- Seguidos pelas previsões para 2024
- Colunas adicionais: `Producao_Minima_Esperada` e `Producao_Maxima_Esperada`

#### 2. `Arquivo Modificado`
- Apenas os 12 meses futuros
- Útil para relatórios e planejamento

---

## ⚙️ Tecnologias Utilizadas

- **Python** + **Flask**: Backend e interface web
- **Pandas**: Leitura e processamento de dados
- **Statsmodels**: Modelo Holt para previsão
- **Tailwind CSS**: Interface limpa e responsiva
- **OpenPyXL**: Geração de arquivos Excel


---

## ⚙️ Como rodar o projeto

```bash
# 1. Criar ambiente virtual
python -m venv venv

# 2. Ativar o ambiente virtual
# No Linux/macOS:
source venv/bin/activate

# No Windows (cmd ou PowerShell):
venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt



### Subir container
``
Prometheus: docker run -d --name prometheus -p 9090:9090 -v /c/Users/joaop/projetos/waste-textile/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus
``