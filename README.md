# MISTeRiOSSE
## Modelling Interconnected Social and Technical Risks in Open Source Software Ecosystems

This repo contains code to reproduce results of the paper "Modelling Interconnected Social and Technical Risks in Open Source Software Ecosystems" by William Schueller and Johannes Wachs.


### Init params

This part of the script defines parameters and credentials used in all other scripts.
You will need an instance of the database either in PostgreSQL (recommended), or in SQLite.

### Script 1: Devs

This script lists developers by importance and generates the graph of developer impact.


### Script 2: Ranks

This script computes the different rankings to be used in the interventions.

### Script 3: Policy effects

This script computes the impact of interventions for each ranking.

### Script 4: Time

This script computes the same as Script 1 but across time (one figure per timestamp).

### Script 5: Time global

This script computes the value of the global measure over time (one point per timestamp).
