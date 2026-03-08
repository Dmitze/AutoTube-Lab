# AI/ML Engineer Agent Prompt

## Overview
This document outlines the implementation plan for various Machine Learning (ML) modules that will form a comprehensive AI/ML agent focusing on content generation and trend analysis.

## Modules and Implementation Plan

### 1. Trend Analyzer (`trend_analyzer.py`)
- **Purpose:** Analyze trends over time and generate statistics.
- **Dependencies:**
  - `numpy`
  - `pandas`
  - `matplotlib`
  - `scikit-learn`
- **Directory Layout:**
  - `trend_analyzer/
    - __init__.py
    - trend_analyzer.py`
- **O-Notation Requirements:** O(n log n) for sorting trends.
- **Testing/Metrics Thresholds:**
  - Accuracy: 90%

### 2. Content Generator (`content_generator.py`)
- **Purpose:** Generate content based on trends identified.
- **Dependencies:**
  - `transformers`
  - `torch`
  - `flask`
- **Directory Layout:**
  - `content_generator/
    - __init__.py
    - content_generator.py`
- **O-Notation Requirements:** O(n) for text generation.
- **Testing/Metrics Thresholds:**
  - Content Quality Score: 85%

### 3. Learner (`learner.py`)
- **Purpose:** Learn from user interactions and improve future content.
- **Dependencies:**
  - `tensorflow`
  - `numpy`
- **Directory Layout:**
  - `learner/
    - __init__.py
    - learner.py`
- **O-Notation Requirements:** O(n^2) for training loop.
- **Testing/Metrics Thresholds:**
  - Model Performance: 80%

### 4. Topic Modeling (`topic_modeling.py`)
- **Purpose:** Extract topics from user inputs using LDA or EM.
- **Dependencies:**
  - `gensim`
  - `scikit-learn`
- **Directory Layout:**
  - `topic_modeling/
    - __init__.py
    - topic_modeling.py`
- **O-Notation Requirements:** O(n^2) for LDA model fitting.
- **Testing/Metrics Thresholds:**
  - Coherence Score: 0.5

## Placeholder Sections
### Niche Configuration
- *Configurable parameters specific to niche applications will be detailed here.*

### YouTube Metrics Schema
- *Specifications for desired YouTube metrics will be outlined here.*

## Run Instructions
1. Clone the repository.
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute each module as follows:
   ```bash
   python trend_analyzer/trend_analyzer.py
   python content_generator/content_generator.py
   python learner/learner.py
   python topic_modeling/topic_modeling.py
   ```
4. Monitor output and ensure metrics are within specified thresholds.