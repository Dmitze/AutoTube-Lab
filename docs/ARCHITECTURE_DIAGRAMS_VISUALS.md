# Візуали

В цьому документі представлено інформацію про візуали, які використовуються в проекті.

## Діаграма класів PlantUML для агентів
```plantuml
@startuml
class TrendAgent
class ContentAgent
class SEOAgent
class ComplianceGate
class UploadAgent
class AnalyticsAgent
class LearnerAgent
class Storage
class BudgetGuard
class Orchestrator

TrendAgent --> ContentAgent
ContentAgent --> SEOAgent
SEOAgent --> ComplianceGate

@enduml
```

## Діаграма потоку PlantUML для циклу бота
```plantuml
@startuml
start
:Budget Guard;
:Compliance Gate;
:Unlisted First;
:Human Review First 50;
stop
@enduml
```

## Код для візуалізації графіка трендів з NetworkX + matplotlib
```python
import matplotlib.pyplot as plt
import networkx as nx

G = nx.Graph()
G.add_edges_from([(1, 2), (1, 3), (2, 4)])

pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True)
plt.show()
```

## Кроки у draw.io та альтернативна кодова реалізація
1. Імплементуйте блоки в draw.io.
2. Використовуйте відповідні шablони з draw.io.

## Ризики та рішення
- Ризик: Неправильна реалізація логіки.
- Виправлення: Ретельне тестування та перевірка.

## Фрагменти PlantUML
```plantuml
@startuml
component Component1
component Component2

Component1 -> Component2: Request
@enduml
```

```plantuml
@startuml
actor User
User -> (Function1)
@enduml
```

## Перевірочний список візуалізації тестів
- [ ] Чи відповідає візуал даним?
- [ ] Чи відповідають тести проекту?

## Таблиця покриття
| Функція          | Покриття |
|------------------|----------|
| Function1        | 80%      |
| Function2        | 75%      |