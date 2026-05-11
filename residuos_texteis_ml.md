# Extração de Dados sobre Resíduos Têxteis para Machine Learning

## Objetivo

Este documento reúne os principais dados, variáveis e padrões extraídos dos PDFs enviados, com foco na construção de datasets para modelos de Machine Learning capazes de prever a quantidade de resíduos têxteis gerados por empresas do setor.

---

# 1. Volume de Produção

## Variáveis relevantes
- Metros de tecido cortados
- Quantidade produzida mensalmente
- Quantidade de peças produzidas
- Escala produtiva
- Eficiência produtiva

## Evidências
A geração de resíduos é diretamente proporcional ao consumo de matéria-prima.

A etapa de fiação apresenta perdas médias de 5%, enquanto a etapa de tecelagem apresenta perdas médias de 15%.

---

# 2. Tipo de Tecido / Fibra

## Tipos encontrados

### Naturais
- Algodão
- Linho
- Seda

### Sintéticos
- Poliéster
- Poliamida
- Elastano
- Nylon

### Mistos
- Algodão + poliéster + elastano
- Algodão + elastano

## Distribuição encontrada
- Poliéster → 25%
- Algodão → 16%
- Poliamida + elastano → 13%
- Seda → 9%
- Linho/sarja → 6%

---

# 3. Percentual Médio de Resíduo por Tecido

## Algodão 79% + Poliéster 19% + Elastano 2%
- Produção anual: 56.946,41 metros
- Resíduo anual: 8.088,37 metros
- Média de perda: 14,20%

## Algodão 98% + Elastano 2%
- Produção anual: 20.214,89 metros
- Resíduo anual: 2.602,23 metros
- Média de perda: 12,87%

## Percentuais gerais da empresa
- Tecido A → 47% do resíduo total
- Tecido B → 15%
- Tecido C → 38%

---

# 4. Sazonalidade (Mês / Período)

## Exemplo de variação mensal

| Mês | Produção | Resíduo | % |
|---|---|---|---|
| Fevereiro | 12.883m | 1.935m | 15,02% |
| Junho | 2.680m | 333m | 12,46% |
| Dezembro | 1.597m | 287m | 18,03% |

---

# 5. Etapas do Processo Produtivo

## Etapas identificadas
- Fiação
- Tecelagem
- Beneficiamento
- Tingimento
- Estamparia
- Lavanderia
- Corte
- Costura
- Acabamento

---

# 6. Tipo de Processo Industrial

## Variáveis relevantes
- Processo manual ou automatizado
- Tear convencional ou moderno
- Open-End ou convencional
- Tingimento
- Lavagem industrial
- Estonagem
- Clareamento

## Observações
- Teares modernos aumentam eficiência produtiva.
- Lavanderias geram grande quantidade de resíduos sólidos e efluentes.

---

# 7. Eficiência dos Equipamentos

Os resíduos variam conforme:
- Tipo do equipamento
- Tamanho
- Eficiência operacional
- Existência de controle ambiental

---

# 8. Tipos de Resíduos

## Resíduos produtivos
- Retalhos
- Fibras
- Fitas
- Pavios
- Fios rompidos
- Sobras de corte

## Resíduos químicos
- Lodo de ETE
- Produtos químicos
- Corantes
- Solventes

## Resíduos atmosféricos
- Cinzas
- Fuligem
- Material particulado

---

# 9. Contaminação do Resíduo

## Classe II A
- Não perigoso
- Reciclável

## Classe I
- Perigoso
- Contaminado com óleo/químicos

---

# 10. Reciclagem e Reaproveitamento

## Dados encontrados
- 95% dos resíduos poderiam ser reciclados
- Menos de 12% são coletados
- 85% vão para aterros/incineração

---

# 11. Tempo de Degradação dos Tecidos

| Material | Tempo |
|---|---|
| Algodão | 10–20 anos |
| Sintéticos | 100–300 anos |

---

# 12. Impactos Ambientais

## Variáveis ambientais úteis
- Consumo de água
- Consumo energético
- Emissão de CO₂
- Poluição hídrica
- Poluição atmosférica

---

# 13. Porte da Empresa

## Classificações
- Micro
- Pequena
- Média
- Grande

## Observação
86% das empresas possuem até 49 funcionários.

---

# 14. Tipo de Empresa

## Categorias identificadas
- Fiação
- Tecelagem
- Confecção
- Lavanderia
- Beneficiamento
- Recuperação de resíduos

---

# 15. Quantidade Global de Resíduos

## Dados do Brasil e Mundo
- Brasil: 4 milhões de toneladas/ano
- Mundo: 150 milhões de toneladas/ano
- Projeção para 2050: 895 milhões de toneladas

---

# Features Ideais para Dataset de ML

## Inputs (X)

```text
mes
ano
tipo_tecido
percentual_algodao
percentual_poliester
percentual_elastano
tipo_processo
tipo_empresa
porte_empresa
metros_cortados
quantidade_pecas
tipo_maquina
nivel_automacao
temperatura_processo
uso_quimicos
tipo_tingimento
tipo_lavagem
eficiencia_maquina
horas_producao
consumo_agua
consumo_energia
```

---

# Outputs Possíveis (Y)

```text
quantidade_residuo_metros
percentual_residuo
peso_residuo_kg
classe_residuo
potencial_reciclagem
impacto_ambiental_estimado
```

---

# Modelos de Machine Learning Recomendados

## Regressão
Para prever:
- Quantidade de resíduos
- Percentual de perda

## Séries Temporais
Para prever:
- Sazonalidade
- Meses críticos

## Clusterização
Para identificar:
- Padrões produtivos
- Empresas semelhantes

## Classificação
Para prever:
- Resíduo perigoso ou não
- Reciclável ou não

---

# Dados Mais Valiosos Encontrados

1. Quantidade mensal produzida
2. Quantidade mensal de resíduos
3. Tipo de tecido
4. Composição percentual das fibras
5. Percentual médio de perda
6. Etapa produtiva
7. Tipo de processo
8. Porte da empresa
9. Eficiência operacional
10. Sazonalidade mensal

Esses dados já permitem construir um dataset tabular relativamente forte para modelos supervisionados voltados à previsão de resíduos têxteis.
