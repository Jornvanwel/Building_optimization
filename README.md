# Building_optimization

This projects aims to minimize the cost while ensuring that every worker is able to work at the office. This project helps a business with multiple buildings to make the most cost effective transition to the new hybrid working environment where people are less often in the office and therefore buildings are less occupied.

## Table of Contents
- [Introduction](#Introduction)
- [Installation](#installation)
- [Usage](#usage)

## Introduction

### Decision Variables

$\( x_{ij} \)$: Binary variable indicating if building $\(i\)$ is open in period $\(j\)$.
$\( y_{ijk} \)$: Binary variable indicating if workers are moved from building $\(i\)$ to building $\(k\)$ in period $\(j\)$.
$\( z_{ijk} \)$: Binary variable indicating if workers are moving from building $\(i\)$ to building $\(k\)$ in period $\(j\)$.

### Objective Function:

The objective is to minimize the total cost, which includes the monthly rent of each building that is open and the cost associated with moving workers between buildings.

### Contraints

**Contractual Obligations**: Ensures that a building remains open for the duration of its contractual obligation.

**Capacity Limitation**: Ensures that the total number of workers at any building does not exceed its capacity. This includes workers originally assigned to the building and those moved from neighboring buildings.

**Unique Movement**: Ensures that workers can only moved once.

**Movement Dependency**: Ensures that workers can only move to a building that is open.

**Exclusive Occupancy**: Ensures that when a building is closed, the workers have been moved to another building and only one.

**Continuity of Operation**: Ensures that if a building is closed in a period, it remains closed in the subsequent period, reflecting a form of operational continuity.

**Movement Activation**: Handles the logic for the z variable, ensuring it correctly reflects the transition of workers from one pand to another, specifically flagging the initiation of a move.


## Installation
Steps to install the project locally:
1. Clone the repo
   ```bash
   git clone https://github.com/Jornvanwel/Building_optimization.git

## Usage
To use the model put in the configurations inside the config.yaml. Follow the file structure of the input file in the example1.csv. 
Then run
    ```bash
    python main_script.py