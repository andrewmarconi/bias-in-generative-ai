<!--
SYNC IMPACT REPORT: Constitution v1.0.0
========================================
Version Change: [TEMPLATE] → 1.0.0 (Initial ratification)
Rationale: MINOR bump - First formal constitution for the project

Modified Principles: N/A (initial creation)
Added Sections:
  - I. Reproducibility First (NON-NEGOTIABLE)
  - II. Statistical Rigor (NON-NEGOTIABLE)
  - III. Modular Architecture
  - IV. Comprehensive Documentation
  - V. Experiment Tracking & Versioning
  - VI. Ethical Responsibility
  - Quality Standards
  - Development Workflow

Removed Sections: N/A (template conversion)

Templates Requiring Updates:
  ✅ plan-template.md - Constitution Check section aligns with new principles
  ✅ spec-template.md - Scope/requirements compatible with research focus
  ✅ tasks-template.md - Task categories support reproducibility and testing requirements

Follow-up TODOs: None - all placeholders resolved

Date: 2025-11-15
-->

# Bias Detection Framework Constitution

## Core Principles

### I. Reproducibility First (NON-NEGOTIABLE)

Every experiment MUST be fully reproducible. This is the foundation of scientific validity.

**Requirements**:
- All generation parameters MUST be tracked: model version, seed values, prompts, timestamps, hardware specs
- Configuration files MUST be version controlled (YAML with git tracking)
- Random seeds MUST be configurable (fixed or random with documented strategy)
- MLflow MUST track all experiments with complete metadata
- Data versioning MUST capture: generated images, analysis results, statistical outputs
- Environment specifications MUST be documented (Python version, dependencies via `pyproject.toml`)

**Rationale**: Bias detection research requires peer review and replication. Without reproducibility, findings cannot be validated or built upon by the scientific community.

**Validation**: Every experiment run MUST produce artifacts that allow another researcher to reproduce identical results given the same configuration.

---

### II. Statistical Rigor (NON-NEGOTIABLE)

All statistical claims MUST be backed by appropriate hypothesis testing and effect size measures.

