# Sistema de Negociación Autónoma B2B con Agentes de IA

Simulación de una mesa de negociación entre empresas (B2B) donde agentes de inteligencia artificial negocian, acuerdan y legalizan contratos de suministro de forma autónoma, sin intervención humana constante.

---

## ¿Qué es esto?

Este proyecto es una **simulación funcional** de cómo podría automatizarse la negociación de contratos de suministro entre una empresa compradora y una empresa vendedora.

Cuando el inventario de materias primas de una fábrica cae por debajo de un nivel crítico, el sistema lo detecta automáticamente y lanza tres agentes de IA que negocian entre sí hasta llegar a un acuerdo. El resultado es un contrato digital revisado por un agente legal, listo para su firma.

> **Es una simulación.** Los datos de inventario, capacidad productiva y regulaciones están en ficheros JSON locales (`data/`). En un entorno real, estos datos vendrían de un ERP, un sistema de producción (MES) y APIs de regulaciones aduaneras. El sistema está diseñado para que esa sustitución sea sencilla.

---

## El escenario simulado

| | Empresa | Descripción |
|---|---|---|
| **Compradora** | AcmeCorp Manufacturing (Barcelona, España) | Fábrica que consume acero para producir |
| **Vendedora** | GlobalSupplyCo (Düsseldorf, Alemania) | Acería con capacidad de producción mensual |

**Situación inicial:**
- AcmeCorp tiene **150 toneladas** de acero en stock
- El punto de reorden es **250 toneladas**
- Consume **180 toneladas al mes**
- En **8 días** se queda sin stock mínimo operativo

El sistema detecta esta situación y lanza automáticamente una negociación para comprar **540 toneladas** (3 meses de consumo).

---

## Los tres agentes

### 🧑‍💼 Agente Comprador

Representa los intereses de AcmeCorp. Tiene acceso a los datos de inventario y a precios de referencia históricos.

**Objetivo:** Comprar al menor precio posible, idealmente un 3% por debajo del último precio pagado (720 €/MT → objetivo 698,40 €/MT).

**Herramientas disponibles:**
- `check_inventory` — consulta el stock actual de un material
- `predict_shortage` — proyecta cuándo se agotará el inventario
- `get_reference_price` — obtiene el precio de referencia histórico
- `evaluate_seller_offer` — puntúa una oferta del vendedor (0-100)

**Reglas de negociación:**
- Acepta si la puntuación de la oferta es ≥ 72 sobre 100
- Contraoferta si la puntuación está entre 45 y 71
- Rechaza solo si la oferta es claramente abusiva (< 45)

---

### 🏭 Agente Vendedor

Representa los intereses de GlobalSupplyCo. Tiene acceso a los datos de capacidad productiva y costes de fabricación.

**Objetivo:** Maximizar el margen de beneficio manteniendo el mínimo del 20%.

**Herramientas disponibles:**
- `check_production_capacity` — verifica si puede fabricar la cantidad solicitada
- `calculate_min_price` — calcula el precio mínimo con el 20% de margen
- `calculate_offer_price` — calcula el precio de oferta a un margen dado
- `evaluate_buyer_counter` — analiza si la contraoferta del comprador es rentable

**Reglas de negociación:**
- Oferta inicial con el 25% de margen (aplicando descuentos por volumen)
- Acepta contraofertas que mantengan ≥ 20% de margen
- Contraoferta al 22% si la propuesta del comprador no es suficiente

**Descuentos por volumen** (acero):
| Cantidad | Descuento |
|---|---|
| ≥ 100 MT | 2% |
| ≥ 250 MT | 4% |
| ≥ 500 MT | 7% |

---

### ⚖️ Agente Legal

Revisa el contrato acordado antes de su finalización, verificando el cumplimiento de normativas europeas.

**Herramientas disponibles:**
- `validate_incoterm` — verifica que el término de entrega es válido según Incoterms® 2020
- `check_applicable_tariffs` — consulta aranceles aplicables (comercio intracomunitario UE)
- `check_carbon_compliance` — verifica la huella de carbono frente a los límites del EU CBAM
- `validate_payment_terms` — comprueba que los plazos de pago cumplen la Directiva Europea de Morosidad (máx. 60 días B2B)
- `check_contract_clauses` — revisa cláusulas obligatorias (fuerza mayor, arbitraje, ley aplicable)

**Veredictos posibles:**
- `APPROVED` → contrato finalizado ✓
- `CONDITIONALLY_APPROVED` → aprobado con advertencias
- `REJECTED` → problemas bloqueantes que impiden proceder

---

## Cómo funciona: el flujo de negociación

