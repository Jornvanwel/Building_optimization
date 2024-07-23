# Building_optimization

This projects aims to minimize the cost while ensuring that every worker is able to work at the office.

The optimization function is as follows

Certainly! Below is the markdown representation of the mathematical equations based on the given Python code for the building closure optimization problem:

### Decision Variables

$\( x_{ij} \)$: Binary variable indicating if building $\(i\)$ is open in period $\(j\)$.
$\( y_{ijk} \)$: Binary variable indicating if workers are moved from building $\(i\)$ to building $\(k\)$ in period $\(j\)$.
$\( z_{ijk} \)$: Binary variable indicating if workers are moving from building $\(i\)$ to building $\(k\)$ in period $\(j\)$.

### Objective Function

Minimize the total cost:

$\quad & \sum_{i \in } \sum_{j=1}^{-1} \_i \cdot x_{i,j} + \sum_{i \in } \sum_{j=1}^{-1} \sum_{k \in _i}  \cdot _{k,} \cdot z_{i,j,k}$

### Constraints

#### Constraint 1: Contract Due

$$
$$
\begin{cases}
x_{ij} = 1 & \text{if } \text{Contractdue}_i > (\text{periods} - 1), \quad \forall i, \forall j \\
x_{ij} = 1 & \text{if } j \leq \text{Contractdue}_i, \quad \forall i, \forall j
\end{cases}
$$
$$

#### Constraint 2: Maximum Occupation

$$
$$
\text{Occupation}_i \cdot x_{ij} + \sum_{k \in \text{Neighbors}_i} \left( \text{Occupation}_k \cdot y_{kji} \right) \leq \text{Desks}_i, \quad \forall i, \forall j
$$
$$

#### Constraint 3: One Move per Period

$$
$$
\sum_{k \in \text{Neighbors}_i} y_{ijk} \leq 1, \quad \forall i, \forall j
$$
$$

#### Constraint 4: Open Building for Movement

$$
\sum_{k \in \text{Neighbors}_i} y_{ijk} \leq 1, \quad \forall i, \forall j
$$
$$
\sum_{k \in \text{Neighbors}_i} y_{ijk} \leq 1, \quad \forall i, \forall j
$$

#### Constraint 5: Building Usage or Movement

$$
x_{ij} \geq y_{kji}, \quad \forall i, \forall j, \forall k \in \text{Neighbors}_i
$$
$$
x_{ij} \geq y_{kji}, \quad \forall i, \forall j, \forall k \in \text{Neighbors}_i
$$

#### Constraint 6: Building Closure Order

$$
$$
x_{ij} \geq x_{i(j+1)}, \quad \forall i, \forall j < (\text{periods} - 1)
$$
$$

#### Constraint 7: Movement Indicator

$$
$$
\begin{cases}
z_{ijk} = y_{ijk} & \text{if } j = 1, \quad \forall i, \forall j, \forall k \in \text{Neighbors}_i \\
z_{ijk} \geq y_{ijk} - y_{i(j-1)k} & \text{if } j > 1, \quad \forall i, \forall j, \forall k \in \text{Neighbors}_i \\
z_{ijk} \leq y_{ijk} & \text{if } j > 1, \quad \forall i, \forall j, \forall k \in \text{Neighbors}_i \\
z_{ijk} \leq 1 - y_{i(j-1)k} & \text{if } j > 1, \quad \forall i, \forall j, \forall k \in \text{Neighbors}_i
\end{cases}
$$
$$