**Requirements**:
- Hypothesis tests MUST include: test statistic, p-value, effect size (e.g., Cramer's V), confidence intervals
- Sample sizes MUST be justified via power analysis (minimum 50-100 images per prompt as per research standards)
- Multiple testing corrections MUST be applied when testing multiple hypotheses
- Assumptions MUST be validated before applying tests (e.g., expected frequencies for chi-square)
- Null results MUST be reported alongside significant findings (publication bias mitigation)
- Statistical code MUST be unit tested for correctness (test calculations against known examples)

**Rationale**: Bias detection involves making claims about AI systems that may influence policy and development practices. Statistical errors undermine credibility and can lead to incorrect conclusions.

**Validation**: Every statistical result MUST be verifiable through independent implementation or peer review of test code.

---

### III. Modular Architecture

Features MUST be developed as independent, composable modules with clear interfaces.

**Requirements**:
- Separation of concerns: Image generation, VQA analysis, statistical tests, MLflow tracking are distinct modules
- Each module MUST have a clear single responsibility
- Interfaces MUST be defined via Python protocols or abstract base classes (e.g., `ProgressCallback`)
- Modules MUST be usable independently (e.g., `ImageGenerator` works without `VQAAnalyzer`)
- Configuration-driven: Modules accept config dictionaries, not hardcoded parameters
- Extension points MUST be documented (e.g., how to add new VQA models, prompts, bias categories)

**Rationale**: Research evolves - new models emerge, new statistical methods are developed. Modularity enables extending the framework without breaking existing functionality.

**Validation**: Each module MUST be testable in isolation and demonstrate clear value independently.

---

### IV. Comprehensive Documentation

Code, experiments, and results MUST be documented for human understanding and machine reproducibility.

**Requirements**:
- **Code Documentation**: Docstrings required for all public classes and functions (Google style)
- **Experiment Documentation**: MLflow logs configuration, parameters, metrics, and sample artifacts
- **Methodology Documentation**: `docs/spec.md` MUST capture the 10-phase research framework
- **User Documentation**: README, quickstart guides, usage examples for common workflows
- **Inline Comments**: Complex statistical calculations, VQA prompts, and edge case handling MUST be explained
- **Versioning Documentation**: Changes to prompts, models, or statistical methods MUST be recorded with rationale

**Rationale**: Bias research requires transparency. Stakeholders (researchers, policymakers, AI developers) need to understand methodology to trust findings.

**Validation**: A new team member MUST be able to understand and run experiments using only the documentation.

---

### V. Experiment Tracking & Versioning

All experiments MUST be tracked with complete provenance for audit and comparison.

**Requirements**:
- **MLflow Integration**: Mandatory for all experiment runs (not optional)
- **Tracked Artifacts**: Configuration snapshots, sample images (max 10 per prompt), analysis results, statistical summaries
- **Tracked Metrics**: Generation time, VQA processing time, statistical test results, effect sizes
- **Tracked Parameters**: Model names, seed strategies, prompt categories, sample sizes
- **Experiment Naming**: Human-readable names with timestamps (format: `exp_YYYYMMDD_HHMMSS`)
- **Comparison Support**: MLflow UI MUST enable comparing experiments side-by-side

**Rationale**: Bias detection involves iterative refinement. Tracking enables identifying which experimental changes improved results and which degraded validity.

**Validation**: Every experiment MUST appear in MLflow with sufficient metadata to understand what was tested and why.

---

### VI. Ethical Responsibility

Bias detection is ethically sensitive work. Development MUST reflect awareness of potential harms.

**Requirements**:
- **Transparency**: Limitations and potential misuse MUST be documented (see README disclaimer)
- **Human Validation**: VQA outputs SHOULD be validated against human annotations for at least 10-15% of images
- **Bias in Tools**: VQA models themselves contain biases - this MUST be acknowledged in analysis
- **Responsible Disclosure**: Findings about specific models SHOULD be shared with model developers before public release
- **Demographic Categories**: Selection of race, gender, age categories MUST be justified and culturally aware
- **Privacy**: Generated images SHOULD NOT include recognizable individuals (synthetic data only)

**Rationale**: Bias research can perpetuate harm if conducted carelessly. Ethical guardrails ensure the framework serves its intended purpose: improving AI fairness.

**Validation**: Every experiment plan MUST include consideration of ethical implications and mitigation strategies.

---

## Quality Standards

### Testing Requirements

- **Unit Tests**: Required for all statistical calculations, VQA parsing, config validation
- **Integration Tests**: Required for end-to-end experiment flows (generation → analysis → statistics)
- **Contract Tests**: Required when adding new VQA models or progress callbacks (see `contracts/`)
- **Statistical Validation**: Test statistical functions against known datasets with expected outcomes
- **Coverage Target**: Aim for 80%+ coverage on core logic (generation, analysis, statistics modules)

**Test-First When Possible**: For new statistical methods or VQA integrations, write tests before implementation to clarify expected behavior.

### Code Quality

- **Type Hints**: Required for all function signatures (Python 3.12+ syntax)
- **Linting**: Code MUST pass `ruff` or `pylint` checks before commit
- **Formatting**: Use `black` or equivalent (consistency over style preferences)
- **Error Handling**: Graceful degradation for non-critical failures (e.g., MLflow tracking fails → log warning, continue experiment)
- **Performance**: VQA analysis and generation MAY be slow (GPU-bound), but statistical analysis MUST be <1s for 1000 samples

### Configuration Validation

- **Schema Validation**: `experiment_config.yaml` MUST validate against expected structure before experiment starts
- **Required Sections**: generation, prompts, vqa_analysis, statistics (validated in `config.py`)
- **Type Checking**: Numeric parameters validated (e.g., `num_images_per_prompt > 0`)
- **Model Names**: Enum validation for known models (dev, schnell, krea_dev)

---

## Development Workflow

### Feature Development

1. **Specification**: Document feature requirements in `specs/###-feature-name/spec.md`
2. **Planning**: Generate implementation plan with architecture decisions (`plan.md`, `research.md`)
3. **Design**: Define data models and contracts (`data-model.md`, `contracts/`)
4. **Implementation**: Build feature following modular architecture principles
5. **Testing**: Write unit, integration, and contract tests
6. **Documentation**: Update README, usage guides, and code docstrings
7. **Validation**: Run experiment with new feature, verify MLflow tracking works

### Experiment Workflow

1. **Configure**: Edit `config/experiment_config.yaml` with experiment parameters
2. **Validate**: Run config validation (built into `BiasDetectionExperiment.setup()`)
3. **Execute**: Run experiment via `python run_experiment.py` or TUI
4. **Monitor**: Track progress via MLflow UI or TUI real-time monitoring
5. **Analyze**: Review statistical results in `data/results/statistical_summary.json`
6. **Document**: Record findings, limitations, and next steps

### Code Review Standards

- **Reproducibility Check**: Can reviewer run the code and reproduce results?
- **Statistical Validity**: Are hypothesis tests appropriate for the data and question?
- **Documentation**: Are complex decisions explained in comments or docs?
- **Test Coverage**: Are new statistical methods or VQA integrations tested?
- **Ethical Awareness**: Have potential biases or harms been considered?

---

## Governance

### Constitution Authority

This constitution supersedes ad-hoc practices. When practices conflict with constitutional principles, the constitution takes precedence. If a principle proves impractical, amend the constitution rather than violating it.

### Amendment Process

1. **Proposal**: Document proposed change with rationale (why current principle is insufficient)
2. **Discussion**: Review with team/stakeholders - what are implications?
3. **Version Bump**: Follow semantic versioning (MAJOR for breaking changes, MINOR for additions, PATCH for clarifications)
4. **Update**: Revise `.specify/memory/constitution.md` with new version number
5. **Propagation**: Update dependent templates, documentation, and guidance files
6. **Migration**: If breaking change, provide migration guide for existing experiments

### Compliance Verification

- **Pull Requests**: Reviewers MUST verify constitutional compliance
- **Experiment Audits**: Periodic review of MLflow experiments for reproducibility and documentation completeness
- **Complexity Justification**: Any deviation from principles (e.g., tight coupling for performance) MUST be documented with rationale

### Runtime Guidance

For day-to-day development decisions not covered by the constitution, refer to:
- [CLAUDE.md](../../CLAUDE.md) - AI assistant context and development patterns
- [docs/spec.md](../../docs/spec.md) - Research methodology and framework
- [docs/tech.md](../../docs/tech.md) - Technical implementation details

---

**Version**: 1.0.0 | **Ratified**: 2025-11-15 | **Last Amended**: 2025-11-15