```
┌─────────────────────────────────────────────────┐
│  ALERTA: inventario de hot_rolled_steel crítico  │
│  Stock actual: 150 MT | Mínimo: 200 MT           │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
         ┌──────────────────────────┐
         │      AGENTE VENDEDOR     │
         │  Calcula capacidad y     │
         │  precio: 647,28 €/MT     │
         │  (20% margen + desc. 7%) │
         └──────────────┬───────────┘
                        │ oferta inicial
                        ▼
         ┌──────────────────────────┐
         │      AGENTE COMPRADOR    │
         │  Evalúa oferta:          │
         │  647 vs ref. 720 €/MT    │
         │  Puntuación: 68/100      │
         │  → CONTRAOFERTA 698 €/MT │
         └──────────────┬───────────┘
                        │ contraoferta
                        ▼
         ┌──────────────────────────┐
         │      AGENTE VENDEDOR     │
         │  698 €/MT implica 29%    │
         │  de margen → ACEPTA      │
         └──────────────┬───────────┘
                        │ acuerdo
                        ▼
         ┌──────────────────────────┐
         │      AGENTE LEGAL        │
         │  ✓ Incoterm DAP válido   │
         │  ✓ Arancel DE→ES: 0%     │
         │  ✓ CO₂: 1,85 < 2,5 kg   │
         │  ✓ NET_45 < 60 días      │
         │  → APROBADO              │
         └──────────────┬───────────┘
                        │
                        ▼
      ┌───────────────────────────────────┐
      │  CONTRATO FINALIZADO              │
      │  CTR-20260528-XXXX                │
      │  540 MT acero S355                │
      │  698,40 €/MT · Total 377.136 €    │
      │  Entrega: DAP Barcelona, 14 días  │
      │  Pago: NET_45                     │
      └───────────────────────────────────┘
```

---

## Arquitectura técnica

### Stack

