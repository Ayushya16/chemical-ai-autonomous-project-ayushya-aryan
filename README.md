# Autonomous Process Simulation Copilot & Headless DWSIM Proof of Concept
**Department of Chemical Engineering | BITS Pilani, Pilani Campus**

* **Course Code:** CHE F376 / CHE F377 Design Oriented Project (3 Units)
* **Faculty Supervisor:** Prof. Shashank Venkat Muddu
* **Student Investigators:** Ayushya Ramesh Ojha (ID: 20241228) and Aryan Jain
* **Live Interactive Web Demo:** https://ayushya16.github.io/dwsim-flash-separator-copilot/

## Included Deliverables
1. **Interactive Web Demonstration & Explainer:** Live at https://ayushya16.github.io/dwsim-flash-separator-copilot/ with three tabs: Interactive Flash Simulator, How to Use & Operating Guide, and Technical Explainer & Thermodynamic Mechanics.
2. **Headless Python Script:** 
un_dwsim_flash_separator.py (orchestrates DWSIM via Automation3 .NET API headlessly).
3. **Standalone Verification Solver:** standalone_flash_verification.py (pure Python multicomponent VLE solver executing bounded Newton-Raphson Rachford-Rice iterations).
4. **Automated Test Suite:** 	est_flash_separator.py (5/5 unit tests verifying mass/energy balances to 10^-12 precision).
5. **DOP 1-Page Proposal PDF:** DOP_ONE_PAGER_PROPOSAL.pdf (MECE work breakdown, target objectives, and semester timeline).
6. **Technical 1-Page Note PDF:** TECHNICAL_PROOF_OF_CONCEPT_ONE_PAGER.pdf (architecture, governing equations, and convergence metrics).
