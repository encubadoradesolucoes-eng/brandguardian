# Metodologia de Análise Inteligente - M24 Brand Guardian

Este documento descreve o funcionamento técnico e estratégico do motor de análise da **M24 Brand Guardian**, concebido especificamente para o mercado de Propriedade Industrial em Moçambique.

## 1. Motores de Comparação Multi-Vetorial

A nossa IA não realiza apenas uma busca por nomes iguais; ela simula o julgamento de um examinador humano do **IPI** através de três eixos fundamentais:

### A. Análise Fonética e Textual (Similaridade Auditiva)
Utilizamos o algoritmo de *SequenceMatcher* e normalização linguística para detetar marcas que "soam" iguais, mesmo com grafias diferentes.
- **Exemplo:** "M-Pesa" vs "Em-Pesa" ou "Karingana" vs "Caringana".
- **Peso na Decisão:** 40%

### B. Análise Visual e Perceptiva (pHash)
Implementamos a tecnologia de *Perceptual Hashing (pHash)*. Ao contrário de uma comparação pixel a pixel, o pHash gera uma "impressão digital" do logotipo.
- **Capacidade:** Identifica se um logotipo foi rodado, se as cores foram alteradas ou se a estrutura geométrica é idêntica à de uma marca já protegida.
- **Peso na Decisão:** 40%

### C. Contextualização por Classe de Nice (Segmento de Mercado)
A IA analisa a probabilidade de confusão no consumidor. Marcas similares em classes diferentes (ex: Classe 25 - Roupas vs Classe 33 - Bebidas) têm um risco menor.
- **Lógica:** Cruzamos as 45 classes de Nice para identificar sobreposições diretas de atividades.
- **Peso na Decisão:** 20%

## 2. Matriz de Risco e Tomada de Decisão

Após o cruzamento de dados, o sistema gera um **Score de Risco (0-100%)**:

| Score | Nível de Risco | Ação do Sistema |
| :--- | :--- | :--- |
| **0% - 15%** | **Baixo** | **Aprovação Automática:** O sistema considera o caminho livre para registo. |
| **16% - 60%** | **Moderado** | **Aguardando Gestor:** O processo é enviado para a "Lista de Veredito" da M24 para análise humana. |
| **> 60%** | **Alto** | **Alerta Crítico:** O titular e o gestor são notificados de um conflito directo com o direito de terceiros. |

## 3. Vigilância Ativa M24 (Monitoramento 24/7)

Para marcas já existentes, a análise é recorrente. O sistema "varre" a base nacional e os novos pedidos de terceiros bi-semanalmente. Se qualquer novo pedido for detectado como conflituante com a sua marca, um **Alerta de Oposição** é enviado instantaneamente via WhatsApp e Email.

---
*M24 Security Systems - Garantindo a soberania da sua identidade visual.*