| Capa | Tecnología |
|---|---|
| Orquestación de agentes | [LangGraph](https://github.com/langchain-ai/langgraph) |
| Framework de agentes | [LangChain](https://github.com/langchain-ai/langchain) |
| Modelos de datos | [Pydantic v2](https://docs.pydantic.dev/) |
| Configuración | pydantic-settings + `.env` |
| LLM por defecto | [Ollama](https://ollama.ai) (local, sin coste) |
| Contenerización | Docker + Docker Compose |

### Estructura de ficheros

```
b2b-multiagent-supply-negotiation/
│
├── main.py                      ← punto de entrada
├── config.py                    ← configuración vía variables de entorno
│
├── src/
│   ├── providers/
│   │   └── llm.py               ← factory de LLMs (multi-proveedor)
│   │
│   ├── models/
│   │   ├── inventory.py         ← InventoryItem, BuyerInventory, SellerCapacity
│   │   ├── offer.py             ← Offer, NegotiationMessage
│   │   └── contract.py         ← Contract, ContractLine, ContractTerms
│   │
│   ├── tools/
│   │   ├── buyer_tools.py       ← herramientas del agente comprador
│   │   ├── seller_tools.py      ← herramientas del agente vendedor
│   │   └── legal_tools.py       ← herramientas del agente legal
│   │
│   ├── agents/
│   │   ├── buyer.py             ← nodo comprador del grafo
│   │   ├── seller.py            ← nodo vendedor del grafo
│   │   └── legal.py             ← nodo legal del grafo
│   │
│   ├── orchestrator/
│   │   ├── state.py             ← NegotiationState (estado compartido)
│   │   └── graph.py             ← StateGraph de LangGraph
│   │
│   └── utils.py                 ← parsing de JSON, generación de IDs
│
├── data/                        ← datos simulados (reemplazables por APIs reales)
│   ├── buyer_inventory.json     ← stock actual de AcmeCorp
│   ├── seller_capacity.json     ← capacidad productiva de GlobalSupplyCo
│   └── regulations.json         ← aranceles, límites CO₂, plazos de pago
│
├── scripts/
│   └── entrypoint.sh            ← espera a Ollama, descarga el modelo, arranca
│
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

### El grafo de negociación (LangGraph)

LangGraph gestiona el flujo como una máquina de estados. El estado (`NegotiationState`) contiene toda la información de la negociación y se pasa entre nodos:

```
INICIO
  │
  └─→ [SELLER] genera oferta inicial
        │
        └─→ [BUYER] evalúa oferta
              │
              ├── ACEPTA ──────────────→ [LEGAL] revisa contrato → FIN
              │
              ├── CONTRAOFERTA ────────→ [SELLER] evalúa contraoferta
              │                               │
              │                               ├── ACEPTA → [LEGAL] → FIN
              │                               └── CONTRAOFERTA → [BUYER] (bucle)
              │
              └── RECHAZA / MAX RONDAS ──────────────────────────→ FIN (fallido)
```

---

## Proveedores de LLM soportados

El sistema funciona con cualquiera de estos proveedores. Se configura con una sola variable de entorno:

| Proveedor | Variable | Notas |
|---|---|---|
| **Ollama** *(por defecto)* | `PROVIDER=ollama` | Gratuito, local, privado. Requiere Ollama instalado. |
| **OpenAI** | `PROVIDER=openai` | GPT-4o-mini por defecto. |
| **Anthropic** | `PROVIDER=anthropic` | Claude Haiku por defecto. |
| **Groq** | `PROVIDER=groq` | Inferencia muy rápida. Tiene tier gratuito. |
| **Google Gemini** | `PROVIDER=gemini` | Gemini 2.0 Flash por defecto. Tiene tier gratuito. |

---

## Instalación y ejecución

### Opción A — Docker (recomendado)

Requiere Docker Desktop en ejecución. Ollama debe estar corriendo en el sistema host.

```bash
# 1. Clonar el repositorio
git clone https://github.com/luisforni/b2b-multiagent-supply-negotiation.git
cd b2b-multiagent-supply-negotiation

# 2. Asegurarse de que Ollama está activo y tiene el modelo
ollama pull llama3.2

# 3. Arrancar
docker compose up --build
```

El contenedor espera a que Ollama esté disponible, descarga el modelo si no está y ejecuta la negociación. Al terminar, el contenedor sale con código 0.

> **Sin Ollama local** (entorno limpio, CI, servidor):
> ```bash
> docker compose --profile with-ollama up --build
> ```
> Esto levanta un contenedor de Ollama en el puerto 11435.

### Opción B — Ejecución local

```bash
# 1. Entorno virtual
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows

# 2. Dependencias
pip install -r requirements.txt

# 3. Configuración
cp .env.example .env
# Editar .env con el proveedor y claves deseadas

# 4. Ejecutar
python main.py
```

---

## Configuración

Copiar `.env.example` a `.env` y ajustar los valores:

```env
# Proveedor de LLM
PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Parámetros de negociación
MAX_ROUNDS=10
BUYER_COMPANY=AcmeCorp Manufacturing
SELLER_COMPANY=GlobalSupplyCo
```

Para usar un proveedor en la nube, descomentar la sección correspondiente en `.env.example`.

---

## Salida de ejemplo

```
============================================================
  B2B MULTI-AGENT SUPPLY NEGOTIATION SYSTEM
============================================================
  Provider  : OLLAMA
  Buyer     : AcmeCorp Manufacturing
  Seller    : GlobalSupplyCo
============================================================

[ALERT] Inventory shortage detected:
  Material       : hot_rolled_steel
  Current stock  : 150.0 metric_ton
  Reorder point  : 250.0 metric_ton
  Days remaining : -8.3
  Order quantity : 540.0 metric_ton

[START] Launching autonomous negotiation...
------------------------------------------------------------

  [Round 1] status=negotiating  | latest offer from seller: 647.28 EUR
  [Round 2] status=negotiating  | latest offer from buyer:  698.40 EUR
  [Round 3] status=agreed

============================================================
  NEGOTIATION RESULT
============================================================
  Status  : FINALIZED
  Rounds  : 3
  Contract: CTR-20260528-895B
  Value   : 377,136.00 EUR
  Verdict : APPROVED
============================================================

  Offer history (2 offers):
    [SELLER] Round  1 |   647.28 EUR/metric_ton | Total   349,531.20 EUR
    [BUYER ] Round  2 |   698.40 EUR/metric_ton | Total   377,136.00 EUR
```

---

## Personalización

### Cambiar las empresas o los materiales

Editar los ficheros en `data/`:

- `buyer_inventory.json` — añadir materiales con su stock, consumo mensual y precio de referencia
- `seller_capacity.json` — añadir materiales con costes de producción y descuentos por volumen
- `regulations.json` — ajustar aranceles, límites de CO₂ y plazos de pago

### Ajustar la estrategia de negociación

Los parámetros clave están en los prompts de cada agente (`src/agents/`):

- Margen mínimo del vendedor: `src/agents/seller.py` → `_SYSTEM` (actualmente 20%)
- Umbral de aceptación del comprador: `src/tools/buyer_tools.py` → `evaluate_seller_offer` (actualmente score ≥ 72)
- Máximo de rondas: variable `MAX_ROUNDS` en `.env`

### Conectar a datos reales

Las funciones de carga de datos están aisladas en los tools. Para conectar un ERP real, basta con modificar las funciones `_inventory()` en `src/tools/buyer_tools.py` y `_capacity()` en `src/tools/seller_tools.py` para que llamen a la API correspondiente en lugar de leer el JSON.

---

## Requisitos

- Python 3.11+
- Docker Desktop (para ejecución en contenedor)
- [Ollama](https://ollama.ai) con modelo `llama3.2` (para el proveedor por defecto)
- O una clave de API de OpenAI, Anthropic, Groq o Google

---

## Autor

**luisforni** · [forni.luis@gmail.com](mailto:forni.luis@gmail.com)
