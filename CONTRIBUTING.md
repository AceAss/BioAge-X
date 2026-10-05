# Contributing to BioAge-X

Thank you for your interest in contributing to BioAge-X! We welcome contributions from computational biologists, bioinformatics researchers, ML engineers, and software architects.

## Development Workflow

1. Fork and clone the repository.
2. Setup the Python environment:
   ```bash
   pip install -r requirements.txt
   ```
3. Setup the frontend:
   ```bash
   cd apps/frontend
   npm install
   ```
4. Run tests before submitting a Pull Request:
   ```bash
   python -m pytest tests/
   cd apps/frontend && npm run build
   ```
5. Follow PEP 8 style standards and provide type annotations.
6. Remember: BioAge-X is a research and educational platform, NOT a clinical diagnostic tool. Never add claims of individual clinical prognostic utility.
